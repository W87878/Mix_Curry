"""
Supabase Storage 檔案處理模組
"""
import io
import qrcode
from typing import BinaryIO, Optional
from datetime import datetime
from app.models.database import get_supabase_client
from app.settings import get_settings

settings = get_settings()
supabase = get_supabase_client()

class StorageService:
    """Storage 服務類別"""
    
    def __init__(self):
        self.client = get_supabase_client()
        self.damage_photos_bucket = settings.DAMAGE_PHOTOS_BUCKET
        self.qr_codes_bucket = settings.QR_CODES_BUCKET
        self.inspection_photos_bucket = settings.INSPECTION_PHOTOS_BUCKET
        self.documents_bucket = "application-documents"  # 新增：證明文件 bucket
    
    # ==========================================
    # 災損照片處理
    # ==========================================
    
    def upload_damage_photo(
        self, 
        application_id: str, 
        file: BinaryIO, 
        filename: str,
        photo_type: str = "before_damage"
    ) -> dict:
        """
        上傳災損照片
        
        Args:
            application_id: 申請案件 ID
            file: 檔案二進制資料
            filename: 檔案名稱
            photo_type: 照片類型 (before_damage, after_damage, site_inspection)
        
        Returns:
            包含 storage_path 和 public_url 的字典
        """
        # 生成唯一檔案路徑
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
        storage_path = f"{application_id}/{photo_type}_{timestamp}.{file_ext}"
        
        # 正確的 MIME type 對應
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        content_type = mime_types.get(file_ext, 'image/jpeg')
        
        # 上傳到 Supabase Storage
        result = self.client.storage.from_(self.damage_photos_bucket).upload(
            path=storage_path,
            file=file,
            file_options={"content-type": content_type}
        )
        
        # 取得檔案 URL (需要簽名的私有 URL)
        # 注意：damage-photos bucket 是私有的，需要生成帶有過期時間的 URL
        url = self.client.storage.from_(self.damage_photos_bucket).create_signed_url(
            path=storage_path,
            expires_in=3600 * 24 * 365  # 1年有效期
        )
        
        return {
            "storage_path": storage_path,
            "signed_url": url['signedURL'] if url else None,
            "bucket": self.damage_photos_bucket
        }
    
    def get_damage_photo_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        取得災損照片的簽名 URL
        
        Args:
            storage_path: Storage 路徑
            expires_in: URL 有效期限（秒），預設 1 小時
        
        Returns:
            簽名的 URL
        """
        result = self.client.storage.from_(self.damage_photos_bucket).create_signed_url(
            path=storage_path,
            expires_in=expires_in
        )
        return result['signedURL'] if result else None
    
    def delete_damage_photo(self, storage_path: str) -> bool:
        """
        刪除災損照片
        
        Args:
            storage_path: Storage 路徑
        
        Returns:
            是否成功刪除
        """
        try:
            self.client.storage.from_(self.damage_photos_bucket).remove([storage_path])
            return True
        except Exception as e:
            print(f"刪除照片失敗: {e}")
            return False
    
    # ==========================================
    # QR Code 生成與處理
    # ==========================================
    
    def generate_qr_code(
        self, 
        certificate_no: str, 
        qr_data: dict
    ) -> dict:
        """
        生成 QR Code 並上傳到 Storage
        
        Args:
            certificate_no: 憑證編號
            qr_data: QR Code 包含的資料（dict，會轉成 JSON 字串）
        
        Returns:
            包含 storage_path 和 public_url 的字典
        """
        import json
        
        # 生成 QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        
        # 將資料轉成 JSON 字串
        qr_content = json.dumps(qr_data, ensure_ascii=False)
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        # 建立圖片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 轉換成二進制
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # 上傳到 Storage
        storage_path = f"certificates/{certificate_no}.png"
        
        result = self.client.storage.from_(self.qr_codes_bucket).upload(
            path=storage_path,
            file=img_buffer.getvalue(),
            file_options={"content-type": "image/png"}
        )
        
        # 取得公開 URL (qr-codes bucket 是公開的)
        public_url = self.client.storage.from_(self.qr_codes_bucket).get_public_url(storage_path)
        
        return {
            "storage_path": storage_path,
            "public_url": public_url,
            "bucket": self.qr_codes_bucket,
            "qr_data": qr_content
        }
    
    def get_qr_code_url(self, storage_path: str) -> str:
        """
        取得 QR Code 的公開 URL
        
        Args:
            storage_path: Storage 路徑
        
        Returns:
            公開 URL
        """
        return self.client.storage.from_(self.qr_codes_bucket).get_public_url(storage_path)
    
    # ==========================================
    # 現場勘查照片處理
    # ==========================================
    
    def upload_inspection_photo(
        self, 
        application_id: str, 
        file: BinaryIO, 
        filename: str,
        reviewer_id: str
    ) -> dict:
        """
        上傳現場勘查照片
        
        Args:
            application_id: 申請案件 ID
            file: 檔案二進制資料
            filename: 檔案名稱
            reviewer_id: 審核員 ID
        
        Returns:
            包含 storage_path 和 signed_url 的字典
        """
        # 生成唯一檔案路徑
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
        storage_path = f"{application_id}/inspection_{timestamp}_{reviewer_id[:8]}.{file_ext}"
        
        # 正確的 MIME type 對應
        mime_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        content_type = mime_types.get(file_ext, 'image/jpeg')
        
        # 上傳到 Supabase Storage
        result = self.client.storage.from_(self.inspection_photos_bucket).upload(
            path=storage_path,
            file=file,
            file_options={"content-type": content_type}
        )
        
        # 取得簽名 URL
        url = self.client.storage.from_(self.inspection_photos_bucket).create_signed_url(
            path=storage_path,
            expires_in=3600 * 24 * 365  # 1年有效期
        )
        
        return {
            "storage_path": storage_path,
            "signed_url": url['signedURL'] if url else None,
            "bucket": self.inspection_photos_bucket
        }
    
    def get_inspection_photo_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        取得現場勘查照片的簽名 URL
        
        Args:
            storage_path: Storage 路徑
            expires_in: URL 有效期限（秒），預設 1 小時
        
        Returns:
            簽名的 URL
        """
        result = self.client.storage.from_(self.inspection_photos_bucket).create_signed_url(
            path=storage_path,
            expires_in=expires_in
        )
        return result['signedURL'] if result else None
    
    # ==========================================
    # 證明文件處理
    # ==========================================
    
    def upload_document(
        self, 
        application_id: str, 
        file: BinaryIO, 
        filename: str,
        document_type: str = "other"
    ) -> dict:
        """
        上傳證明文件（戶籍謄本、財產證明等）
        
        Args:
            application_id: 申請案件 ID
            file: 檔案二進制資料
            filename: 檔案名稱
            document_type: 文件類型
        
        Returns:
            包含 storage_path 和 signed_url 的字典
        """
        # 生成唯一檔案路徑
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_ext = filename.split('.')[-1].lower() if '.' in filename else 'pdf'
        storage_path = f"{application_id}/{document_type}_{timestamp}.{file_ext}"
        
        # MIME type 對應
        mime_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
        }
        content_type = mime_types.get(file_ext, 'application/octet-stream')
        
        # 上傳到 Supabase Storage
        result = self.client.storage.from_(self.documents_bucket).upload(
            path=storage_path,
            file=file,
            file_options={"content-type": content_type}
        )
        
        # 生成簽名 URL（7 天有效期）
        url = self.client.storage.from_(self.documents_bucket).create_signed_url(
            path=storage_path,
            expires_in=3600 * 24 * 7  # 7 days
        )
        
        return {
            "storage_path": storage_path,
            "signed_url": url['signedURL'] if url else None,
            "bucket": self.documents_bucket
        }
    
    def get_document_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        取得證明文件的簽名 URL
        
        Args:
            storage_path: Storage 路徑
            expires_in: URL 有效期限（秒），預設 1 小時
        
        Returns:
            簽名的 URL
        """
        result = self.client.storage.from_(self.documents_bucket).create_signed_url(
            path=storage_path,
            expires_in=expires_in
        )
        return result['signedURL'] if result else None
    
    def download_document(self, storage_path: str) -> bytes:
        """
        下載證明文件
        
        Args:
            storage_path: Storage 路徑
        
        Returns:
            文件的二進制內容
        """
        try:
            result = self.client.storage.from_(self.documents_bucket).download(storage_path)
            return result
        except Exception as e:
            print(f"下載文件失敗: {e}")
            return None
    
    def delete_document(self, storage_path: str) -> bool:
        """
        刪除證明文件
        
        Args:
            storage_path: Storage 路徑
        
        Returns:
            是否成功刪除
        """
        try:
            self.client.storage.from_(self.documents_bucket).remove([storage_path])
            return True
        except Exception as e:
            print(f"刪除文件失敗: {e}")
            return False
    
    # ==========================================
    # 通用檔案操作
    # ==========================================
    
    def list_files(self, bucket_name: str, folder_path: str = "") -> list:
        """
        列出指定資料夾的所有檔案
        
        Args:
            bucket_name: Bucket 名稱
            folder_path: 資料夾路徑
        
        Returns:
            檔案列表
        """
        result = self.client.storage.from_(bucket_name).list(folder_path)
        return result
    
    def get_file_info(self, bucket_name: str, file_path: str) -> dict:
        """
        取得檔案資訊
        
        Args:
            bucket_name: Bucket 名稱
            file_path: 檔案路徑
        
        Returns:
            檔案資訊
        """
        files = self.client.storage.from_(bucket_name).list(file_path)
        return files[0] if files else None

# 全域 Storage 服務實例
storage_service = StorageService()

