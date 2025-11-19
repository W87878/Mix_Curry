"""
完整的政府 API 流程
符合真實的災害補助領取流程
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.database import DatabaseService
from app.services.gov_wallet import get_gov_wallet_service

router = APIRouter(prefix="/api/v1/complete-flow", tags=["完整流程"])

# 初始化服務
db_service = DatabaseService()

# ==========================================
# Helper Functions
# ==========================================

async def record_credential_history(
    application_id: str,
    user_id: str,
    action_type: str,  # 'credential_issued' or 'credential_verified'
    status: str,  # 'issued' or 'verified'
    transaction_id: Optional[str] = None,
    issuer_organization: Optional[str] = None,
    verifier_organization: Optional[str] = None,
    verification_location: Optional[Dict[str, Any]] = None,
    certificate_id: Optional[str] = None,
    notes: Optional[str] = None
):
    """
    記錄憑證使用歷史
    
    Args:
        application_id: 申請案件 ID
        user_id: 使用者 ID
        action_type: 動作類型 (credential_issued/credential_verified)
        status: 狀態 (issued/verified)
        transaction_id: 政府 API transaction ID
        issuer_organization: 發行機構（領取時記錄）
        verifier_organization: 驗證機構（驗證時記錄，如：7-11 中正門市）
        verification_location: 驗證地點詳細資訊
        certificate_id: 憑證 ID
        notes: 備註
    """
    try:
        # 取得申請資料
        app_result = db_service.client.table("applications")\
            .select("applicant_name, id_number, disaster_type, address, approved_amount")\
            .eq("id", application_id)\
            .execute()
        
        if not app_result.data:
            print(f"⚠️ 找不到申請記錄，無法記錄 history: {application_id}")
            return
        
        app_data = app_result.data[0]
        
        # 插入 history 記錄
        history_data = {
            "application_id": application_id,
            "user_id": user_id,
            "action_type": action_type,
            "action_time": datetime.now().isoformat(),
            "applicant_name": app_data.get("applicant_name"),
            "id_number": app_data.get("id_number"),
            "disaster_type": app_data.get("disaster_type"),
            "disaster_address": app_data.get("address"),
            "approved_amount": app_data.get("approved_amount"),
            "status": status,
            "transaction_id": transaction_id,
            "issuer_organization": issuer_organization,
            "verifier_organization": verifier_organization,
            "verification_location": verification_location,
            "certificate_id": certificate_id,
            "notes": notes
        }
        
        result = db_service.client.table("credential_history")\
            .insert(history_data)\
            .execute()
        
        print(f"✅ 憑證歷史記錄已儲存:")
        print(f"   動作類型: {action_type}")
        print(f"   狀態: {status}")
        print(f"   申請人: {app_data.get('applicant_name')}")
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"❌ 記錄憑證歷史失敗: {e}")
        # 不拋出異常，避免影響主流程
        return None


# ==========================================
# 請求/回應模型
# ==========================================

class ReviewApplicationRequest(BaseModel):
    """里長審核申請"""
    application_id: str
    approved: bool
    review_notes: Optional[str] = ""
    approved_amount: Optional[int] = None


class IssueCredentialResponse(BaseModel):
    """發行憑證回應"""
    success: bool
    application_id: str
    transaction_id: Optional[str] = None
    qr_code: Optional[str] = None
    deep_link: Optional[str] = None
    message: str


class GenerateVPQRCodeRequest(BaseModel):
    """產生 VP 驗證 QR Code"""
    ref: str  # VP 驗證服務代碼，例如：00000000_subsidy_667


class VerifyVPRequest(BaseModel):
    """驗證 VP"""
    transaction_id: str  # 從 generate_vp_qrcode 取得的 transactionId
    applicant_id_number: Optional[str] = None  # 申請人身分證字號

# ==========================================
# API 端點
# ==========================================

@router.post("/review-and-issue")
async def review_and_issue_credential(request: ReviewApplicationRequest):
    """
    🎯 步驟 2-3：里長審核 + 發行數位憑證
    
    流程：
    1. 里長審核通過
    2. 系統呼叫政府發行端 API (POST /api/qrcode/data)
    3. 取得 qrCode, transactionId, deepLink
    4. 通知災民（發送 QR Code）
    """
    try:
        print(f"\n{'='*60}")
        print(f"📝 開始審核申請")
        print(f"{'='*60}")
        print(f"申請ID: {request.application_id}")
        print(f"審核結果: {'✅ 核准' if request.approved else '❌ 駁回'}")
        print(f"審核備註: {request.review_notes or '無'}")
        
        # 1. 檢查申請是否存在
        try:
            print(f"\n🔍 步驟 1: 查詢申請記錄...")
            result = db_service.client.table("applications")\
                .select("*")\
                .eq("id", request.application_id)\
                .execute()
            
            if not result.data:
                print(f"❌ 找不到申請記錄: {request.application_id}")
                raise HTTPException(status_code=404, detail="找不到申請記錄")
            
            application = result.data[0]
            print(f"✅ 找到申請記錄:")
            print(f"   案件編號: {application.get('case_no', 'N/A')}")
            print(f"   申請人: {application.get('applicant_name', 'N/A')}")
            print(f"   身分證: {application.get('id_number', 'N/A')}")
            
        except HTTPException:
            raise
        except Exception as db_error:
            print(f"❌ 資料庫查詢失敗: {db_error}")
            raise HTTPException(
                status_code=500,
                detail=f"資料庫查詢失敗: {str(db_error)}"
            )
        
        # 2. 處理駁回情況
        if not request.approved:
            print(f"\n❌ 步驟 2: 駁回申請...")
            try:
                db_service.client.table("applications").update({
                    "status": "rejected",
                    "review_notes": request.review_notes,
                    "reviewed_at": datetime.now().isoformat()
                }).eq("id", request.application_id).execute()
                
                print(f"✅ 申請已駁回")
                return {
                    "success": True,
                    "message": "申請已駁回"
                }
            except Exception as update_error:
                print(f"❌ 更新駁回狀態失敗: {update_error}")
                raise HTTPException(
                    status_code=500,
                    detail=f"更新狀態失敗: {str(update_error)}"
                )
        
        # 3. 審核通過，準備發行憑證
        print(f"\n✅ 步驟 3: 核准申請，準備發行憑證...")
        
        # 根據 VC 面板要求的欄位格式化資料
        now = datetime.now()
        issuance_date = now.strftime("%Y%m%d")
        expired_date = (now.replace(year=now.year + 1)).strftime("%Y%m%d")
        
        # VC 面板要求的欄位
        fields = [
            {
                "ename": "name",
                "content": application.get("applicant_name", "")
            },
            {
                "ename": "id_number",
                "content": application.get("id_number", "")
            },
            {
                "ename": "phone_number",
                "content": application.get("phone", "")
            },
            {
                "ename": "registered_address",
                "content": application.get("address", "")
            },
            {
                "ename": "address",
                "content": application.get("damage_address", application.get("address", ""))
            }
        ]
        
        # 4. 呼叫政府發行端 API
        gov_service = get_gov_wallet_service()
        
        # 使用真實的 vcUid (從 VC 面板的 credentialType)
        vc_uid = "00000000_subsidy_666"  # 你提供的 vcUid
        
        try:
            issue_result = await gov_service.generate_qrcode_data(
                vctid=vc_uid,
                issuance_date=issuance_date,
                expired_date=expired_date,
                fields=fields
            )
        except Exception as api_error:
            print(f"❌ 呼叫政府發行端 API 失敗: {api_error}")
            raise HTTPException(
                status_code=500,
                detail=f"發行憑證失敗: {str(api_error)}"
            )
        
        print(f"🔍 issue_result 內容:")
        print(f"  - success: {issue_result.get('success')}")
        print(f"  - qr_code_data 存在: {issue_result.get('qr_code_data') is not None}")
        print(f"  - qr_code_data 長度: {len(issue_result.get('qr_code_data', ''))}")
        print(f"  - transaction_id: {issue_result.get('transaction_id')}")
        print(f"  - deep_link: {issue_result.get('deep_link')[:50] if issue_result.get('deep_link') else None}...")
        
        if not issue_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"發行憑證失敗: {issue_result.get('message')}"
            )
        
        # 5. 更新資料庫
        try:
            db_service.client.table("applications").update({
                "status": "approved",
                "review_notes": request.review_notes,
                "approved_amount": request.approved_amount,
                "reviewed_at": datetime.now().isoformat(),
                "gov_qr_code_data": issue_result.get("qr_code_data"),
                "gov_transaction_id": issue_result.get("transaction_id"),
                "gov_deep_link": issue_result.get("deep_link")
            }).eq("id", request.application_id).execute()
        except Exception as db_error:
            print(f"❌ 更新資料庫失敗: {db_error}")
            raise HTTPException(
                status_code=500,
                detail=f"更新資料庫失敗: {str(db_error)}"
            )
        
        # 6. 記錄憑證發行歷史
        print(f"\n📝 步驟 6: 記錄憑證發行歷史...")
        await record_credential_history(
            application_id=request.application_id,
            user_id=application.get("applicant_id"),
            action_type="credential_issued",
            status="issued",
            transaction_id=issue_result.get("transaction_id"),
            issuer_organization="台南市政府災害救助中心",  # 可以從設定檔或資料庫讀取
            notes=f"憑證發行成功，核准金額: NT$ {request.approved_amount:,.0f}"
        )
        
        # 7. TODO: 發送通知給災民（包含 QR Code）
        # send_notification_to_applicant(...)
        
        response = IssueCredentialResponse(
            success=True,
            application_id=request.application_id,
            transaction_id=issue_result.get("transaction_id"),
            qr_code=issue_result.get("qr_code_data"),
            deep_link=issue_result.get("deep_link"),
            message="憑證已發行！QR Code 已發送給災民"
        )
        
        print(f"🔍 返回 Response:")
        print(f"  - qr_code 存在: {response.qr_code is not None}")
        print(f"  - qr_code 長度: {len(response.qr_code) if response.qr_code else 0}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"審核並發行憑證錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-vp-qrcode")
async def generate_vp_qrcode(request: GenerateVPQRCodeRequest):
    """
    🎯 步驟 5：7-11 機台產生 VP 驗證 QR Code
    
    流程：
    1. 災民到 7-11，點擊「災害補助領取」
    2. 系統呼叫政府驗證端 API (GET /api/oidvp/qrcode)
    3. 產生 QR Code 給災民掃描
    4. 災民用 APP 掃描 QR Code
    """
    try:
        # 產生隨機 transaction_id（不超過50字元）
        transaction_id = str(uuid.uuid4())[:50]
        
        # 呼叫政府驗證端 API
        gov_service = get_gov_wallet_service()
        
        vp_result = await gov_service.generate_vp_qrcode(
            ref=request.ref,  # 例如：00000000_subsidy_667
            transaction_id=transaction_id
        )
        
        if not vp_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"產生 VP QR Code 失敗: {vp_result.get('message')}"
            )
        
        return {
            "success": True,
            "qrcode_image": vp_result.get("qrcode_image"),
            "auth_uri": vp_result.get("auth_uri"),
            "transaction_id": vp_result.get("transaction_id"),
            "message": "VP QR Code 已產生，請災民掃描"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"產生 VP QR Code 錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-vp")
async def verify_vp(request: VerifyVPRequest):
    """
    🎯 步驟 6：驗證 VP 並發放補助
    
    流程：
    1. 災民用 APP 掃描完成
    2. 系統呼叫政府驗證端 API (POST /api/oidvp/result)
    3. 取得 verifyResult (bool)
    4. 若通過，發放補助
    """
    try:
        # 呼叫政府驗證端 API
        gov_service = get_gov_wallet_service()
        
        verify_result = await gov_service.verify_vp_result(
            transaction_id=request.transaction_id
        )
        
        
        if not verify_result.get("success"):
            return {
                "success": False,
                "verified": False,
                "message": f"驗證失敗: {verify_result.get('message')}"
            }
        
        # 驗證通過
        if verify_result.get("verify_result"):
            data = verify_result.get("credential_data", {})
            credential_type = data.get("credentialType", "未知類型")
            claims = data.get("claims", [])
            
            # 1️⃣ 處理身分證憑證 (00000000_mixcurry_idcard)
            if credential_type == "00000000_mixcurry_idcard":
                # 解析憑證資料
                email = ''
                name = ''
                phone = ''
                id_number = ''
                registered_address = ''
                
                for dic in claims:
                    ename = dic.get("ename", "")
                    value = dic.get("value", "")
                    
                    if ename == "email":
                        email = value
                    elif ename == "name":
                        name = value
                    elif ename == "phone":
                        phone = value
                    elif ename == "id_number":
                        id_number = value
                    elif ename == "registered_address":
                        registered_address = value
                
                # 驗證必要欄位
                if not email:
                    return {
                        "success": False,
                        "verified": False,
                        "message": "❌ Email 遺失"
                    }
                
                # 檢查使用者是否已存在（用 email 查詢）
                try:
                    existing_user = db_service.client.table("users")\
                        .select("*")\
                        .eq("email", email)\
                        .execute()
                    if existing_user.data and len(existing_user.data) > 0:
                        user_data = existing_user.data[0]
                    else:
                        user_data = {
                            "email": email,
                            "full_name": name,
                            "phone": phone,
                            "id_number": id_number,
                            "role": "applicant",
                            "is_verified": True,
                            "twfido_verified": True,
                            # "verified_at": datetime.now().isoformat(),
                            # "registered_address": registered_address
                        }
                    
                    
                    if existing_user.data and len(existing_user.data) > 0:
                        # 更新現有使用者
                        user_id = existing_user.data[0]["id"]
                        db_service.client.table("users").update(user_data)\
                            .eq("id", user_id).execute()
                        
                        print(f"✅ 使用者已更新: {name} ({email})")
                    else:
                        # 新增使用者
                        result = db_service.client.table("users").insert(user_data).execute()
                        user_id = result.data[0]["id"] if result.data else None
                        
                        print(f"✅ 新使用者已建立: {name} ({id_number})")
                    
                    return {
                        "success": True,
                        "verified": True,
                        "user_id": user_id,
                        "email": email,
                        "name": name,
                        "id_number": id_number,  # 加入身分證字號
                        "phone": phone,
                        "message": "✅ 身分驗證成功！使用者資料已更新"
                    }
                    
                except Exception as db_error:
                    print(f"❌ 資料庫操作失敗: {db_error}")
                    return {
                        "success": False,
                        "verified": True,
                        "message": f"身分驗證成功，但資料庫更新失敗: {str(db_error)}"
                    }
            
            # 2️⃣ 處理災害補助憑證 (00000000_subsidy_667)
            elif credential_type == "00000000_subsidy_667":
                # 解析憑證資料
                name = ''
                email = ''
                phone = ''
                registered_address = ''
                
                for dic in claims:
                    ename = dic.get("ename", "")
                    value = dic.get("value", "")
                    
                    if ename == "name":
                        name = value
                    elif ename == "id_number":
                        id_number = value
                    elif ename == "phone":
                        phone = value
                    elif ename == "registered_address":
                        registered_address = value
                    elif ename == "email":
                        email = value
                
                # 驗證必要欄位
                if not id_number:
                    return {
                        "success": False,
                        "verified": False,
                        "message": "❌ 身分證號碼遺失"
                    }
                
                # 根據身分證號碼查詢申請案件
                try:
                    # 查詢該身分證的申請案件（取最新一筆已核准的）
                    applications = db_service.client.table("applications")\
                        .select("*")\
                        .eq("email", email)\
                        .eq("status", "approved")\
                        .order("approved_at", desc=True)\
                        .limit(1)\
                        .execute()
                    
                    if not applications.data or len(applications.data) == 0:
                        return {
                            "success": False,
                            "verified": True,
                            "message": f"❌ 找不到核准的申請案件 (Email: {email})"
                        }
                    
                    application = applications.data[0]
                    application_id = application["id"]
                    case_no = application["case_no"]
                    
                    # 驗證憑證資料與申請資料是否相符
                    if application.get("applicant_name") != name:
                        print(f"⚠️  姓名不符: 憑證={name}, 申請={application.get('applicant_name')}")
                    
                    # 更新申請案件狀態為「已發放」
                    db_service.client.table("applications").update({
                        "status": "disbursed",
                        "disbursed_at": datetime.now().isoformat(),
                        "vp_transaction_id": request.transaction_id
                    }).eq("id", application_id).execute()
                    
                    print(f"✅ 補助已發放: {case_no} ({name})")
                    
                    # 記錄憑證驗證歷史（711 機台驗證）
                    await record_credential_history(
                        application_id=application_id,
                        user_id=application.get("applicant_id"),
                        action_type="credential_verified",
                        status="verified",
                        transaction_id=request.transaction_id,
                        verifier_organization="7-11 便利商店",  # 可以從請求參數中傳入具體門市
                        verification_location={
                            "type": "711_store",
                            "verified_at": datetime.now().isoformat()
                        },
                        notes=f"在 7-11 機台驗證成功，補助已發放。案件編號: {case_no}"
                    )
                    
                    # TODO: 發送補助發放通知郵件
                    # from app.services.edm.send_disaster_notification import DisasterNotificationService
                    # notification_service = DisasterNotificationService()
                    # notification_service.send_disbursement_notification(...)
                    
                    return {
                        "success": True,
                        "verified": True,
                        "application_id": application_id,
                        "case_no": case_no,
                        "applicant_name": name,
                        "id_number": id_number,
                        "message": f"✅ 驗證成功！補助已發放 (案件編號: {case_no})"
                    }
                    
                except Exception as db_error:
                    print(f"❌ 資料庫操作失敗: {db_error}")
                    return {
                        "success": False,
                        "verified": True,
                        "message": f"憑證驗證成功，但補助發放失敗: {str(db_error)}"
                    }
            
            elif credential_type == "00000000_20251110":
                # 解析房屋持有憑證 (20251112)
                property_owner_name = ''
                property_owner_id_number = ''
                property_address = ''
                
                for dic in claims:
                    ename = dic.get("ename", "")
                    value = dic.get("value", "")
                    
                    if ename == "name":
                        property_owner_name = value
                    elif ename == "id_number":
                        property_owner_id_number = value
                    elif ename == "address":
                        property_address = value
                
                # 驗證必要欄位
                if not property_owner_id_number:
                    return {
                        "success": False,
                        "verified": False,
                        "id_match": False,
                        "message": "❌ 房屋持有人身分證號碼遺失"
                    }
                
                # 🔍 比對身分證字號
                if property_owner_id_number != request.applicant_id_number:
                    return {
                        "success": False,
                        "verified": True,
                        "id_match": False,
                        "property_owner_name": property_owner_name,
                        "property_owner_id_number": property_owner_id_number,
                        "applicant_id_number": request.applicant_id_number,
                        "message": "❌ 房屋持有人與申請人不符！\n\n房屋持有人須與申請人為同一人。\n請確認您的憑證是否正確。"
                    }
                
                # 檢查使用者是否已存在（用 email 查詢）
                existing_user = db_service.client.table("users")\
                    .select("*")\
                    .eq("id_number", property_owner_id_number)\
                    .execute()
                if existing_user.data and len(existing_user.data) > 0:
                    user_data = existing_user.data[0]
                else:
                    user_data = {
                        "full_name": property_owner_name,
                        "id_number": property_owner_id_number,
                        "address": property_address,
                        "role": "applicant",
                        "is_verified": True,
                        "twfido_verified": True,
                        # "verified_at": datetime.now().isoformat(),
                        # "registered_address": registered_address
                    }
                
                
                if existing_user.data and len(existing_user.data) > 0:
                    # 更新現有使用者
                    user_id = existing_user.data[0]["id"]
                    db_service.client.table("users").update(user_data)\
                        .eq("id", user_id).execute()

                    print(f"✅ 使用者已更新: {property_owner_name} ({property_owner_id_number})")

                # ✅ 身分證相符
                return {
                    "success": True,
                    "verified": True,
                    "id_match": True,
                    "property_owner_name": property_owner_name,
                    "property_owner_id_number": property_owner_id_number,
                    "property_address": property_address,
                    "message": "✅ 房屋持有驗證成功！"
                }

            # 3️⃣ 未知憑證類型
            else:
                return {
                    "success": False,
                    "verified": False,
                    "message": f"❌ 不支援的憑證類型: {credential_type}"
                }
        else:
            return {
                "success": True,
                "verified": False,
                "message": "❌ 憑證驗證失敗"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"驗證 VP 錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/credential-history/{application_id}")
async def get_credential_history(application_id: str):
    """
    📋 查詢憑證使用歷史記錄
    
    Args:
        application_id: 申請案件 ID
        
    Returns:
        該申請案件的所有憑證使用歷史記錄
    """
    try:
        result = db_service.client.table("credential_history")\
            .select("*")\
            .eq("application_id", application_id)\
            .order("action_time", desc=True)\
            .execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data)
        }
        
    except Exception as e:
        print(f"查詢憑證歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credential-history-by-user/{user_id}")
async def get_credential_history_by_user(user_id: str):
    """
    📋 查詢使用者的所有憑證使用歷史記錄
    
    Args:
        user_id: 使用者 ID
        
    Returns:
        該使用者的所有憑證使用歷史記錄
    """
    try:
        result = db_service.client.table("credential_history")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("action_time", desc=True)\
            .execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data)
        }
        
    except Exception as e:
        print(f"查詢憑證歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credential-history-stats")
async def get_credential_history_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    disaster_type: Optional[str] = None
):
    """
    📊 查詢憑證使用統計數據
    
    Args:
        start_date: 開始日期 (YYYY-MM-DD)
        end_date: 結束日期 (YYYY-MM-DD)
        disaster_type: 災害類型篩選
        
    Returns:
        統計數據（發行數量、驗證數量等）
    """
    try:
        query = db_service.client.table("credential_history").select("*")
        
        if start_date:
            query = query.gte("action_time", start_date)
        if end_date:
            query = query.lte("action_time", end_date)
        if disaster_type:
            query = query.eq("disaster_type", disaster_type)
        
        result = query.execute()
        
        # 統計數據
        issued_count = len([r for r in result.data if r.get("status") == "issued"])
        verified_count = len([r for r in result.data if r.get("status") == "verified"])
        
        # 按災害類型統計
        disaster_stats = {}
        for record in result.data:
            dt = record.get("disaster_type", "unknown")
            if dt not in disaster_stats:
                disaster_stats[dt] = {"issued": 0, "verified": 0}
            
            if record.get("status") == "issued":
                disaster_stats[dt]["issued"] += 1
            elif record.get("status") == "verified":
                disaster_stats[dt]["verified"] += 1
        
        # 按機構統計
        issuer_stats = {}
        verifier_stats = {}
        
        for record in result.data:
            if record.get("issuer_organization"):
                org = record.get("issuer_organization")
                issuer_stats[org] = issuer_stats.get(org, 0) + 1
            
            if record.get("verifier_organization"):
                org = record.get("verifier_organization")
                verifier_stats[org] = verifier_stats.get(org, 0) + 1
        
        return {
            "success": True,
            "stats": {
                "total_records": len(result.data),
                "issued_count": issued_count,
                "verified_count": verified_count,
                "disaster_stats": disaster_stats,
                "issuer_stats": issuer_stats,
                "verifier_stats": verifier_stats
            },
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
        
    except Exception as e:
        print(f"查詢統計數據失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check-credential-claim/{transaction_id}")
async def check_credential_claim(transaction_id: str):
    """
    🔍 檢查用戶是否已掃描並存入 VC 卡片
    
    對應政府 API: GET /api/credential/nonce/{transactionId}
    
    流程：
    1. 前端定期輪詢此 API（每 2 秒一次）
    2. 呼叫政府驗證端 GET /api/credential/nonce/{transactionId}
    3. 檢查回應中的 credential 欄位
    4. 如果有 credential (JWT Token)，表示用戶已掃描並存入
    
    Returns:
        - credential 存在 → 用戶已領取憑證
        - credential 不存在 → 用戶尚未掃描或尚未存入
    """
    try:
        gov_service = get_gov_wallet_service()
        
        # 呼叫政府驗證端 API
        result = await gov_service.check_credential_nonce(transaction_id)
        
        print(f"🔍 檢查憑證領取狀態: transaction_id={transaction_id}")
        print(f"   結果: {result}")
        
        return result
        
    except Exception as e:
        print(f"檢查憑證領取狀態錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/record-credential-claimed")
async def record_credential_claimed_endpoint(
    application_id: str,
    transaction_id: str
):
    """
    📝 記錄憑證領取（當用戶掃描 QR Code 並儲存憑證到手機時調用）
    
    此 API 由前端在檢測到憑證領取成功後調用
    """
    try:
        # 取得申請資料
        app_result = db_service.client.table("applications")\
            .select("*, applicant_id")\
            .eq("id", application_id)\
            .execute()
        
        if not app_result.data:
            raise HTTPException(status_code=404, detail="找不到申請記錄")
        
        application = app_result.data[0]
        
        # 記錄憑證領取歷史
        await record_credential_history(
            application_id=application_id,
            user_id=application.get("applicant_id"),
            action_type="credential_issued",
            status="issued",
            transaction_id=transaction_id,
            issuer_organization="台南市政府災害救助中心",
            notes="使用者已掃描 QR Code 並將憑證儲存至數位皮夾"
        )
        
        return {
            "success": True,
            "message": "憑證領取記錄已儲存"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"記錄憑證領取失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康檢查"""
    gov_service = get_gov_wallet_service()
    
    return {
        "status": "ok",
        "service": "complete-flow",
        "issuer_api": "connected" if gov_service.issuer_api_key else "mock",
        "verifier_api": "connected" if gov_service.verifier_api_key else "mock"
    }

