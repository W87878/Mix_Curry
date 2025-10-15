"""
Pydantic 資料模型
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal

# ==========================================
# 使用者相關模型
# ==========================================

class UserRole:
    APPLICANT = "applicant"
    REVIEWER = "reviewer"
    ADMIN = "admin"

class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str
    id_number: str  # 身分證字號
    role: str = UserRole.APPLICANT

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ==========================================
# 申請案件相關模型
# ==========================================

class ApplicationStatus:
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    SITE_INSPECTION = "site_inspection"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"

class DisasterType:
    FLOOD = "flood"  # 水災
    TYPHOON = "typhoon"  # 颱風
    EARTHQUAKE = "earthquake"  # 地震
    FIRE = "fire"  # 火災
    OTHER = "other"  # 其他

class SubsidyType:
    HOUSING = "housing"  # 房屋補助
    EQUIPMENT = "equipment"  # 設備補助
    LIVING = "living"  # 生活補助
    BUSINESS = "business"  # 營業補助

class ApplicationBase(BaseModel):
    # 申請人資料
    applicant_name: str = Field(..., description="申請人姓名")
    id_number: str = Field(..., description="身分證字號")
    phone: str = Field(..., description="聯絡電話")
    address: str = Field(..., description="聯絡地址")
    
    # 災損資料
    disaster_date: date = Field(..., description="災害發生日期")
    disaster_type: str = Field(..., description="災害類型")
    damage_description: str = Field(..., description="災損描述")
    damage_location: str = Field(..., description="災損地點")
    estimated_loss: Optional[Decimal] = Field(None, description="預估損失金額")
    
    # 申請資料
    subsidy_type: str = Field(..., description="補助類型")
    requested_amount: Optional[Decimal] = Field(None, description="申請金額")

class ApplicationCreate(ApplicationBase):
    applicant_id: str

class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    review_notes: Optional[str] = None
    approved_amount: Optional[Decimal] = None

class ApplicationResponse(ApplicationBase):
    id: str
    case_no: str
    applicant_id: str
    status: str
    review_notes: Optional[str] = None
    approved_amount: Optional[Decimal] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ==========================================
# 照片相關模型
# ==========================================

class PhotoType:
    BEFORE_DAMAGE = "before_damage"
    AFTER_DAMAGE = "after_damage"
    SITE_INSPECTION = "site_inspection"

class DamagePhotoBase(BaseModel):
    photo_type: str
    description: Optional[str] = None

class DamagePhotoCreate(DamagePhotoBase):
    application_id: str
    storage_path: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_by: Optional[str] = None

class DamagePhotoResponse(DamagePhotoBase):
    id: str
    application_id: str
    storage_path: str
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    signed_url: Optional[str] = None  # 前端顯示用的簽名 URL
    uploaded_by: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==========================================
# 審核相關模型
# ==========================================

class ReviewAction:
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    SITE_INSPECTION = "site_inspection"
    APPROVED = "approved"
    REJECTED = "rejected"

class ReviewRecordBase(BaseModel):
    action: str
    comments: Optional[str] = None
    decision_reason: Optional[str] = None

class ReviewRecordCreate(ReviewRecordBase):
    application_id: str
    reviewer_id: str
    reviewer_name: str
    previous_status: Optional[str] = None
    new_status: str
    inspection_date: Optional[datetime] = None
    inspection_notes: Optional[str] = None

class ReviewRecordResponse(ReviewRecordBase):
    id: str
    application_id: str
    reviewer_id: str
    reviewer_name: str
    previous_status: Optional[str] = None
    new_status: str
    inspection_date: Optional[datetime] = None
    inspection_notes: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==========================================
# 數位憑證相關模型
# ==========================================

class DisbursementMethod:
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CASH = "cash"

class CertificateBase(BaseModel):
    certificate_no: str
    issued_amount: Decimal

class CertificateCreate(CertificateBase):
    application_id: str
    qr_code_data: str
    qr_code_image_path: str
    issued_by: str
    expires_at: Optional[datetime] = None

class CertificateResponse(CertificateBase):
    id: str
    application_id: str
    qr_code_data: str
    qr_code_image_path: str
    qr_code_url: Optional[str] = None  # QR Code 圖片 URL
    issued_by: str
    issued_at: datetime
    is_verified: bool
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    is_disbursed: bool
    disbursed_at: Optional[datetime] = None
    disbursement_method: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class CertificateVerifyRequest(BaseModel):
    certificate_no: str
    verified_by: str

class CertificateDisburseRequest(BaseModel):
    certificate_id: str
    disbursement_method: str

# ==========================================
# 補助項目相關模型
# ==========================================

class ItemCategory:
    HOUSING = "housing"
    FURNITURE = "furniture"
    APPLIANCES = "appliances"
    LIVING_EXPENSES = "living_expenses"

class SubsidyItemBase(BaseModel):
    item_category: str
    item_name: str
    item_description: Optional[str] = None
    quantity: int = 1
    unit_price: Optional[Decimal] = None
    total_price: Decimal

class SubsidyItemCreate(SubsidyItemBase):
    application_id: str

class SubsidyItemUpdate(BaseModel):
    approved: bool
    approved_amount: Decimal

class SubsidyItemResponse(SubsidyItemBase):
    id: str
    application_id: str
    approved: bool
    approved_amount: Optional[Decimal] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ==========================================
# API 回應模型
# ==========================================

class APIResponse(BaseModel):
    """標準 API 回應格式"""
    success: bool
    message: str
    data: Optional[dict] = None

class PaginatedResponse(BaseModel):
    """分頁回應格式"""
    success: bool
    message: str
    data: List[dict]
    total: int
    page: int
    page_size: int
    total_pages: int

# ==========================================
# 檔案上傳相關模型
# ==========================================

class FileUploadResponse(BaseModel):
    """檔案上傳回應"""
    success: bool
    message: str
    file_id: Optional[str] = None
    storage_path: Optional[str] = None
    file_url: Optional[str] = None

# ==========================================
# 統計資料模型
# ==========================================

class DashboardStats(BaseModel):
    """儀表板統計資料"""
    total_applications: int
    pending_applications: int
    under_review_applications: int
    approved_applications: int
    rejected_applications: int
    total_approved_amount: Decimal
    total_disbursed_amount: Decimal

class ApplicationDetailResponse(BaseModel):
    """完整申請案件詳情（包含相關資料）"""
    application: ApplicationResponse
    photos: List[DamagePhotoResponse] = []
    review_records: List[ReviewRecordResponse] = []
    subsidy_items: List[SubsidyItemResponse] = []
    certificate: Optional[CertificateResponse] = None

