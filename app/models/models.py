"""
Pydantic 資料模型
定義 API 的請求和回應格式
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from decimal import Decimal


# ==========================================
# 通用回應模型
# ==========================================

class APIResponse(BaseModel):
    """統一的 API 回應格式"""
    success: bool
    message: str
    data: Optional[Any] = None


# ==========================================
# 使用者相關模型
# ==========================================

class UserBase(BaseModel):
    """使用者基礎模型"""
    email: EmailStr
    full_name: str
    phone: str
    id_number: str
    role: str = Field(default="applicant", description="角色: applicant, reviewer, admin")


class UserCreate(UserBase):
    """建立使用者請求"""
    password: Optional[str] = Field(None, description="密碼（選填，支援數位憑證登入）")
    district_id: Optional[str] = Field(None, description="區域 ID（里長專用）")


class UserResponse(UserBase):
    """使用者回應"""
    id: str
    is_active: bool
    is_verified: bool
    district_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# 申請案件相關模型
# ==========================================

class DisasterType:
    """災害類型常數"""
    FLOOD = "flood"  # 水災
    TYPHOON = "typhoon"  # 颱風
    EARTHQUAKE = "earthquake"  # 地震
    FIRE = "fire"  # 火災
    OTHER = "other"  # 其他


class SubsidyType:
    """補助類型常數"""
    HOUSING = "housing"  # 房屋補助
    EQUIPMENT = "equipment"  # 設備補助
    LIVING = "living"  # 生活補助
    BUSINESS = "business"  # 營業補助


class ApplicationBase(BaseModel):
    """申請案件基礎模型"""
    # 申請人資料
    applicant_name: str = Field(..., description="申請人姓名")
    id_number: str = Field(..., description="身分證字號")
    phone: str = Field(..., description="聯絡電話")
    address: Optional[str] = Field(None, description="聯絡地址（選填）")
    
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
    """建立申請案件請求"""
    applicant_id: str


class ApplicationUpdate(BaseModel):
    """更新申請案件請求"""
    status: Optional[str] = None
    review_notes: Optional[str] = None
    approved_amount: Optional[Decimal] = None


class ApplicationResponse(ApplicationBase):
    """申請案件回應"""
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


class ApplicationDetailResponse(BaseModel):
    """申請案件詳細資訊回應"""
    application: Dict
    photos: List[Dict] = []
    review_records: List[Dict] = []
    subsidy_items: List[Dict] = []
    certificate: Optional[Dict] = None


# ==========================================
# 審核相關模型
# ==========================================

class ReviewBase(BaseModel):
    """審核基礎模型"""
    application_id: str
    reviewer_id: str
    review_status: str = Field(..., description="審核狀態: approved, rejected, under_review")
    review_notes: Optional[str] = Field(None, description="審核備註")
    approved_amount: Optional[Decimal] = Field(None, description="核准金額")
    rejection_reason: Optional[str] = Field(None, description="駁回原因")


class ReviewCreate(ReviewBase):
    """建立審核記錄請求"""
    pass


class ReviewResponse(ReviewBase):
    """審核記錄回應"""
    id: str
    reviewed_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# 審核相關模型（擴展）
# ==========================================

class ReviewRecordCreate(ReviewBase):
    """建立審核記錄請求（別名）"""
    pass


class ReviewRecordResponse(ReviewResponse):
    """審核記錄回應（別名）"""
    pass


# ==========================================
# 憑證相關模型
# ==========================================

class CertificateBase(BaseModel):
    """憑證基礎模型"""
    application_id: str
    certificate_type: str = Field(..., description="憑證類型: qr_code, digital_id")
    qr_code_data: Optional[str] = Field(None, description="QR Code 資料")
    verification_code: Optional[str] = Field(None, description="驗證碼")


class CertificateCreate(CertificateBase):
    """建立憑證請求"""
    pass


class CertificateResponse(CertificateBase):
    """憑證回應"""
    id: str
    is_used: bool
    issued_at: datetime
    used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# 憑證相關模型（擴展）
# ==========================================

class CertificateVerifyRequest(BaseModel):
    """憑證驗證請求"""
    certificate_id: str
    verification_code: Optional[str] = None
    qr_code_data: Optional[str] = None


class CertificateDisburseRequest(BaseModel):
    """憑證發放補助請求"""
    certificate_id: str
    disbursement_method: str = Field(..., description="發放方式: bank_transfer, cash, check")
    bank_account: Optional[str] = Field(None, description="銀行帳號")
    bank_code: Optional[str] = Field(None, description="銀行代碼")
    notes: Optional[str] = None


# ==========================================
# 照片相關模型
# ==========================================

class PhotoBase(BaseModel):
    """照片基礎模型"""
    application_id: str
    photo_type: str = Field(..., description="照片類型: damage_before, damage_after, inspection")
    file_path: str
    description: Optional[str] = None


class PhotoCreate(PhotoBase):
    """建立照片記錄請求"""
    pass


class PhotoResponse(PhotoBase):
    """照片記錄回應"""
    id: str
    uploaded_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# 照片相關模型（擴展）
# ==========================================

class DamagePhotoCreate(PhotoBase):
    """建立災損照片記錄請求（別名）"""
    pass


class DamagePhotoResponse(PhotoResponse):
    """災損照片記錄回應（別名）"""
    pass


class FileUploadResponse(BaseModel):
    """檔案上傳回應"""
    file_path: str
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    uploaded_at: datetime


# ==========================================
# 通知相關模型
# ==========================================

class NotificationBase(BaseModel):
    """通知基礎模型"""
    user_id: str
    application_id: Optional[str] = None
    notification_type: str = Field(..., description="通知類型: approval, rejection, reminder")
    title: str
    content: str
    email: Optional[str] = None


class NotificationCreate(NotificationBase):
    """建立通知請求"""
    pass


class NotificationResponse(NotificationBase):
    """通知回應"""
    id: str
    is_read: bool
    sent_via_email: bool
    email_sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# 區域相關模型
# ==========================================

class DistrictBase(BaseModel):
    """區域基礎模型"""
    name: str = Field(..., description="區域名稱")
    city: str = Field(..., description="城市")
    code: Optional[str] = Field(None, description="區域代碼")


class DistrictCreate(DistrictBase):
    """建立區域請求"""
    pass


class DistrictResponse(DistrictBase):
    """區域回應"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# 地圖相關模型
# ==========================================

class RouteOptimizationRequest(BaseModel):
    """路線規劃請求"""
    start_location: str = Field(..., description="起點地址")
    destinations: List[str] = Field(..., description="目的地地址列表")


class RouteOptimizationResponse(BaseModel):
    """路線規劃回應"""
    routes: List[Dict]
    total_distance: str
    total_duration: str


class GeocodingRequest(BaseModel):
    """地理編碼請求"""
    address: str = Field(..., description="地址")


class GeocodingResponse(BaseModel):
    """地理編碼回應"""
    lat: float
    lng: float
    formatted_address: str

