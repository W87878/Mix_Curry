"""
身份驗證 API 路由
處理登入、註冊、Token 刷新等功能
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict
from datetime import timedelta

from app.services.auth import (
    auth_service,
    get_current_user,
    require_admin,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.services.notifications import notification_service
from app.services.digital_id import verify_digital_credential, generate_test_credential
from app.services.digital_id_v2 import (
    digital_id_service_v2,
    generate_login_qr_code,
    check_login_status,
    mock_verify
)
from app.models.database import db_service

router = APIRouter(prefix="/api/v1/auth", tags=["身份驗證"])


# ==========================================
# Pydantic 模型
# ==========================================

class LoginRequest(BaseModel):
    """登入請求"""
    email: EmailStr
    password: Optional[str] = None  # 可選，如果使用數位憑證則不需要
    digital_credential: Optional[Dict] = None  # 數位憑證資料
    login_type: str = Field(default="password", description="登入方式: password 或 digital_id")


class LoginResponse(BaseModel):
    """登入回應"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict
    expires_in: int


class RegisterRequest(BaseModel):
    """註冊請求"""
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    full_name: str = Field(..., min_length=2, max_length=100)
    id_number: str = Field(..., min_length=10, max_length=20)
    role: str = Field(default="applicant", description="角色: applicant, reviewer, admin")
    district_id: Optional[str] = Field(None, description="區域 ID（里長專用）")
    password: Optional[str] = Field(None, min_length=8, description="密碼（可選，支援數位憑證登入）")


class RefreshTokenRequest(BaseModel):
    """刷新 Token 請求"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """修改密碼請求"""
    old_password: str
    new_password: str = Field(..., min_length=8)


class VerifyDigitalIDRequest(BaseModel):
    """驗證數位身份請求"""
    id_number: str
    digital_credential: Dict


# ==========================================
# API 端點
# ==========================================

@router.post("/register", response_model=Dict, summary="註冊新使用者")
async def register(request: RegisterRequest):
    """
    註冊新使用者
    
    - **email**: 電子郵件
    - **phone**: 手機號碼
    - **full_name**: 姓名
    - **id_number**: 身分證字號
    - **role**: 角色（applicant, reviewer, admin）
    - **district_id**: 區域 ID（里長必填）
    - **password**: 密碼（可選）
    """
    try:
        # 檢查 email 是否已存在
        existing_user = None
        try:
            existing_user = db_service.get_user_by_email(request.email)
        except:
            pass
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此 Email 已被註冊"
            )
        
        # 檢查身分證字號是否已存在
        existing_id = None
        try:
            existing_id = db_service.get_user_by_id_number(request.id_number)
        except:
            pass
        
        if existing_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此身分證字號已被註冊"
            )
        
        # 檢查里長是否有填寫區域
        if request.role == "reviewer" and not request.district_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="里長帳號必須指定所屬區域"
            )
        
        # 建立使用者
        user_data = {
            "email": request.email,
            "phone": request.phone,
            "full_name": request.full_name,
            "id_number": request.id_number,
            "role": request.role,
            "district_id": request.district_id,
            "is_active": True,
            "is_verified": False,
            # TODO: 加密密碼
            # "password": auth_service.hash_password(request.password) if request.password else None
        }
        
        user = db_service.create_user(user_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="使用者建立失敗"
            )
        
        return {
            "message": "註冊成功",
            "user": {
                "id": user['id'],
                "email": user['email'],
                "full_name": user['full_name'],
                "role": user['role']
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"註冊失敗: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse, summary="使用者登入")
async def login(request: LoginRequest):
    """
    使用者登入
    
    支援兩種登入方式：
    1. **密碼登入**: 提供 email + password
    2. **數位憑證登入**: 提供 email + digital_credential
    """
    try:
        user = None
        
        if request.login_type == "digital_id" and request.digital_credential:
            # 數位憑證登入
            # 1. 先找到使用者
            user = db_service.get_user_by_email(request.email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="使用者不存在"
                )
            
            # 2. 驗證數位身份
            verified = await auth_service.verify_digital_identity(
                user['id_number'],
                request.digital_credential
            )
            
            if not verified:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="數位憑證驗證失敗"
                )
            
            # 更新驗證狀態
            db_service.client.table('users').update({
                'twfido_verified': True,
                'digital_identity': request.digital_credential,
                'last_login_at': datetime.now().isoformat()
            }).eq('id', user['id']).execute()
            
        elif request.login_type == "password":
            # 密碼登入
            # 注意：目前資料庫沒有 password 欄位，所以只驗證 email 是否存在
            user = db_service.get_user_by_email(request.email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="使用者不存在"
                )
            
            # TODO: 實作密碼驗證
            # 目前暫時允許任何密碼登入（開發模式）
            # if request.password:
            #     verified = auth_service.verify_password(request.password, user.get('password'))
            #     if not verified:
            #         raise HTTPException(
            #             status_code=status.HTTP_401_UNAUTHORIZED,
            #             detail="密碼錯誤"
            #         )
            
            # 更新最後登入時間
            db_service.client.table('users').update({
                'last_login_at': datetime.now().isoformat()
            }).eq('id', user['id']).execute()
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="請提供有效的登入憑證"
            )
        
        # 檢查帳戶狀態
        if not user.get('is_active'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="帳戶已被停用"
            )
        
        # 生成 Token
        token_data = {
            "user_id": user['id'],
            "email": user['email'],
            "role": user['role'],
            "district_id": user.get('district_id')
        }
        
        access_token = auth_service.create_access_token(token_data)
        refresh_token = auth_service.create_refresh_token({"user_id": user['id']})
        
        # 移除敏感資訊
        safe_user = {
            "id": user['id'],
            "email": user['email'],
            "full_name": user['full_name'],
            "role": user['role'],
            "district_id": user.get('district_id'),
            "is_verified": user.get('is_verified', False)
        }
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=safe_user,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登入失敗: {str(e)}"
        )


@router.post("/refresh", response_model=Dict, summary="刷新 Access Token")
async def refresh_token(request: RefreshTokenRequest):
    """
    使用 Refresh Token 刷新 Access Token
    """
    try:
        # 驗證 refresh token
        payload = auth_service.verify_token(request.refresh_token)
        
        if payload.get('type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的 Refresh Token"
            )
        
        user_id = payload.get('user_id')
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的 Token"
            )
        
        # 取得使用者資料
        user = db_service.get_user_by_id(user_id)
        if not user or not user.get('is_active'):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="使用者不存在或已停用"
            )
        
        # 生成新的 access token
        token_data = {
            "user_id": user['id'],
            "email": user['email'],
            "role": user['role'],
            "district_id": user.get('district_id')
        }
        
        new_access_token = auth_service.create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token 刷新失敗: {str(e)}"
        )


@router.get("/me", response_model=Dict, summary="取得當前使用者資訊")
async def get_me(current_user: Dict = Depends(get_current_user)):
    """
    取得當前登入使用者的資訊
    """
    # 移除敏感資訊
    safe_user = {
        "id": current_user['id'],
        "email": current_user['email'],
        "phone": current_user.get('phone'),
        "full_name": current_user['full_name'],
        "id_number": current_user['id_number'],
        "role": current_user['role'],
        "district_id": current_user.get('district_id'),
        "is_active": current_user.get('is_active'),
        "is_verified": current_user.get('is_verified'),
        "twfido_verified": current_user.get('twfido_verified'),
        "last_login_at": current_user.get('last_login_at'),
        "created_at": current_user.get('created_at')
    }
    
    # 如果是里長，取得區域資訊
    if current_user.get('district_id'):
        try:
            district = db_service.client.table('districts') \
                .select('*') \
                .eq('id', current_user['district_id']) \
                .single() \
                .execute()
            
            if district.data:
                safe_user['district'] = district.data
        except:
            pass
    
    return safe_user


@router.post("/verify-digital-id", response_model=Dict, summary="驗證數位身份")
async def verify_digital_id(request: VerifyDigitalIDRequest):
    """
    驗證數位身份（TW FidO 或政府數位憑證）
    
    - **id_number**: 身分證字號
    - **digital_credential**: 數位憑證資料
    """
    try:
        verified = await auth_service.verify_digital_identity(
            request.id_number,
            request.digital_credential
        )
        
        return {
            "verified": verified,
            "message": "驗證成功" if verified else "驗證失敗"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"驗證失敗: {str(e)}"
        )


@router.post("/change-password", response_model=Dict, summary="修改密碼")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    修改密碼
    
    - **old_password**: 舊密碼
    - **new_password**: 新密碼（至少 8 個字元）
    """
    # TODO: 實作密碼修改
    # 目前資料庫沒有 password 欄位，需要先加入
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="密碼修改功能尚未實作"
    )


@router.post("/logout", response_model=Dict, summary="登出")
async def logout(current_user: Dict = Depends(get_current_user)):
    """
    登出（客戶端需清除 Token）
    """
    # JWT Token 是無狀態的，實際登出由客戶端處理
    # 可以選擇將 Token 加入黑名單（需要額外實作）
    return {
        "message": "登出成功"
    }


# 匯入必要的模組
from datetime import datetime


# ==========================================
# 數位憑證登入功能
# ==========================================

class DigitalIDLoginRequest(BaseModel):
    """數位憑證登入請求"""
    qr_code_data: str = Field(..., description="數位憑證 QR Code 資料")
    role: Optional[str] = Field(None, description="首次登入時需指定角色")
    phone: Optional[str] = Field(None, description="首次登入時需提供手機號碼")
    email: Optional[EmailStr] = Field(None, description="首次登入時可提供 Email（選填）")
    district_id: Optional[str] = Field(None, description="如果是里長，需提供區域 ID")


class DigitalIDRegisterRequest(BaseModel):
    """數位憑證註冊請求"""
    qr_code_data: str = Field(..., description="數位憑證 QR Code 資料")
    role: str = Field(..., description="角色: applicant, reviewer, admin")
    phone: str = Field(..., min_length=10, max_length=20, description="手機號碼")
    email: Optional[EmailStr] = Field(None, description="Email（選填）")
    district_id: Optional[str] = Field(None, description="區域 ID（里長必填）")


@router.post("/digital-id/login", response_model=LoginResponse, summary="數位憑證登入")
async def digital_id_login(request: DigitalIDLoginRequest):
    """
    使用政府數位憑證登入
    
    流程：
    1. 掃描數位憑證 QR Code
    2. 驗證憑證真實性
    3. 檢查是否為已註冊用戶
    4. 如果是首次使用，需提供角色和手機號碼完成註冊
    5. 返回 JWT Token
    """
    try:
        # 1. 驗證數位憑證
        verification_result = await verify_digital_credential(request.qr_code_data)
        
        if not verification_result["verified"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"數位憑證驗證失敗: {verification_result.get('error', '未知錯誤')}"
            )
        
        user_info = verification_result["user_info"]
        id_number = user_info["id_number"]
        full_name = user_info["full_name"]
        
        # 2. 檢查用戶是否已存在
        existing_user = None
        try:
            existing_user = db_service.get_user_by_id_number(id_number)
        except:
            pass
        
        # 3. 如果用戶不存在，進行首次註冊
        if not existing_user:
            # 首次登入，需要補充資料
            if not request.role or not request.phone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="首次使用請提供角色和手機號碼"
                )
            
            # 里長必須提供區域
            if request.role == "reviewer" and not request.district_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="里長帳號必須指定所屬區域"
                )
            
            # 創建新用戶
            user_data = {
                "id_number": id_number,
                "full_name": full_name,
                "phone": request.phone,
                "email": request.email,
                "role": request.role,
                "district_id": request.district_id,
                "twfido_verified": True,
                "digital_identity": user_info,
                "is_active": True,
                "is_verified": True,
                "last_login_at": datetime.now().isoformat()
            }
            
            user = db_service.create_user(user_data)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="用戶創建失敗"
                )
        else:
            # 已存在用戶，更新登入時間和憑證資訊
            user = existing_user
            try:
                db_service.client.table('users') \
                    .update({
                        'last_login_at': datetime.now().isoformat(),
                        'twfido_verified': True,
                        'digital_identity': user_info
                    }) \
                    .eq('id', user['id']) \
                    .execute()
            except Exception as e:
                print(f"Update login time error: {e}")
        
        # 4. 生成 JWT Token
        access_token = auth_service.create_access_token(
            data={"sub": user['id'], "role": user['role']},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        refresh_token = auth_service.create_refresh_token(
            data={"sub": user['id']}
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user={
                "id": user['id'],
                "email": user.get('email'),
                "full_name": user['full_name'],
                "role": user['role'],
                "id_number": user['id_number'],
                "phone": user.get('phone'),
                "twfido_verified": True
            },
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Digital ID login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"數位憑證登入失敗: {str(e)}"
        )


@router.post("/digital-id/register", response_model=Dict, summary="數位憑證註冊")
async def digital_id_register(request: DigitalIDRegisterRequest):
    """
    使用政府數位憑證註冊
    
    - **qr_code_data**: 數位憑證 QR Code 資料
    - **role**: 角色（applicant, reviewer, admin）
    - **phone**: 手機號碼
    - **email**: Email（選填）
    - **district_id**: 區域 ID（里長必填）
    """
    try:
        # 1. 驗證數位憑證
        verification_result = await verify_digital_credential(request.qr_code_data)
        
        if not verification_result["verified"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"數位憑證驗證失敗: {verification_result.get('error', '未知錯誤')}"
            )
        
        user_info = verification_result["user_info"]
        id_number = user_info["id_number"]
        full_name = user_info["full_name"]
        
        # 2. 檢查是否已註冊
        existing_user = None
        try:
            existing_user = db_service.get_user_by_id_number(id_number)
        except:
            pass
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此身分證字號已註冊，請直接登入"
            )
        
        # 3. 檢查里長是否有填寫區域
        if request.role == "reviewer" and not request.district_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="里長帳號必須指定所屬區域"
            )
        
        # 4. 創建用戶
        user_data = {
            "id_number": id_number,
            "full_name": full_name,
            "phone": request.phone,
            "email": request.email,
            "role": request.role,
            "district_id": request.district_id,
            "twfido_verified": True,
            "digital_identity": user_info,
            "is_active": True,
            "is_verified": True
        }
        
        user = db_service.create_user(user_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="使用者建立失敗"
            )
        
        return {
            "message": "註冊成功",
            "user": {
                "id": user['id'],
                "full_name": user['full_name'],
                "id_number": user['id_number'],
                "role": user['role'],
                "twfido_verified": True
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Digital ID register error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"註冊失敗: {str(e)}"
        )


@router.get("/digital-id/generate-test-qr", response_model=Dict, summary="生成測試用 QR Code")
async def generate_test_qr(
    id_number: str = "A123456789",
    full_name: str = "測試用戶"
):
    """
    生成測試用數位憑證 QR Code（開發測試用）
    
    - **id_number**: 身分證字號
    - **full_name**: 姓名
    
    返回 QR Code 資料，可以直接用於測試登入
    """
    qr_code_data = generate_test_credential(id_number, full_name)
    
    return {
        "qr_code_data": qr_code_data,
        "usage": "將此資料貼到「數位憑證登入」的 QR Code 欄位進行測試",
        "example": {
            "id_number": id_number,
            "full_name": full_name
        }
    }


# ==========================================
# 數位憑證登入 V2 - 正確的掃描流程
# ==========================================

@router.get("/digital-id-v2/generate-qr", response_model=Dict, summary="產生供 APP 掃描的 QR Code（正確流程）")
async def generate_scan_qr_code():
    """
    產生供政府 APP 掃描的 QR Code（正確流程）
    
    流程：
    1. 網站呼叫此 API 產生 QR Code
    2. 使用者用政府 APP 掃描
    3. APP 向政府後端驗證
    4. 前端輪詢檢查驗證狀態
    5. 驗證成功後完成登入
    
    返回：
    - session_id: 用於輪詢狀態
    - qr_code_data: QR Code 內容（JSON）
    - qr_code_url: Deep link（可直接喚起 APP）
    - expires_in: 有效時間（秒）
    """
    result = generate_login_qr_code()
    
    return {
        "session_id": result["session_id"],
        "qr_code_data": result["qr_code_data"],
        "qr_code_url": result["qr_code_url"],
        "expires_in": result["expires_in"],
        "instructions": {
            "step1": "使用政府數位憑證 APP 掃描此 QR Code",
            "step2": "在 APP 中完成身份驗證（指紋/臉部辨識）",
            "step3": "前端自動輪詢此 session_id 的狀態",
            "step4": "驗證成功後自動登入"
        }
    }


@router.get("/digital-id-v2/check-status/{session_id}", response_model=Dict, summary="檢查驗證狀態（輪詢用）")
async def check_verification_status(session_id: str):
    """
    檢查數位憑證驗證狀態（前端輪詢）
    
    前端應該每 2-3 秒呼叫一次此 API，檢查使用者是否已完成 APP 掃描
    
    狀態：
    - pending: 等待掃描
    - verified: 驗證成功
    - expired: QR Code 已過期
    - failed: 驗證失敗
    """
    result = await check_login_status(session_id)
    
    return result


@router.post("/digital-id-v2/complete-login/{session_id}", response_model=LoginResponse, summary="完成登入（驗證成功後）")
async def complete_digital_id_login(
    session_id: str,
    role: Optional[str] = None,
    phone: Optional[str] = None,
    email: Optional[EmailStr] = None,
    district_id: Optional[str] = None
):
    """
    完成數位憑證登入（在驗證成功後呼叫）
    
    流程：
    1. 前端輪詢發現 status = 'verified'
    2. 呼叫此 API 完成登入
    3. 如果是首次使用，需提供 role, phone 等資料
    4. 系統產生 JWT Token
    5. 返回用戶資訊和 Token
    """
    # 檢查驗證狀態
    status_result = await check_login_status(session_id)
    
    if status_result["status"] != "verified":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"驗證尚未完成，當前狀態：{status_result['status']}"
        )
    
    user_info = status_result["user_info"]
    id_number = user_info["id_number"]
    full_name = user_info["full_name"]
    
    # 檢查用戶是否已存在
    existing_user = None
    try:
        existing_user = db_service.get_user_by_id_number(id_number)
    except:
        pass
    
    # 如果用戶不存在，進行註冊
    if not existing_user:
        if not role or not phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="首次使用請提供角色和手機號碼"
            )
        
        # 里長必須提供區域
        if role == "reviewer" and not district_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="里長帳號必須指定所屬區域"
            )
        
        # 創建新用戶
        user_data = {
            "id_number": id_number,
            "full_name": full_name,
            "phone": phone,
            "email": email,
            "role": role,
            "district_id": district_id,
            "twfido_verified": True,
            "digital_identity": user_info,
            "is_active": True,
            "is_verified": True,
            "last_login_at": datetime.now().isoformat()
        }
        
        user = db_service.create_user(user_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用戶創建失敗"
            )
    else:
        # 已存在用戶，更新登入時間
        user = existing_user
        try:
            db_service.client.table('users') \
                .update({
                    'last_login_at': datetime.now().isoformat(),
                    'twfido_verified': True,
                    'digital_identity': user_info
                }) \
                .eq('id', user['id']) \
                .execute()
        except Exception as e:
            print(f"Update login time error: {e}")
    
    # 生成 JWT Token
    access_token = auth_service.create_access_token(
        data={"sub": user['id'], "role": user['role']},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = auth_service.create_refresh_token(
        data={"sub": user['id']}
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user={
            "id": user['id'],
            "email": user.get('email'),
            "full_name": user['full_name'],
            "role": user['role'],
            "id_number": user['id_number'],
            "phone": user.get('phone'),
            "twfido_verified": True
        },
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/digital-id-v2/callback", response_model=Dict, summary="政府後端驗證回調（Webhook）")
async def digital_id_callback(verification_data: Dict):
    """
    接收政府後端的驗證回調（如果政府支援 Webhook）
    
    政府後端在使用者完成 APP 驗證後，會呼叫此 API 通知驗證結果
    """
    session_id = verification_data.get("session_id")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少 session_id"
        )
    
    result = await digital_id_service_v2.handle_verification_callback(
        session_id,
        verification_data
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return {
        "message": "驗證回調處理成功",
        "session_id": session_id
    }


# ==========================================
# 測試用端點（模擬政府 APP 掃描）
# ==========================================

class MockScanRequest(BaseModel):
    """模擬掃描請求"""
    session_id: str
    id_number: str = Field(..., description="身分證字號")
    full_name: str = Field(..., description="姓名")
    birth_date: Optional[str] = Field("1990-01-01", description="出生日期")


@router.post("/digital-id-v2/mock-scan", response_model=Dict, summary="模擬 APP 掃描（測試用）")
async def mock_app_scan(request: MockScanRequest):
    """
    模擬政府 APP 掃描和驗證（僅供測試）
    
    在沒有真實政府 APP 的情況下，使用此 API 模擬整個掃描流程
    
    使用方式：
    1. 呼叫 /generate-qr 取得 session_id
    2. 呼叫此 API 模擬掃描
    3. 前端輪詢會發現 status 變成 'verified'
    4. 完成登入
    """
    result = await mock_verify(
        request.session_id,
        {
            "id_number": request.id_number,
            "full_name": request.full_name,
            "birth_date": request.birth_date
        }
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["error"]
        )
    
    return {
        "message": "模擬掃描成功",
        "user_info": result["user_info"],
        "next_step": "呼叫 /complete-login/{session_id} 完成登入"
    }

