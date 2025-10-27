"""
使用者相關 API 路由
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional
from app.models.models import UserCreate, UserResponse, APIResponse
from app.models.database import db_service
from app.services.auth import get_current_user

router = APIRouter(prefix="/users", tags=["使用者管理"])


class UpdateUserProfileRequest(BaseModel):
    """更新使用者資料請求"""
    id_number: Optional[str] = Field(None, description="身分證字號（10 碼）")
    phone: Optional[str] = Field(None, description="手機號碼")
    full_name: Optional[str] = Field(None, description="姓名")
    address: Optional[str] = Field(None, description="地址")


@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    """
    建立新使用者
    
    - **email**: 電子郵件
    - **phone**: 電話號碼
    - **full_name**: 全名
    - **id_number**: 身分證字號
    - **role**: 角色 (applicant, reviewer, admin)
    """
    try:
        # 檢查 email 是否已存在
        try:
            existing_user = db_service.get_user_by_email(user.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="此 Email 已被註冊"
                )
        except:
            pass  # 使用者不存在，可以繼續
        
        # 檢查身分證字號是否已存在
        try:
            existing_user = db_service.get_user_by_id_number(user.id_number)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="此身分證字號已被註冊"
                )
        except:
            pass  # 使用者不存在，可以繼續
        
        # 建立使用者
        user_data = user.model_dump()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/{user_id}", response_model=APIResponse)
async def get_user(user_id: str):
    """
    根據 ID 取得使用者資料
    """
    try:
        user = db_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="使用者不存在"
            )
        
        return APIResponse(
            success=True,
            message="取得使用者資料成功",
            data=user
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/email/{email}", response_model=APIResponse)
async def get_user_by_email(email: str):
    """
    根據 Email 取得使用者資料
    """
    try:
        user = db_service.get_user_by_email(email)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="使用者不存在"
            )
        
        return APIResponse(
            success=True,
            message="取得使用者資料成功",
            data=user
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/id-number/{id_number}", response_model=APIResponse)
async def get_user_by_id_number(id_number: str):
    """
    根據身分證字號取得使用者資料
    """
    try:
        user = db_service.get_user_by_id_number(id_number)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="使用者不存在"
            )
        
        return APIResponse(
            success=True,
            message="取得使用者資料成功",
            data=user
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

