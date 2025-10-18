"""
區域管理 API 路由
處理區域（里/鄰）管理功能
"""
from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

from app.services.auth import get_current_user, require_admin
from app.models.database import db_service

router = APIRouter(prefix="/api/v1/districts", tags=["區域管理"])


# ==========================================
# Pydantic 模型
# ==========================================

class DistrictCreate(BaseModel):
    """建立區域請求"""
    district_code: str = Field(..., description="區域代碼，例如：TN-CW-001")
    district_name: str = Field(..., description="區域名稱，例如：中西區-民權里")
    city: str = Field(..., description="城市，例如：台南市")
    district: str = Field(..., description="行政區，例如：中西區")
    village: Optional[str] = Field(None, description="里，例如：民權里")
    neighborhood: Optional[str] = Field(None, description="鄰")
    contact_person: Optional[str] = Field(None, description="里長姓名")
    contact_phone: Optional[str] = Field(None, description="聯絡電話")
    contact_email: Optional[str] = Field(None, description="聯絡 Email")


class DistrictUpdate(BaseModel):
    """更新區域請求"""
    district_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: Optional[bool] = None


# ==========================================
# API 端點
# ==========================================

@router.get("/", response_model=List[Dict], summary="取得區域列表")
async def get_districts(
    city: Optional[str] = Query(None, description="篩選城市"),
    district: Optional[str] = Query(None, description="篩選行政區"),
    is_active: bool = Query(True, description="是否只顯示啟用的區域"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    取得區域列表
    
    - **city**: 篩選城市（可選）
    - **district**: 篩選行政區（可選）
    - **is_active**: 是否只顯示啟用的區域
    - **limit**: 限制數量
    """
    try:
        query = db_service.client.table('districts').select('*')
        
        if city:
            query = query.eq('city', city)
        
        if district:
            query = query.eq('district', district)
        
        if is_active:
            query = query.eq('is_active', True)
        
        query = query.order('district_code').limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得區域列表失敗: {str(e)}"
        )


@router.get("/{district_id}", response_model=Dict, summary="取得區域詳情")
async def get_district(district_id: str):
    """
    取得單一區域的詳細資訊
    """
    try:
        result = db_service.client.table('districts') \
            .select('*') \
            .eq('id', district_id) \
            .single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="區域不存在"
            )
        
        return result.data
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得區域失敗: {str(e)}"
        )


@router.post("/", response_model=Dict, summary="建立新區域")
async def create_district(
    request: DistrictCreate,
    current_user: Dict = Depends(require_admin)
):
    """
    建立新區域（僅管理員）
    """
    try:
        # 檢查區域代碼是否已存在
        existing = None
        try:
            existing = db_service.client.table('districts') \
                .select('id') \
                .eq('district_code', request.district_code) \
                .single() \
                .execute()
        except:
            pass
        
        if existing and existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此區域代碼已存在"
            )
        
        # 建立區域
        district_data = request.dict()
        district_data['is_active'] = True
        
        result = db_service.client.table('districts').insert(
            district_data
        ).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="區域建立失敗"
            )
        
        return result.data[0]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"建立區域失敗: {str(e)}"
        )


@router.patch("/{district_id}", response_model=Dict, summary="更新區域資訊")
async def update_district(
    district_id: str,
    request: DistrictUpdate,
    current_user: Dict = Depends(require_admin)
):
    """
    更新區域資訊（僅管理員）
    """
    try:
        # 檢查區域是否存在
        existing = db_service.client.table('districts') \
            .select('id') \
            .eq('id', district_id) \
            .single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="區域不存在"
            )
        
        # 更新區域
        update_data = request.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="沒有需要更新的資料"
            )
        
        result = db_service.client.table('districts').update(
            update_data
        ).eq('id', district_id).execute()
        
        return result.data[0] if result.data else {}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新區域失敗: {str(e)}"
        )


@router.delete("/{district_id}", response_model=Dict, summary="刪除區域")
async def delete_district(
    district_id: str,
    current_user: Dict = Depends(require_admin)
):
    """
    刪除區域（僅管理員）
    
    實際上是將區域設為停用（軟刪除），而不是真的刪除
    """
    try:
        result = db_service.client.table('districts').update({
            'is_active': False
        }).eq('id', district_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="區域不存在"
            )
        
        return {
            "message": "區域已停用",
            "district_id": district_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除區域失敗: {str(e)}"
        )


@router.get("/{district_id}/applications", response_model=List[Dict], summary="取得區域的申請案件")
async def get_district_applications(
    district_id: str,
    status_filter: Optional[str] = Query(None, description="篩選案件狀態"),
    limit: int = Query(50, ge=1, le=500),
    current_user: Dict = Depends(get_current_user)
):
    """
    取得指定區域的所有申請案件
    
    - 管理員可查看所有區域
    - 里長只能查看自己轄區
    """
    # 檢查權限
    if current_user['role'] == 'reviewer':
        if current_user.get('district_id') != district_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您沒有權限查看此區域的案件"
            )
    elif current_user['role'] == 'applicant':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="災民無法查看區域案件列表"
        )
    
    try:
        query = db_service.client.table('applications') \
            .select('*') \
            .eq('district_id', district_id)
        
        if status_filter:
            query = query.eq('status', status_filter)
        
        query = query.order('submitted_at', desc=True).limit(limit)
        
        result = query.execute()
        return result.data if result.data else []
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得區域案件失敗: {str(e)}"
        )


@router.get("/{district_id}/stats", response_model=Dict, summary="取得區域統計")
async def get_district_stats(
    district_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    取得區域的統計資料
    
    包含：
    - 總申請案件數
    - 各狀態案件數
    - 核准金額總計
    """
    # 檢查權限
    if current_user['role'] == 'reviewer':
        if current_user.get('district_id') != district_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您沒有權限查看此區域的統計"
            )
    elif current_user['role'] == 'applicant':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="災民無法查看區域統計"
        )
    
    try:
        # 取得所有案件
        result = db_service.client.table('applications') \
            .select('status, approved_amount') \
            .eq('district_id', district_id) \
            .execute()
        
        applications = result.data if result.data else []
        
        # 統計
        stats = {
            "total_applications": len(applications),
            "status_breakdown": {},
            "total_approved_amount": 0,
            "approved_applications": 0
        }
        
        for app in applications:
            status_val = app['status']
            stats['status_breakdown'][status_val] = stats['status_breakdown'].get(status_val, 0) + 1
            
            if status_val in ['approved', 'completed', 'disbursed'] and app.get('approved_amount'):
                stats['total_approved_amount'] += float(app['approved_amount'])
                stats['approved_applications'] += 1
        
        return stats
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取得區域統計失敗: {str(e)}"
        )

