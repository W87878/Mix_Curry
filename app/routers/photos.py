"""
照片上傳相關 API 路由
颱風水災災損照片管理
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from typing import List
from app.models.models import DamagePhotoCreate, DamagePhotoResponse, FileUploadResponse, APIResponse
from app.models.database import db_service
from app.services.storage import storage_service

router = APIRouter(prefix="/photos", tags=["照片管理（災損）"])

@router.post("/upload", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def upload_damage_photo(
    application_id: str = Form(...),
    photo_type: str = Form(...),
    description: str = Form(None),
    uploaded_by: str = Form(None),
    file: UploadFile = File(...)
):
    """
    上傳災損照片
    
    - **application_id**: 申請案件 ID
    - **photo_type**: 照片類型 (before_damage, after_damage, site_inspection)
    - **description**: 照片說明
    - **uploaded_by**: 上傳者 ID
    - **file**: 照片檔案
    """
    try:
        # 檢查申請案件是否存在
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        # 檢查檔案類型
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只接受圖片檔案"
            )
        
        # 讀取檔案內容
        file_content = await file.read()
        
        # 檢查檔案大小 (10MB)
        if len(file_content) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="檔案大小不能超過 10MB"
            )
        
        # 上傳到 Storage
        storage_result = storage_service.upload_damage_photo(
            application_id=application_id,
            file=file_content,
            filename=file.filename,
            photo_type=photo_type
        )
        
        # 建立資料庫記錄
        photo_data = {
            "application_id": application_id,
            "photo_type": photo_type,
            "storage_path": storage_result['storage_path'],
            "file_name": file.filename,
            "file_size": len(file_content),
            "mime_type": file.content_type,
            "description": description,
            "uploaded_by": uploaded_by
        }
        
        result = db_service.create_damage_photo(photo_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="建立照片記錄失敗"
            )
        
        # 加入簽名 URL
        result['signed_url'] = storage_result['signed_url']
        
        return APIResponse(
            success=True,
            message="照片上傳成功",
            data=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.post("/upload-multiple", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def upload_multiple_photos(
    application_id: str = Form(...),
    photo_type: str = Form(...),
    uploaded_by: str = Form(None),
    files: List[UploadFile] = File(...)
):
    """
    批次上傳多張照片
    
    - **application_id**: 申請案件 ID
    - **photo_type**: 照片類型
    - **uploaded_by**: 上傳者 ID
    - **files**: 照片檔案陣列
    """
    try:
        # 檢查申請案件是否存在
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        uploaded_photos = []
        errors = []
        
        for file in files:
            try:
                # 檢查檔案類型
                if not file.content_type.startswith('image/'):
                    errors.append(f"{file.filename}: 不是圖片檔案")
                    continue
                
                # 讀取檔案內容
                file_content = await file.read()
                
                # 檢查檔案大小
                if len(file_content) > 10 * 1024 * 1024:
                    errors.append(f"{file.filename}: 檔案大小超過 10MB")
                    continue
                
                # 上傳到 Storage
                storage_result = storage_service.upload_damage_photo(
                    application_id=application_id,
                    file=file_content,
                    filename=file.filename,
                    photo_type=photo_type
                )
                
                # 建立資料庫記錄
                photo_data = {
                    "application_id": application_id,
                    "photo_type": photo_type,
                    "storage_path": storage_result['storage_path'],
                    "file_name": file.filename,
                    "file_size": len(file_content),
                    "mime_type": file.content_type,
                    "uploaded_by": uploaded_by
                }
                
                result = db_service.create_damage_photo(photo_data)
                if result:
                    result['signed_url'] = storage_result['signed_url']
                    uploaded_photos.append(result)
                
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
        
        return APIResponse(
            success=len(uploaded_photos) > 0,
            message=f"成功上傳 {len(uploaded_photos)} 張照片",
            data={
                "uploaded": uploaded_photos,
                "errors": errors,
                "total_uploaded": len(uploaded_photos),
                "total_errors": len(errors)
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.get("/application/{application_id}", response_model=APIResponse)
async def get_photos_by_application(application_id: str):
    """
    取得申請案件的所有照片
    """
    try:
        # 檢查申請案件是否存在
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        # 取得照片列表
        photos = db_service.get_photos_by_application(application_id)
        
        # 為每張照片生成簽名 URL
        for photo in photos:
            signed_url = storage_service.get_damage_photo_url(
                photo['storage_path'],
                expires_in=3600  # 1 小時
            )
            photo['signed_url'] = signed_url
        
        return APIResponse(
            success=True,
            message=f"找到 {len(photos)} 張照片",
            data={"photos": photos, "total": len(photos)}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.delete("/{photo_id}", response_model=APIResponse)
async def delete_photo(photo_id: str):
    """
    刪除照片
    """
    try:
        # 取得照片資料
        photos = db_service.get_photos_by_application("")  # 這裡需要優化
        photo = next((p for p in photos if p['id'] == photo_id), None)
        
        if not photo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="照片不存在"
            )
        
        # 從 Storage 刪除檔案
        storage_service.delete_damage_photo(photo['storage_path'])
        
        # 從資料庫刪除記錄
        db_service.delete_photo(photo_id)
        
        return APIResponse(
            success=True,
            message="照片刪除成功",
            data={"photo_id": photo_id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

@router.post("/inspection/upload", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def upload_inspection_photo(
    application_id: str = Form(...),
    reviewer_id: str = Form(...),
    description: str = Form(None),
    file: UploadFile = File(...)
):
    """
    上傳現場勘查照片（審核員使用）
    
    - **application_id**: 申請案件 ID
    - **reviewer_id**: 審核員 ID
    - **description**: 照片說明
    - **file**: 照片檔案
    """
    try:
        # 檢查申請案件是否存在
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        # 檢查審核員權限
        reviewer = db_service.get_user_by_id(reviewer_id)
        if not reviewer or reviewer.get('role') not in ['reviewer', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限上傳現場勘查照片"
            )
        
        # 檢查檔案類型
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只接受圖片檔案"
            )
        
        # 讀取檔案內容
        file_content = await file.read()
        
        # 上傳到 Storage
        storage_result = storage_service.upload_inspection_photo(
            application_id=application_id,
            file=file_content,
            filename=file.filename,
            reviewer_id=reviewer_id
        )
        
        # 建立資料庫記錄
        photo_data = {
            "application_id": application_id,
            "photo_type": "site_inspection",
            "storage_path": storage_result['storage_path'],
            "file_name": file.filename,
            "file_size": len(file_content),
            "mime_type": file.content_type,
            "description": description,
            "uploaded_by": reviewer_id
        }
        
        result = db_service.create_damage_photo(photo_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="建立照片記錄失敗"
            )
        
        # 加入簽名 URL
        result['signed_url'] = storage_result['signed_url']
        
        return APIResponse(
            success=True,
            message="現場勘查照片上傳成功",
            data=result
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )

