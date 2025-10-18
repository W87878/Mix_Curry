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

