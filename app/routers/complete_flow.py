"""
完整的政府 API 流程
符合真實的災害補助領取流程
"""
from fastapi import APIRouter, HTTPException
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
        
        # 6. TODO: 發送通知給災民（包含 QR Code）
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

