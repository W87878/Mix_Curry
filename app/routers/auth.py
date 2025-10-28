"""
身份驗證 API 路由
處理登入、註冊、Token 刷新等功能
"""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict
from datetime import timedelta
import secrets
import os
import logging

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
from app.services.google_oauth import google_oauth_service
from app.services.email_verification import EmailVerificationService, send_verification_email
from app.models.database import db_service

# 設定日誌
logger = logging.getLogger(__name__)

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
    verify: Optional[bool] = Field(None, description="Email 驗證狀態：true=已驗證, false=未驗證")


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


class EmailAuthRequest(BaseModel):
    """Email 註冊/登入請求"""
    email: EmailStr
    is_verified: bool = Field(default=False, description="是否已驗證 Email")
    verification_code: Optional[str] = Field(None, description="驗證碼（驗證時必填）")


class EmailAuthResponse(BaseModel):
    """Email 註冊/登入回應"""
    success: bool
    message: str
    verification_code: Optional[str] = Field(None, description="驗證碼（開發環境回傳）")
    user: Optional[Dict] = None
    applications: Optional[list] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None


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
# API 端點 - Email 驗證登入/註冊
# ==========================================

@router.post("/email/auth", response_model=EmailAuthResponse, summary="Email 驗證登入/註冊")
async def email_auth(request: EmailAuthRequest):
    """
    Email 驗證碼發送 API（第一步）
    
    此端點只負責：
    1. 生成驗證碼
    2. 發送驗證郵件
    3. 在開發環境回傳驗證碼（生產環境不回傳）
    
    ⚠️ 注意：此端點不驗證驗證碼，只發送！
    驗證碼的比對由前端完成，登入請使用 /api/v1/auth/login 端點
    
    請求範例：
    ```json
    {
        "email": "user@example.com",
        "is_verified": false
    }
    ```
    
    回應範例（開發環境）：
    ```json
    {
        "success": true,
        "message": "驗證碼已發送到您的 Email",
        "verification_code": "123456"
    }
    ```
    
    回應範例（生產環境）：
    ```json
    {
        "success": true,
        "message": "驗證碼已發送到您的 Email，請在 3 分鐘內輸入"
    }
    ```
    """
    try:
        email = request.email
        
        logger.info(f"發送驗證碼請求: {email}")
        
        # 生成驗證碼
        code = EmailVerificationService.create_verification_code(email)
        
        # 發送驗證郵件
        email_sent = await send_verification_email(
            email=email,
            code=code,
            user_name="使用者"
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="驗證碼發送失敗，請稍後再試"
            )
        
        # 只在開發環境回傳驗證碼
        is_debug = os.getenv("DEBUG", "False").lower() == "true"
        
        return EmailAuthResponse(
            success=True,
            message="驗證碼已發送到您的 Email，請在 3 分鐘內輸入",
            verification_code=code if is_debug else None  # 開發環境才回傳
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"發送驗證碼失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發送驗證碼失敗: {str(e)}"
        )


@router.post("/email/resend", summary="重新發送驗證碼")
async def resend_verification_code(request: Dict):
    """
    重新發送驗證碼
    
    請求格式：
    ```json
    {
        "email": "user@example.com"
    }
    ```
    """
    try:
        email = request.get("email")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少 Email 參數"
            )
        
        # 重新生成驗證碼
        code = EmailVerificationService.resend_code(email)
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="請求過於頻繁，請稍後再試"
            )
        
        # 發送驗證郵件
        email_sent = await send_verification_email(
            email=email,
            code=code,
            user_name="使用者"
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="驗證碼發送失敗，請稍後再試"
            )
        
        # 只在開發環境回傳驗證碼
        is_debug = os.getenv("DEBUG", "False").lower() == "true"
        
        return {
            "success": True,
            "message": "驗證碼已重新發送",
            "verification_code": code if is_debug else None  # 開發環境才回傳
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新發送驗證碼失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新發送驗證碼失敗: {str(e)}"
        )


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
        }
        
        # 如果提供密碼，加密後儲存
        if request.password:
            user_data["password"] = auth_service.hash_password(request.password)
        
        user = db_service.create_user(user_data)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="使用者建立失敗"
            )
        
        # 建立 access token
        access_token = auth_service.create_access_token(
            data={"sub": str(user["id"]), "role": user["role"]}
        )
        refresh_token = auth_service.create_refresh_token(
            data={"sub": str(user["id"])}
        )
        
        return {
            "success": True,
            "message": "註冊成功",
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"]
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"註冊失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"註冊失敗: {str(e)}"
        )


@router.post("/login", response_model=LoginResponse, summary="使用者登入")
async def login(request: LoginRequest):
    """
    使用者登入（第二步）
    
    支援多種登入方式：
    1. **Email 驗證登入**：提供 email 和 verify=true/false
       - verify=true: 前端已驗證成功，建立/登入帳號
       - verify=false: 前端驗證失敗，返回錯誤
    
    2. **密碼登入**：提供 email 和 password
    
    3. **數位憑證登入**：提供 email 和 digital_credential
    
    請求範例：
    ```json
    // Email 驗證登入（驗證成功）
    {
        "email": "user@example.com",
        "login_type": "password",
        "verify": true
    }
    
    // Email 驗證登入（驗證失敗）
    {
        "email": "user@example.com",
        "login_type": "password",
        "verify": false
    }
    
    // 傳統密碼登入
    {
        "email": "user@example.com",
        "password": "mypassword",
        "login_type": "password"
    }
    ```
    """
    try:
        email = request.email
        
        # ========================================
        # 情況 1: Email 驗證登入
        # ========================================
        if request.verify is not None:
            logger.info(f"Email 驗證登入: {email}, verify={request.verify}")
            
            # 如果前端驗證失敗
            if request.verify is False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "message": "驗證碼錯誤",
                        "suggestion": "請重新輸入驗證碼或重新發送",
                        "hint": "您可以點擊「重新發送驗證碼」"
                    }
                )
            
            # 如果前端驗證成功，查找或建立使用者
            user = None
            try:
                user = db_service.get_user_by_email(email)
                logger.info(f"找到現有使用者: {email}")
            except:
                # 使用者不存在，建立新使用者
                logger.info(f"建立新使用者: {email}")
                
                # 生成短的臨時 ID（最多 20 字元）
                # 使用時間戳的後 12 位數字確保唯一性
                import time
                temp_id = f"EMAIL{int(time.time() * 1000) % 1000000000000}"[:20]
                
                user_data = {
                    "email": email,
                    "full_name": email.split("@")[0],  # 臨時名稱
                    "phone": "",  # 待填寫
                    "id_number": temp_id,  # 臨時值（最多20字元）
                    "role": "applicant",
                    "is_active": True,
                    "is_verified": True  # Email 已驗證
                }
                user = db_service.create_user(user_data)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="使用者建立失敗"
                )
            
            # 更新 is_verified 狀態
            if not user.get("is_verified"):
                db_service.update_user(user["id"], {"is_verified": True})
                user["is_verified"] = True
        
        # ========================================
        # 情況 2 & 3: 傳統登入（已棄用密碼）或數位憑證登入
        # ========================================
        else:
            # 查找使用者
            user = None
            try:
                user = db_service.get_user_by_email(email)
            except:
                pass
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "message": "使用者不存在",
                        "suggestion": "請先使用 Email 驗證註冊",
                        "endpoint": "/api/v1/auth/email/auth",
                        "hint": "點擊「Email 驗證登入」開始"
                    }
                )
            
            # 驗證登入方式
            if request.login_type == "password":
                # ⚠️ 密碼登入已棄用，建議使用 Email 驗證
                # 但為了向後相容，仍然允許無密碼登入（僅限已存在的使用者）
                logger.warning(f"使用者 {email} 使用舊式密碼登入（已棄用）")
                
                # 如果提供了密碼但使用者沒有設定密碼，提示改用 Email 驗證
                if request.password and not user.get("password"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "message": "此帳號未設定密碼",
                            "suggestion": "請使用 Email 驗證登入",
                            "endpoint": "/api/v1/auth/email/auth",
                            "hint": "系統已不再使用密碼登入"
                        }
                    )
                
                # 如果使用者有密碼且提供了密碼，驗證密碼
                if user.get("password") and request.password:
                    if not auth_service.verify_password(request.password, user.get("password", "")):
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Email 或密碼錯誤"
                        )
                # 否則允許無密碼登入（向後相容）
            
            elif request.login_type == "digital_id":
                if not request.digital_credential:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="缺少數位憑證"
                    )
                
                # 驗證數位憑證
                is_valid = verify_digital_credential(
                    request.digital_credential,
                    user["id_number"]
                )
                
                if not is_valid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="數位憑證驗證失敗"
                    )
        
        # ========================================
        # 通用：檢查帳號狀態並建立 Token
        # ========================================
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="此帳號已被停用"
            )
        
        # 建立 JWT Token
        token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth_service.create_access_token(
            data={"sub": str(user["id"]), "role": user["role"]},
            expires_delta=token_expires
        )
        refresh_token = auth_service.create_refresh_token(
            data={"sub": str(user["id"])}
        )
        
        logger.info(f"登入成功: {email}")
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user={
                "id": str(user["id"]),
                "email": user["email"],
                "full_name": user.get("full_name", ""),
                "role": user["role"],
                "is_verified": user.get("is_verified", False),
                "district_id": user.get("district_id")  # 新增 district_id
            },
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"登入失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登入失敗: {str(e)}"
        )


# ==========================================
# Google OAuth 端點
# ==========================================

@router.get("/google/login", summary="Google OAuth 登入")
async def google_login():
    """
    開始 Google OAuth 登入流程
    
    此端點會重定向到 Google 登入頁面
    使用者登入後，Google 會回調到 /api/v1/auth/google/callback
    """
    try:
        # 產生 OAuth 授權 URL (同步函數，不需要 await)
        auth_url = google_oauth_service.get_authorization_url()
        
        # 重定向到 Google 登入頁面
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Google OAuth 登入失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google 登入失敗: {str(e)}"
        )


@router.get("/google/callback", summary="Google OAuth 回調")
async def google_callback(code: str = None, error: str = None):
    """
    Google OAuth 回調端點
    
    當使用者在 Google 登入完成後，Google 會重定向到此端點
    並帶上授權碼 (code) 或錯誤訊息 (error)
    
    此端點會：
    1. 用授權碼換取 access token
    2. 取得使用者資訊
    3. 在資料庫中查找或建立使用者
    4. 產生 JWT Token
    5. 重定向到前端頁面並帶上 token
    """
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google 登入失敗: {error}"
        )
    
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少授權碼"
        )
    
    try:
        # 1. 用 code 換取 access token
        token_data = await google_oauth_service.exchange_code_for_token(code)
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise Exception("無法取得 access token")
        
        # 2. 用 access token 取得使用者資訊
        user_info = await google_oauth_service.get_user_info(access_token)
        
        # 3. 在資料庫中查找或建立使用者
        user = await google_oauth_service.login_or_create_user(user_info, db_service)
        
        # 4. 建立 JWT Token
        token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_access_token = auth_service.create_access_token(
            data={"sub": str(user["id"]), "role": user["role"]},
            expires_delta=token_expires
        )
        jwt_refresh_token = auth_service.create_refresh_token(
            data={"sub": str(user["id"])}
        )
        
        # 5. 回傳結果（重定向到前端頁面，並透過 URL 傳遞 token）
        frontend_url = f"/applicant?access_token={jwt_access_token}&refresh_token={jwt_refresh_token}"
        
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        logger.error(f"Google 登入失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google 登入失敗: {str(e)}"
        )


@router.post("/google/token", response_model=LoginResponse, summary="Google Token 登入")
async def google_token_login(request: Dict):
    """
    使用 Google ID Token 進行登入（適用於前端已取得 ID Token 的情況）
    
    前端可以使用 Google Sign-In JavaScript Library 取得 ID Token
    然後呼叫此 API 完成登入
    
    請求格式：
    {
        "id_token": "Google ID Token"
    }
    """
    id_token = request.get("id_token")
    
    if not id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="缺少 ID Token"
        )
    
    try:
        # 1. 驗證 ID Token（簡化版，生產環境應驗證簽章）
        payload = google_oauth_service.verify_id_token(id_token)
        
        # 2. 提取使用者資訊
        user_info = {
            "email": payload.get("email"),
            "name": payload.get("name"),
            "id": payload.get("sub"),
            "picture": payload.get("picture"),
            "verified_email": payload.get("email_verified", False)
        }
        
        # 3. 在資料庫中查找或建立使用者
        user = await google_oauth_service.login_or_create_user(user_info, db_service)
        
        # 4. 建立 JWT Token
        token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_access_token = auth_service.create_access_token(
            data={"sub": str(user["id"]), "role": user["role"]},
            expires_delta=token_expires
        )
        jwt_refresh_token = auth_service.create_refresh_token(
            data={"sub": str(user["id"])}
        )
        
        return LoginResponse(
            access_token=jwt_access_token,
            refresh_token=jwt_refresh_token,
            token_type="bearer",
            user={
                "id": str(user["id"]),
                "email": user["email"],
                "full_name": user.get("full_name", ""),
                "role": user["role"],
                "is_verified": user.get("is_verified", False)
            },
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        logger.error(f"Google Token 登入失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Google 登入失敗: {str(e)}"
        )


# ==========================================
# 其他端點
# ==========================================

@router.post("/refresh", response_model=Dict, summary="刷新 Access Token")
async def refresh_token(request: RefreshTokenRequest):
    """
    使用 Refresh Token 刷新 Access Token
    """
    try:
        # 驗證 refresh token
        payload = auth_service.verify_refresh_token(request.refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的 Refresh Token"
            )
        
        # 查找使用者
        user = db_service.get_user(user_id)
        
        if not user or not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="使用者不存在或已被停用"
            )
        
        # 建立新的 access token
        token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = auth_service.create_access_token(
            data={"sub": str(user["id"]), "role": user["role"]},
            expires_delta=token_expires
        )
        
        return {
            "success": True,
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token 刷新失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 刷新失敗"
        )

