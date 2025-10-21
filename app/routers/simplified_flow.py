"""
簡化版完整流程 API
專注於政府發行端 + 驗證端 API 整合
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.database import DatabaseService
from app.services.gov_wallet import GovWalletService

router = APIRouter(prefix="/api/v1/simplified", tags=["simplified"])

# 初始化服務
db_service = DatabaseService()
gov_wallet_service = GovWalletService()


# ==========================================
# 請求/回應模型
# ==========================================

class SubmitApplicationRequest(BaseModel):
    """提交申請"""
    applicant_name: str
    id_number: str
    phone: str
    disaster_type: str  # typhoon, flood, earthquake
    address: str
    requested_amount: float
    damage_description: Optional[str] = ""


class ApplicationResponse(BaseModel):
    """申請回應"""
    success: bool
    application_id: Optional[str] = None
    case_no: Optional[str] = None
    qr_code_data: Optional[str] = None  # Base64 QR Code 圖片
    transaction_id: Optional[str] = None
    deep_link: Optional[str] = None
    message: str


class VerifyCredentialRequest(BaseModel):
    """驗證憑證"""
    transaction_id: str
    vp_token: str  # 從 APP 掃描後取得的 VP Token


class VerifyResponse(BaseModel):
    """驗證回應"""
    success: bool
    verified: bool
    application_id: Optional[str] = None
    case_no: Optional[str] = None
    credential_data: Optional[Dict[str, Any]] = None
    message: str


# ==========================================
# API 端點
# ==========================================

@router.post("/submit-application", response_model=ApplicationResponse)
async def submit_application(request: SubmitApplicationRequest):
    """
    🎯 完整流程 - 步驟 1：提交申請並產生 QR Code
    
    流程：
    1. 儲存申請資料到資料庫
    2. 自動呼叫政府發行端 API
    3. 返回 QR Code 給前端顯示
    """
    try:
        # 1. 生成案件編號
        case_no = f"TNN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 2. 儲存申請到資料庫
        application_data = {
            "case_no": case_no,
            "applicant_name": request.applicant_name,
            "id_number": request.id_number,
            "phone": request.phone,
            "disaster_type": request.disaster_type,
            "address": request.address,
            "damage_description": request.damage_description,
            "requested_amount": request.requested_amount,
            "approved_amount": request.requested_amount,  # 簡化版直接核准
            "status": "approved",  # 簡化版：跳過審核
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = db_service.supabase.table("applications").insert(application_data).execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="儲存申請失敗")
        
        application_id = result.data[0]["id"]
        
        # 3. 呼叫政府發行端 API 產生 QR Code
        qr_result = await gov_wallet_service.issue_disaster_relief_qrcode(
            application_data=application_data,
            approved_amount=request.requested_amount,
            case_no=case_no
        )
        
        if not qr_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"產生 QR Code 失敗: {qr_result.get('message')}"
            )
        
        # 4. 更新資料庫，儲存 QR Code 和 transaction_id
        db_service.supabase.table("applications").update({
            "qr_code_data": qr_result.get("qr_code_data"),
            "transaction_id": qr_result.get("transaction_id"),
            "updated_at": datetime.now().isoformat()
        }).eq("id", application_id).execute()
        
        # 5. 返回結果
        return ApplicationResponse(
            success=True,
            application_id=str(application_id),
            case_no=case_no,
            qr_code_data=qr_result.get("qr_code_data"),
            transaction_id=qr_result.get("transaction_id"),
            deep_link=qr_result.get("deep_link"),
            message="申請成功！請使用數位憑證 APP 掃描 QR Code"
        )
        
    except Exception as e:
        print(f"提交申請錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-credential", response_model=VerifyResponse)
async def verify_credential(request: VerifyCredentialRequest):
    """
    🎯 完整流程 - 步驟 2：驗證憑證（APP 掃描後呼叫）
    
    流程：
    1. 接收 APP 掃描後的 VP Token
    2. 呼叫政府驗證端 API
    3. 更新申請狀態為「已發放」
    """
    try:
        # 1. 呼叫政府驗證端 API
        verify_result = await gov_wallet_service.verify_presentation(
            vp_token=request.vp_token,
            transaction_id=request.transaction_id
        )
        
        if not verify_result.get("verified"):
            return VerifyResponse(
                success=False,
                verified=False,
                message=f"憑證驗證失敗: {verify_result.get('message')}"
            )
        
        # 2. 從資料庫查詢對應的申請
        result = db_service.supabase.table("applications")\
            .select("*")\
            .eq("transaction_id", request.transaction_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="找不到對應的申請記錄")
        
        application = result.data[0]
        
        # 3. 更新狀態為「已發放」
        db_service.supabase.table("applications").update({
            "status": "disbursed",
            "disbursed_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }).eq("id", application["id"]).execute()
        
        # 4. 返回結果
        return VerifyResponse(
            success=True,
            verified=True,
            application_id=str(application["id"]),
            case_no=application["case_no"],
            credential_data=verify_result.get("credential_subject"),
            message="憑證驗證成功！補助已發放"
        )
        
    except Exception as e:
        print(f"驗證憑證錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/application/{case_no}")
async def get_application(case_no: str):
    """
    查詢申請狀態
    """
    try:
        result = db_service.supabase.table("applications")\
            .select("*")\
            .eq("case_no", case_no)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="找不到申請記錄")
        
        application = result.data[0]
        
        return {
            "success": True,
            "application": {
                "id": application["id"],
                "case_no": application["case_no"],
                "applicant_name": application["applicant_name"],
                "status": application["status"],
                "requested_amount": application["requested_amount"],
                "approved_amount": application.get("approved_amount"),
                "transaction_id": application.get("transaction_id"),
                "qr_code_data": application.get("qr_code_data"),
                "created_at": application["created_at"],
                "disbursed_at": application.get("disbursed_at")
            }
        }
        
    except Exception as e:
        print(f"查詢申請錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "ok",
        "service": "simplified-flow",
        "gov_api": "connected" if gov_wallet_service.use_real_api else "mock"
    }

