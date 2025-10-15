"""
Supabase 資料庫連接模組
使用 Supabase Client 作為資料庫 ORM
"""
from supabase import create_client, Client
from app.settings import get_settings
from typing import Optional

settings = get_settings()

# Supabase 客戶端（延遲初始化）
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """取得 Supabase 客戶端（單例模式）"""
    global _supabase_client
    if _supabase_client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE:
            raise ValueError("請設定 SUPABASE_URL 和 SUPABASE_SERVICE_ROLE 環境變數")
        _supabase_client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_ROLE
        )
    return _supabase_client

# 向後相容
supabase = get_supabase_client

def serialize_data(data: dict) -> dict:
    """
    序列化資料，將 date, datetime, Decimal 等特殊類型轉換為 JSON 可序列化的格式
    """
    from datetime import date, datetime
    from decimal import Decimal
    
    serialized = {}
    for key, value in data.items():
        if isinstance(value, (date, datetime)):
            serialized[key] = value.isoformat()
        elif isinstance(value, Decimal):
            serialized[key] = float(value)
        elif value is None:
            serialized[key] = None
        else:
            serialized[key] = value
    return serialized

class DatabaseService:
    """資料庫服務類別"""
    
    def __init__(self):
        self._client = None
    
    @property
    def client(self) -> Client:
        """延遲初始化客戶端"""
        if self._client is None:
            self._client = get_supabase_client()
        return self._client
    
    # ==========================================
    # 案件相關操作
    # ==========================================
    
    def create_application(self, application_data: dict):
        """建立新申請案件"""
        # 生成案件編號
        case_no_result = self.client.rpc('generate_case_no').execute()
        application_data['case_no'] = case_no_result.data
        
        # 序列化資料
        serialized_data = serialize_data(application_data)
        
        result = self.client.table('applications').insert(serialized_data).execute()
        return result.data[0] if result.data else None
    
    def get_application_by_id(self, application_id: str):
        """根據 ID 取得申請案件"""
        result = self.client.table('applications') \
            .select('*') \
            .eq('id', application_id) \
            .single() \
            .execute()
        return result.data
    
    def get_application_by_case_no(self, case_no: str):
        """根據案件編號取得申請案件"""
        result = self.client.table('applications') \
            .select('*') \
            .eq('case_no', case_no) \
            .single() \
            .execute()
        return result.data
    
    def get_applications_by_applicant(self, applicant_id: str):
        """取得特定申請人的所有案件"""
        result = self.client.table('applications') \
            .select('*') \
            .eq('applicant_id', applicant_id) \
            .order('submitted_at', desc=True) \
            .execute()
        return result.data
    
    def get_applications_by_status(self, status: str, limit: int = 50):
        """根據狀態取得申請案件"""
        result = self.client.table('applications') \
            .select('*') \
            .eq('status', status) \
            .order('submitted_at', desc=True) \
            .limit(limit) \
            .execute()
        return result.data
    
    def update_application_status(self, application_id: str, status: str, **kwargs):
        """更新申請案件狀態"""
        update_data = {'status': status, **kwargs}
        result = self.client.table('applications') \
            .update(update_data) \
            .eq('id', application_id) \
            .execute()
        return result.data[0] if result.data else None
    
    # ==========================================
    # 使用者相關操作
    # ==========================================
    
    def create_user(self, user_data: dict):
        """建立新使用者"""
        serialized_data = serialize_data(user_data)
        result = self.client.table('users').insert(serialized_data).execute()
        return result.data[0] if result.data else None
    
    def get_user_by_id(self, user_id: str):
        """根據 ID 取得使用者"""
        result = self.client.table('users') \
            .select('*') \
            .eq('id', user_id) \
            .single() \
            .execute()
        return result.data
    
    def get_user_by_email(self, email: str):
        """根據 email 取得使用者"""
        result = self.client.table('users') \
            .select('*') \
            .eq('email', email) \
            .single() \
            .execute()
        return result.data
    
    def get_user_by_id_number(self, id_number: str):
        """根據身分證字號取得使用者"""
        result = self.client.table('users') \
            .select('*') \
            .eq('id_number', id_number) \
            .single() \
            .execute()
        return result.data
    
    # ==========================================
    # 照片相關操作
    # ==========================================
    
    def create_damage_photo(self, photo_data: dict):
        """建立災損照片記錄"""
        serialized_data = serialize_data(photo_data)
        result = self.client.table('damage_photos').insert(serialized_data).execute()
        return result.data[0] if result.data else None
    
    def get_photos_by_application(self, application_id: str):
        """取得申請案件的所有照片"""
        result = self.client.table('damage_photos') \
            .select('*') \
            .eq('application_id', application_id) \
            .order('created_at', desc=False) \
            .execute()
        return result.data
    
    def delete_photo(self, photo_id: str):
        """刪除照片記錄"""
        result = self.client.table('damage_photos') \
            .delete() \
            .eq('id', photo_id) \
            .execute()
        return result.data
    
    # ==========================================
    # 審核記錄相關操作
    # ==========================================
    
    def create_review_record(self, review_data: dict):
        """建立審核記錄"""
        serialized_data = serialize_data(review_data)
        result = self.client.table('review_records').insert(serialized_data).execute()
        return result.data[0] if result.data else None
    
    def get_review_records_by_application(self, application_id: str):
        """取得申請案件的所有審核記錄"""
        result = self.client.table('review_records') \
            .select('*') \
            .eq('application_id', application_id) \
            .order('created_at', desc=False) \
            .execute()
        return result.data
    
    # ==========================================
    # 數位憑證相關操作
    # ==========================================
    
    def create_certificate(self, certificate_data: dict):
        """建立數位憑證"""
        serialized_data = serialize_data(certificate_data)
        result = self.client.table('digital_certificates').insert(serialized_data).execute()
        return result.data[0] if result.data else None
    
    def get_certificate_by_no(self, certificate_no: str):
        """根據憑證編號取得憑證"""
        result = self.client.table('digital_certificates') \
            .select('*') \
            .eq('certificate_no', certificate_no) \
            .single() \
            .execute()
        return result.data
    
    def get_certificate_by_application(self, application_id: str):
        """取得申請案件的憑證"""
        result = self.client.table('digital_certificates') \
            .select('*') \
            .eq('application_id', application_id) \
            .single() \
            .execute()
        return result.data
    
    def verify_certificate(self, certificate_id: str, verified_by: str):
        """驗證憑證"""
        from datetime import datetime
        result = self.client.table('digital_certificates') \
            .update({
                'is_verified': True,
                'verified_at': datetime.now().isoformat(),
                'verified_by': verified_by
            }) \
            .eq('id', certificate_id) \
            .execute()
        return result.data[0] if result.data else None
    
    def disburse_certificate(self, certificate_id: str, method: str):
        """發放補助"""
        from datetime import datetime
        result = self.client.table('digital_certificates') \
            .update({
                'is_disbursed': True,
                'disbursed_at': datetime.now().isoformat(),
                'disbursement_method': method
            }) \
            .eq('id', certificate_id) \
            .execute()
        return result.data[0] if result.data else None
    
    # ==========================================
    # 補助項目相關操作
    # ==========================================
    
    def create_subsidy_item(self, item_data: dict):
        """建立補助項目"""
        serialized_data = serialize_data(item_data)
        result = self.client.table('subsidy_items').insert(serialized_data).execute()
        return result.data[0] if result.data else None
    
    def get_subsidy_items_by_application(self, application_id: str):
        """取得申請案件的所有補助項目"""
        result = self.client.table('subsidy_items') \
            .select('*') \
            .eq('application_id', application_id) \
            .execute()
        return result.data
    
    def update_subsidy_item_approval(self, item_id: str, approved: bool, approved_amount: float):
        """更新補助項目核准狀態"""
        result = self.client.table('subsidy_items') \
            .update({
                'approved': approved,
                'approved_amount': approved_amount
            }) \
            .eq('id', item_id) \
            .execute()
        return result.data[0] if result.data else None

# 全域資料庫服務實例
db_service = DatabaseService()

