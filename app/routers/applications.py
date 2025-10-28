"""
申請案件相關 API 路由
颱風水災受災戶申請管理
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
from app.models.models import (
    ApplicationCreate, 
    ApplicationResponse, 
    ApplicationUpdate,
    ApplicationDetailResponse,
    APIResponse
)
from app.models.database import db_service

router = APIRouter(prefix="/applications", tags=["申請案件（颱風水災）"])

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_application(application: ApplicationCreate):
    """
    建立新的災民補助申請案件
    
    - **applicant_id**: 申請人 ID
    - **applicant_name**: 申請人姓名
    - **id_number**: 身分證字號
    - **phone**: 聯絡電話
    - **address**: 聯絡地址
    - **disaster_date**: 災害發生日期
    - **disaster_type**: 災害類型
    - **damage_description**: 災損描述
    - **damage_location**: 災損地點
    - **subsidy_type**: 補助類型
    """
    try:
        # 確保用戶存在，如果不存在則創建
        user_exists = False
        try:
            user = db_service.get_user_by_id(application.applicant_id)
            if user:
                user_exists = True
                
                # 如果是 Google 登入的使用者（id_number 以 GOOGLE_ 開頭）
                # 則更新為真實的身分證字號和手機號碼
                if user.get("id_number", "").startswith("GOOGLE_"):
                    update_data = {
                        "id_number": application.id_number,
                        "phone": application.phone,
                        "is_verified": True,  # 填寫完整資料後標記為已驗證
                        "updated_at": datetime.now().isoformat()
                    }
                    db_service.client.table("users").update(update_data).eq("id", application.applicant_id).execute()
                    print(f"已更新 Google 登入使用者的身分證和手機: {application.applicant_id}")
                
        except Exception as e:
            print(f"檢查用戶存在時出錯: {e}")
        
        if not user_exists:
            # 必須先創建用戶
            try:
                user_data = {
                    "id": application.applicant_id,
                    "email": f"{application.id_number}@auto.generated",
                    "full_name": application.applicant_name,
                    "id_number": application.id_number,
                    "phone": application.phone,
                    "role": "applicant",
                    "created_at": datetime.now().isoformat(),
                    "is_active": True
                }
                
                user_result = db_service.client.table("users").insert(user_data).execute()
                
                if not user_result.data:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="無法創建用戶"
                    )
                    
                print(f"成功創建用戶: {application.applicant_id}")
                
            except Exception as e:
                print(f"創建用戶失敗: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"創建用戶失敗: {str(e)}"
                )
        
        # 建立申請案件
        application_data = application.model_dump()
        result = db_service.create_application(application_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="建立申請案件失敗"
            )
        
        return APIResponse(
            success=True,
            message="申請案件建立成功",
            data=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/{application_id}", response_model=APIResponse)
async def get_application(application_id: str):
    """
    根據 ID 取得申請案件詳情
    """
    try:
        application = db_service.get_application_by_id(application_id)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        # 取得相關資料
        photos = db_service.get_photos_by_application(application_id)
        review_records = db_service.get_review_records_by_application(application_id)
        subsidy_items = db_service.get_subsidy_items_by_application(application_id)
        
        # 嘗試取得憑證（可能不存在）
        try:
            certificate = db_service.get_certificate_by_application(application_id)
        except:
            certificate = None
        
        detail = {
            "application": application,
            "photos": photos,
            "review_records": review_records,
            "subsidy_items": subsidy_items,
            "certificate": certificate
        }
        
        return APIResponse(
            success=True,
            message="取得申請案件成功",
            data=detail
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/case-no/{case_no}", response_model=APIResponse)
async def get_application_by_case_no(case_no: str):
    """
    根據案件編號取得申請案件
    """
    try:
        application = db_service.get_application_by_case_no(case_no)
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        return APIResponse(
            success=True,
            message="取得申請案件成功",
            data=application
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/applicant/{applicant_id}", response_model=APIResponse)
async def get_applications_by_applicant(applicant_id: str):
    """
    取得特定申請人的所有申請案件
    """
    try:
        applications = db_service.get_applications_by_applicant(applicant_id)
        
        return APIResponse(
            success=True,
            message=f"找到 {len(applications)} 筆申請案件",
            data={"applications": applications, "total": len(applications)}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/status/{status}", response_model=APIResponse)
async def get_applications_by_status(
    status: str, 
    limit: int = 50
):
    """
    根據狀態取得申請案件列表
    
    - **status**: 案件狀態 (pending, under_review, site_inspection, approved, rejected, completed)
    - **limit**: 回傳數量限制，預設 50
    """
    try:
        applications = db_service.get_applications_by_status(status, limit)
        
        return APIResponse(
            success=True,
            message=f"找到 {len(applications)} 筆 {status} 狀態的申請案件",
            data={"applications": applications, "total": len(applications)}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )


@router.get("/district/{district_id}", response_model=APIResponse)
async def get_applications_by_district(
    district_id: str,
    status: Optional[str] = None,
    limit: int = 100
):
    """
    根據區域 ID 取得申請案件列表（里長專用）
    
    **暫時方案**: 由於災民提交申請時未設定 district_id，
    目前返回所有案件。未來會根據地址自動匹配區域。
    
    - **district_id**: 區域 ID（暫時未使用）
    - **status**: 可選的狀態篩選 (pending, under_review, approved, rejected)
    - **limit**: 回傳數量限制，預設 100
    """
    try:
        # 驗證區域是否存在
        district = None
        try:
            district = db_service.get_district_by_id(district_id)
        except:
            pass
        
        # 暫時方案：查詢所有案件（不限區域）
        # TODO: 未來根據 address 或 damage_location 自動匹配區域
        query = db_service.client.table("applications")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(limit)
        
        # 如果有狀態篩選
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        applications = result.data if result.data else []
        
        return APIResponse(
            success=True,
            message=f"找到 {len(applications)} 筆申請案件",
            data={
                "applications": applications,
                "total": len(applications),
                "district": district,
                "note": "⚠️ 暫時顯示所有案件，未來會根據區域篩選"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )


@router.patch("/{application_id}", response_model=APIResponse)
async def update_application(
    application_id: str,
    update_data: ApplicationUpdate
):
    """
    更新申請案件資料
    
    - **status**: 案件狀態
    - **review_notes**: 審核備註
    - **approved_amount**: 核准金額
    """
    try:
        # 檢查案件是否存在
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        # 更新案件
        update_dict = update_data.model_dump(exclude_unset=True)
        result = db_service.update_application_status(application_id, **update_dict)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新申請案件失敗"
            )
        
        return APIResponse(
            success=True,
            message="申請案件更新成功",
            data=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/", response_model=APIResponse)
async def list_applications(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None
):
    """
    列出所有申請案件（支援分頁和篩選）
    
    - **skip**: 跳過幾筆資料
    - **limit**: 回傳數量限制
    - **status**: 可選的狀態篩選
    """
    try:
        if status:
            applications = db_service.get_applications_by_status(status, limit)
        else:
            # 取得所有案件（這裡可以優化成分頁查詢）
            applications = db_service.get_applications_by_status("pending", 1000)
        
        # 簡單分頁
        paginated = applications[skip:skip + limit]
        
        return APIResponse(
            success=True,
            message=f"取得 {len(paginated)} 筆申請案件",
            data={
                "applications": paginated,
                "total": len(applications),
                "skip": skip,
                "limit": limit
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )
