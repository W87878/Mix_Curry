"""
文件上傳相關 API 路由
災民補助申請文件管理（如戶籍謄本、財產證明、收入證明等）
"""
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response
from typing import List, Optional
from app.models.models import APIResponse
from app.models.database import db_service
from app.services.storage import storage_service
import mimetypes
import io
import tempfile
import os
from urllib.parse import quote

router = APIRouter(prefix="/documents", tags=["文件管理（證明文件）"])

# 允許的文件類型
ALLOWED_MIME_TYPES = {
    'application/pdf': '.pdf',
    'image/jpeg': '.jpg',
    'image/jpg': '.jpg',
    'image/png': '.png',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/vnd.ms-excel': '.xls',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
}

@router.post("/upload", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    application_id: str = Form(..., description="申請案件 ID"),
    document_type: str = Form(..., description="文件類型: household_registration(戶籍謄本), income_proof(收入證明), property_proof(財產證明), other(其他)"),
    description: str = Form(None, description="文件說明"),
    uploaded_by: str = Form(..., description="上傳者 ID"),
    file: UploadFile = File(..., description="文件檔案")
):
    """
    上傳證明文件
    
    支援的文件類型：
    - PDF (.pdf)
    - 圖片 (.jpg, .png)
    - Word (.doc, .docx)
    - Excel (.xls, .xlsx)
    
    文件類型：
    - household_registration: 戶籍謄本
    - income_proof: 收入證明
    - property_proof: 財產證明
    - damage_assessment: 災損鑑定
    - other: 其他證明文件
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
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支援的檔案類型。允許的類型: PDF, JPG, PNG, DOC, DOCX, XLS, XLSX"
            )
        
        # 讀取檔案內容
        file_content = await file.read()
        
        # 檢查檔案大小 (20MB)
        max_size = 20 * 1024 * 1024  # 20MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"檔案大小不能超過 20MB（當前: {len(file_content) / 1024 / 1024:.2f}MB）"
            )
        
        # 上傳到 Storage
        storage_result = storage_service.upload_document(
            application_id=application_id,
            file=file_content,
            filename=file.filename,
            document_type=document_type
        )
        
        # 建立資料庫記錄
        document_data = {
            "application_id": application_id,
            "document_type": document_type,
            "storage_path": storage_result['storage_path'],
            "file_name": file.filename,
            "file_size": len(file_content),
            "mime_type": file.content_type,
            "description": description,
            "uploaded_by": uploaded_by
        }
        
        result = db_service.create_document(document_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="建立文件記錄失敗"
            )
        
        # 加入簽名 URL（有效期 7 天）
        result['signed_url'] = storage_result['signed_url']
        
        return APIResponse(
            success=True,
            message="文件上傳成功",
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
async def upload_multiple_documents(
    application_id: str = Form(...),
    document_type: str = Form(...),
    uploaded_by: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    批次上傳多個證明文件
    
    可以一次上傳多個檔案，例如多頁的戶籍謄本掃描檔
    """
    try:
        # 檢查申請案件是否存在
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在"
            )
        
        uploaded_documents = []
        errors = []
        
        for file in files:
            try:
                # 檢查檔案類型
                if file.content_type not in ALLOWED_MIME_TYPES:
                    errors.append(f"{file.filename}: 不支援的檔案類型")
                    continue
                
                # 讀取檔案
                file_content = await file.read()
                
                # 檢查檔案大小
                if len(file_content) > 20 * 1024 * 1024:
                    errors.append(f"{file.filename}: 檔案過大")
                    continue
                
                # 上傳到 Storage
                storage_result = storage_service.upload_document(
                    application_id=application_id,
                    file=file_content,
                    filename=file.filename,
                    document_type=document_type
                )
                
                # 建立資料庫記錄
                document_data = {
                    "application_id": application_id,
                    "document_type": document_type,
                    "storage_path": storage_result['storage_path'],
                    "file_name": file.filename,
                    "file_size": len(file_content),
                    "mime_type": file.content_type,
                    "uploaded_by": uploaded_by
                }
                
                result = db_service.create_document(document_data)
                if result:
                    result['signed_url'] = storage_result['signed_url']
                    uploaded_documents.append(result)
                
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
        
        return APIResponse(
            success=True,
            message=f"成功上傳 {len(uploaded_documents)} 個文件" + (f"，{len(errors)} 個失敗" if errors else ""),
            data={
                "uploaded": uploaded_documents,
                "errors": errors,
                "total": len(files),
                "success_count": len(uploaded_documents),
                "error_count": len(errors)
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
async def get_documents_by_application(
    application_id: str,
    document_type: Optional[str] = None
):
    """
    取得指定申請案件的所有文件
    
    - **application_id**: 申請案件 ID
    - **document_type**: 可選的文件類型篩選
    """
    try:
        documents = db_service.get_documents_by_application(
            application_id=application_id,
            document_type=document_type
        )
        
        # 為每個文件生成簽名 URL（有效期 24 小時）
        for doc in documents:
            if doc.get('storage_path'):
                doc['signed_url'] = storage_service.get_document_url(
                    storage_path=doc['storage_path'],
                    expires_in=86400  # 24 hours
                )
        
        return APIResponse(
            success=True,
            message=f"找到 {len(documents)} 個文件",
            data={"documents": documents, "total": len(documents)}
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )


@router.get("/{document_id}", response_model=APIResponse)
async def get_document(document_id: str):
    """
    取得指定文件的詳細資訊
    """
    try:
        document = db_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 生成簽名 URL
        if document.get('storage_path'):
            document['signed_url'] = storage_service.get_document_url(
                storage_path=document['storage_path'],
                expires_in=3600  # 1 hour
            )
        
        return APIResponse(
            success=True,
            message="取得文件成功",
            data=document
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )


@router.get("/{document_id}/preview")
async def preview_document(document_id: str):
    """
    預覽文件
    
    - 對於 DOCX 文件，會自動轉換為 PDF 進行預覽
    - 對於 PDF 和圖片文件，直接返回原檔案
    """
    try:
        # 取得文件資訊
        document = db_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 從 Storage 取得文件內容
        file_content = storage_service.download_document(document['storage_path'])
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件內容不存在"
            )
        
        mime_type = document.get('mime_type', 'application/octet-stream')
        file_name = document['file_name']
        
        # 如果是 DOCX 文件，轉換為 PDF
        if mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            try:
                # 嘗試使用 python-docx 和 reportlab 轉換
                from docx import Document
                from reportlab.lib.pagesizes import letter, A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import inch
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                
                # 建立臨時檔案來處理 DOCX
                with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_docx:
                    tmp_docx.write(file_content)
                    tmp_docx_path = tmp_docx.name
                
                # 讀取 DOCX
                doc = Document(tmp_docx_path)
                
                # 建立 PDF 輸出緩衝
                pdf_buffer = io.BytesIO()
                pdf_doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
                
                # 準備內容
                story = []
                styles = getSampleStyleSheet()
                
                # 添加文檔內容
                for para in doc.paragraphs:
                    if para.text.strip():
                        story.append(Paragraph(para.text, styles['Normal']))
                        story.append(Spacer(1, 0.2*inch))
                
                # 生成 PDF
                pdf_doc.build(story)
                pdf_content = pdf_buffer.getvalue()
                
                # 清理臨時檔案
                os.unlink(tmp_docx_path)
                
                # 返回轉換後的 PDF
                return Response(
                    content=pdf_content,
                    media_type='application/pdf',
                    headers={
                        'Content-Disposition': f'inline; filename="{file_name.replace(".docx", ".pdf")}"',
                        'Content-Length': str(len(pdf_content))
                    }
                )
            
            except ImportError:
                # 如果沒有安裝轉換庫，返回提示訊息
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail="DOCX 轉 PDF 功能需要安裝 python-docx 和 reportlab 套件。請直接下載檔案查看。"
                )
            except Exception as e:
                # 轉換失敗，返回原檔案
                print(f"DOCX 轉 PDF 失敗: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"文件轉換失敗，請直接下載檔案: {str(e)}"
                )
        
        # 其他文件類型直接返回
        # 使用 RFC 2231 編碼來處理中文文件名
        encoded_filename = quote(file_name)
        return Response(
            content=file_content,
            media_type=mime_type,
            headers={
                'Content-Disposition': f"inline; filename*=UTF-8''{encoded_filename}",
                'Content-Length': str(len(file_content))
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )


@router.get("/{document_id}/download")
async def download_document(document_id: str):
    """
    下載文件
    
    返回文件的二進制內容，可以直接下載
    """
    try:
        # 取得文件資訊
        document = db_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 從 Storage 取得文件內容
        file_content = storage_service.download_document(document['storage_path'])
        
        if not file_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件內容不存在"
            )
        
        # 使用 RFC 2231 編碼來處理中文文件名
        encoded_filename = quote(document["file_name"])
        
        # 返回串流回應
        return StreamingResponse(
            iter([file_content]),
            media_type=document.get('mime_type', 'application/octet-stream'),
            headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
                'Content-Length': str(len(file_content))
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )


@router.delete("/{document_id}", response_model=APIResponse)
async def delete_document(document_id: str):
    """
    刪除文件
    
    會同時刪除 Storage 中的檔案和資料庫記錄
    """
    try:
        # 取得文件資訊
        document = db_service.get_document_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在"
            )
        
        # 刪除 Storage 中的檔案
        storage_service.delete_document(document['storage_path'])
        
        # 刪除資料庫記錄
        db_service.delete_document(document_id)
        
        return APIResponse(
            success=True,
            message="文件刪除成功",
            data={"document_id": document_id}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"發生錯誤: {str(e)}"
        )
