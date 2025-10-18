"""
通知系統 API 路由
處理通知的查詢、標記已讀等功能
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.services.auth import get_current_user
from app.services.notifications import notification_service

router = APIRouter(prefix="/api/v1/notifications", tags=["通知系統"])


# ==========================================
# Pydantic 模型
# ==========================================

class CreateNotificationRequest(BaseModel):
    """建立通知請求（內部使用）"""
    user_id: str
    notification_type: str
    application_id: Optional[str] = None
    data: Optional[Dict] = None


# ==========================================
# API 端點
# ==========================================

@router.get("/", response_model=List[Dict], summary="取得通知列表")
async def get_notifications(
    unread_only: bool = Query(False, description="是否只取得未讀通知"),
    limit: int = Query(50, ge=1, le=200, description="限制數量"),
    current_user: Dict = Depends(get_current_user)
):
    """
    取得當前使用者的通知列表
    
    - **unread_only**: 是否只取得未讀通知
    - **limit**: 限制數量（預設 50，最多 200）
    """
    try:
        notifications = notification_service.get_user_notifications(
            user_id=current_user['id'],
            unread_only=unread_only,
            limit=limit
        )
        
        return notifications
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得通知失敗: {str(e)}"
        )


@router.get("/unread-count", response_model=Dict, summary="取得未讀通知數量")
async def get_unread_count(current_user: Dict = Depends(get_current_user)):
    """
    取得當前使用者的未讀通知數量
    """
    try:
        count = notification_service.get_unread_count(current_user['id'])
        
        return {
            "unread_count": count
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得未讀數量失敗: {str(e)}"
        )


@router.patch("/{notification_id}/read", response_model=Dict, summary="標記通知為已讀")
async def mark_notification_as_read(
    notification_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    標記單一通知為已讀
    """
    try:
        success = notification_service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user['id']
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="通知不存在或無權限"
            )
        
        return {
            "message": "通知已標記為已讀",
            "notification_id": notification_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"標記通知失敗: {str(e)}"
        )


@router.post("/mark-all-read", response_model=Dict, summary="標記所有通知為已讀")
async def mark_all_as_read(current_user: Dict = Depends(get_current_user)):
    """
    標記當前使用者的所有通知為已讀
    """
    try:
        success = notification_service.mark_all_as_read(current_user['id'])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="標記失敗"
            )
        
        return {
            "message": "所有通知已標記為已讀"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"標記通知失敗: {str(e)}"
        )


@router.get("/types", response_model=Dict, summary="取得支援的通知類型")
async def get_notification_types():
    """
    取得系統支援的通知類型列表
    """
    return {
        "notification_types": list(notification_service.NOTIFICATION_TYPES.keys()),
        "descriptions": {
            k: v["title"] 
            for k, v in notification_service.NOTIFICATION_TYPES.items()
        }
    }

