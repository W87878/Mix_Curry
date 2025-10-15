"""
審核相關 API 路由
"""
from fastapi import APIRouter, HTTPException, status
from app.models.models import ReviewRecordCreate, ReviewRecordResponse, APIResponse
from app.models.database import db_service
from datetime import datetime

router = APIRouter(prefix="/reviews", tags=["審核管理"])

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_review_record(review: ReviewRecordCreate):
    """
    建立審核記錄
    
    - **application_id**: 申請案件 ID
    - **reviewer_id**: 審核員 ID
    - **reviewer_name**: 審核員姓名
    - **action**: 動作 (submitted, under_review, site_inspection, approved, rejected)
    - **new_status**: 新狀態
    - **comments**: 審核意見
    - **decision_reason**: 核准/駁回理由
    """
    try:
        # 檢查申請案件是否存在
        application = db_service.get_application_by_id(review.application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        # 檢查審核員是否存在
        reviewer = db_service.get_user_by_id(review.reviewer_id)
        if not reviewer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="審核員不存在"
            )
        
        # 檢查審核員權限
        if reviewer.get('role') not in ['reviewer', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您沒有審核權限"
            )
        
        # 建立審核記錄
        review_data = review.model_dump()
        result = db_service.create_review_record(review_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="建立審核記錄失敗"
            )
        
        # 更新申請案件狀態
        update_data = {'status': review.new_status}
        
        # 如果是核准或駁回，記錄審核時間
        if review.new_status in ['approved', 'rejected']:
            update_data['reviewed_at'] = datetime.now().isoformat()
        
        # 如果是完成，記錄完成時間
        if review.new_status == 'completed':
            update_data['completed_at'] = datetime.now().isoformat()
        
        db_service.update_application_status(review.application_id, **update_data)
        
        return APIResponse(
            success=True,
            message="審核記錄建立成功",
            data=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/application/{application_id}", response_model=APIResponse)
async def get_review_records(application_id: str):
    """
    取得申請案件的所有審核記錄
    """
    try:
        # 檢查申請案件是否存在
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        # 取得審核記錄
        records = db_service.get_review_records_by_application(application_id)
        
        return APIResponse(
            success=True,
            message=f"找到 {len(records)} 筆審核記錄",
            data={"records": records, "total": len(records)}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.post("/approve/{application_id}", response_model=APIResponse)
async def approve_application(
    application_id: str,
    reviewer_id: str,
    reviewer_name: str,
    approved_amount: float,
    decision_reason: str = ""
):
    """
    核准申請案件
    
    - **application_id**: 申請案件 ID
    - **reviewer_id**: 審核員 ID
    - **reviewer_name**: 審核員姓名
    - **approved_amount**: 核准金額
    - **decision_reason**: 核准理由
    """
    try:
        # 檢查申請案件是否存在
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        # 建立審核記錄
        review_data = {
            "application_id": application_id,
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "action": "approved",
            "previous_status": application['status'],
            "new_status": "approved",
            "decision_reason": decision_reason
        }
        db_service.create_review_record(review_data)
        
        # 更新申請案件
        update_data = {
            "status": "approved",
            "approved_amount": approved_amount,
            "reviewed_at": datetime.now().isoformat()
        }
        db_service.update_application_status(application_id, **update_data)
        
        return APIResponse(
            success=True,
            message="申請案件已核准",
            data={"application_id": application_id, "approved_amount": approved_amount}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.post("/reject/{application_id}", response_model=APIResponse)
async def reject_application(
    application_id: str,
    reviewer_id: str,
    reviewer_name: str,
    decision_reason: str
):
    """
    駁回申請案件
    
    - **application_id**: 申請案件 ID
    - **reviewer_id**: 審核員 ID
    - **reviewer_name**: 審核員姓名
    - **decision_reason**: 駁回理由
    """
    try:
        # 檢查申請案件是否存在
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        # 建立審核記錄
        review_data = {
            "application_id": application_id,
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "action": "rejected",
            "previous_status": application['status'],
            "new_status": "rejected",
            "decision_reason": decision_reason
        }
        db_service.create_review_record(review_data)
        
        # 更新申請案件
        update_data = {
            "status": "rejected",
            "reviewed_at": datetime.now().isoformat(),
            "review_notes": decision_reason
        }
        db_service.update_application_status(application_id, **update_data)
        
        return APIResponse(
            success=True,
            message="申請案件已駁回",
            data={"application_id": application_id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

