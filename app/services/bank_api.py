"""
銀行 API 整合服務模組
實作帳戶驗證、重複申請檢查、交易記錄等功能
"""
from typing import Optional, Dict, List, Any
from datetime import datetime
import httpx
from app.models.database import db_service
from app.settings import get_settings

settings = get_settings()


class BankAPIService:
    """銀行 API 整合服務"""
    
    def __init__(self):
        # TODO: 從環境變數或系統設定讀取
        self.bank_api_url = getattr(settings, 'BANK_API_URL', 'https://bank-api.example.com')
        self.bank_api_key = getattr(settings, 'BANK_API_KEY', 'your-bank-api-key')
        self.timeout = 30.0  # 30 秒逾時
    
    async def verify_account(
        self,
        bank_code: str,
        account_number: str,
        account_holder_name: str,
        id_number: str,
        application_id: str
    ) -> Dict[str, Any]:
        """
        驗證銀行帳戶
        
        Args:
            bank_code: 銀行代碼
            account_number: 帳號
            account_holder_name: 戶名
            id_number: 身分證字號
            application_id: 申請案件 ID
            
        Returns:
            驗證結果
        """
        verification_result = {
            "is_valid": False,
            "message": "",
            "error_code": None
        }
        
        api_request = {
            "bank_code": bank_code,
            "account_number": account_number,
            "account_holder_name": account_holder_name,
            "id_number": id_number
        }
        
        try:
            # 呼叫銀行 API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                start_time = datetime.now()
                
                # TODO: 替換為實際的銀行 API 端點
                response = await client.post(
                    f"{self.bank_api_url}/api/v1/account/verify",
                    json=api_request,
                    headers={
                        "Authorization": f"Bearer {self.bank_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                end_time = datetime.now()
                response_time_ms = int((end_time - start_time).total_seconds() * 1000)
                
                api_response = response.json()
                
                # 解析 API 回應
                if response.status_code == 200 and api_response.get('status') == 'success':
                    verification_result['is_valid'] = True
                    verification_result['message'] = "帳戶驗證成功"
                else:
                    verification_result['is_valid'] = False
                    verification_result['message'] = api_response.get('message', '帳戶驗證失敗')
                    verification_result['error_code'] = api_response.get('error_code')
                
                # 記錄驗證結果到資料庫
                await self._record_verification(
                    application_id=application_id,
                    verification_type='account_validation',
                    bank_code=bank_code,
                    account_number=account_number,
                    account_holder_name=account_holder_name,
                    is_valid=verification_result['is_valid'],
                    verification_message=verification_result['message'],
                    error_code=verification_result['error_code'],
                    api_endpoint=f"{self.bank_api_url}/api/v1/account/verify",
                    api_request=api_request,
                    api_response=api_response,
                    response_time_ms=response_time_ms
                )
                
        except httpx.TimeoutException:
            verification_result['message'] = "銀行 API 連線逾時"
            verification_result['error_code'] = "TIMEOUT"
        except httpx.HTTPError as e:
            verification_result['message'] = f"銀行 API 連線錯誤: {str(e)}"
            verification_result['error_code'] = "CONNECTION_ERROR"
        except Exception as e:
            verification_result['message'] = f"驗證過程發生錯誤: {str(e)}"
            verification_result['error_code'] = "UNKNOWN_ERROR"
        
        # 如果 API 失敗，使用本地模擬驗證（開發模式）
        if not verification_result['is_valid'] and settings.DEBUG:
            print(f"⚠️ 銀行 API 驗證失敗，使用模擬模式")
            verification_result = await self._mock_verify_account(
                bank_code, account_number, account_holder_name, id_number, application_id
            )
        
        return verification_result
    
    async def _mock_verify_account(
        self,
        bank_code: str,
        account_number: str,
        account_holder_name: str,
        id_number: str,
        application_id: str
    ) -> Dict[str, Any]:
        """模擬帳戶驗證（開發模式）"""
        # 簡單的驗證規則
        is_valid = (
            len(account_number) >= 10 and
            len(account_holder_name) >= 2 and
            len(id_number) == 10
        )
        
        result = {
            "is_valid": is_valid,
            "message": "帳戶驗證成功（模擬）" if is_valid else "帳戶資料不完整",
            "error_code": None if is_valid else "INVALID_DATA"
        }
        
        # 記錄模擬驗證
        await self._record_verification(
            application_id=application_id,
            verification_type='account_validation',
            bank_code=bank_code,
            account_number=account_number,
            account_holder_name=account_holder_name,
            is_valid=result['is_valid'],
            verification_message=result['message'] + " (模擬模式)",
            error_code=result['error_code'],
            api_endpoint="mock://bank-api/verify",
            api_request={"mode": "mock"},
            api_response=result,
            response_time_ms=10
        )
        
        return result
    
    async def check_duplicate_application(
        self,
        id_number: str,
        disaster_date: str,
        application_id: str
    ) -> Dict[str, Any]:
        """
        檢查重複申請
        
        Args:
            id_number: 身分證字號
            disaster_date: 災害日期
            application_id: 申請案件 ID
            
        Returns:
            檢查結果
        """
        check_result = {
            "has_duplicate": False,
            "duplicate_details": [],
            "message": ""
        }
        
        try:
            # 1. 檢查本地資料庫
            local_duplicates = self._check_local_duplicates(id_number, disaster_date)
            
            # 2. 呼叫銀行 API 跨系統查詢
            bank_duplicates = await self._check_bank_duplicates(id_number, disaster_date)
            
            # 合併結果
            all_duplicates = local_duplicates + bank_duplicates
            
            if all_duplicates:
                check_result['has_duplicate'] = True
                check_result['duplicate_details'] = all_duplicates
                check_result['message'] = f"發現 {len(all_duplicates)} 筆重複申請記錄"
            else:
                check_result['message'] = "未發現重複申請"
            
            # 記錄檢查結果
            await self._record_verification(
                application_id=application_id,
                verification_type='duplicate_check',
                is_valid=not check_result['has_duplicate'],
                verification_message=check_result['message'],
                has_duplicate=check_result['has_duplicate'],
                duplicate_details=check_result['duplicate_details'],
                api_endpoint=f"{self.bank_api_url}/api/v1/subsidy/check-duplicate",
                api_request={"id_number": id_number, "disaster_date": disaster_date},
                api_response=check_result,
                response_time_ms=100
            )
            
        except Exception as e:
            check_result['message'] = f"檢查過程發生錯誤: {str(e)}"
            print(f"Duplicate check error: {e}")
        
        return check_result
    
    def _check_local_duplicates(self, id_number: str, disaster_date: str) -> List[Dict]:
        """檢查本地資料庫的重複申請"""
        try:
            result = db_service.client.table('applications') \
                .select('id, case_no, status, approved_amount, submitted_at') \
                .eq('id_number', id_number) \
                .eq('disaster_date', disaster_date) \
                .in_('status', ['pending', 'under_review', 'approved', 'completed']) \
                .execute()
            
            duplicates = []
            for app in (result.data or []):
                duplicates.append({
                    "source": "本系統",
                    "case_no": app['case_no'],
                    "status": app['status'],
                    "approved_amount": app.get('approved_amount'),
                    "submitted_at": app['submitted_at']
                })
            
            return duplicates
        except Exception as e:
            print(f"Local duplicate check error: {e}")
            return []
    
    async def _check_bank_duplicates(self, id_number: str, disaster_date: str) -> List[Dict]:
        """透過銀行 API 檢查跨系統的重複申請"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.bank_api_url}/api/v1/subsidy/check-duplicate",
                    json={
                        "id_number": id_number,
                        "disaster_date": disaster_date
                    },
                    headers={
                        "Authorization": f"Bearer {self.bank_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('duplicates', [])
                else:
                    return []
        except Exception as e:
            print(f"Bank API duplicate check error: {e}")
            return []
    
    async def record_disbursement(
        self,
        certificate_id: str,
        application_id: str,
        amount: float,
        bank_code: str,
        account_number: str,
        disbursement_method: str
    ) -> Dict[str, Any]:
        """
        記錄補助發放到銀行系統
        
        Args:
            certificate_id: 憑證 ID
            application_id: 申請案件 ID
            amount: 發放金額
            bank_code: 銀行代碼
            account_number: 帳號
            disbursement_method: 發放方式
            
        Returns:
            記錄結果
        """
        result = {
            "success": False,
            "message": "",
            "transaction_id": None
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.bank_api_url}/api/v1/subsidy/disburse",
                    json={
                        "certificate_id": certificate_id,
                        "amount": amount,
                        "bank_code": bank_code,
                        "account_number": account_number,
                        "disbursement_method": disbursement_method
                    },
                    headers={
                        "Authorization": f"Bearer {self.bank_api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result['success'] = True
                    result['message'] = "發放記錄已送至銀行系統"
                    result['transaction_id'] = data.get('transaction_id')
                else:
                    result['message'] = "銀行系統記錄失敗"
                
                # 記錄到資料庫
                await self._record_verification(
                    application_id=application_id,
                    certificate_id=certificate_id,
                    verification_type='disbursement_record',
                    bank_code=bank_code,
                    account_number=account_number,
                    is_valid=result['success'],
                    verification_message=result['message'],
                    api_endpoint=f"{self.bank_api_url}/api/v1/subsidy/disburse",
                    api_request={"amount": amount, "method": disbursement_method},
                    api_response=result,
                    response_time_ms=200
                )
                
        except Exception as e:
            result['message'] = f"記錄過程發生錯誤: {str(e)}"
            print(f"Disbursement record error: {e}")
        
        return result
    
    async def _record_verification(
        self,
        application_id: str,
        verification_type: str,
        is_valid: bool,
        verification_message: str,
        certificate_id: Optional[str] = None,
        bank_code: Optional[str] = None,
        account_number: Optional[str] = None,
        account_holder_name: Optional[str] = None,
        error_code: Optional[str] = None,
        api_endpoint: Optional[str] = None,
        api_request: Optional[Dict] = None,
        api_response: Optional[Dict] = None,
        response_time_ms: Optional[int] = None,
        has_duplicate: bool = False,
        duplicate_details: Optional[List] = None
    ):
        """記錄驗證結果到資料庫"""
        try:
            record_data = {
                "application_id": application_id,
                "certificate_id": certificate_id,
                "verification_type": verification_type,
                "bank_code": bank_code,
                "bank_account": account_number,
                "account_holder_name": account_holder_name,
                "is_valid": is_valid,
                "verification_message": verification_message,
                "error_code": error_code,
                "api_endpoint": api_endpoint,
                "api_request": api_request,
                "api_response": api_response,
                "response_time_ms": response_time_ms,
                "has_duplicate": has_duplicate,
                "duplicate_details": duplicate_details,
                "verified_at": datetime.now().isoformat()
            }
            
            db_service.client.table('bank_verification_records').insert(
                record_data
            ).execute()
            
        except Exception as e:
            print(f"Failed to record verification: {e}")
    
    def get_verification_history(
        self,
        application_id: str,
        verification_type: Optional[str] = None
    ) -> List[Dict]:
        """
        取得驗證歷史記錄
        
        Args:
            application_id: 申請案件 ID
            verification_type: 驗證類型（可選）
            
        Returns:
            驗證記錄列表
        """
        try:
            query = db_service.client.table('bank_verification_records') \
                .select('*') \
                .eq('application_id', application_id) \
                .order('created_at', desc=True)
            
            if verification_type:
                query = query.eq('verification_type', verification_type)
            
            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"Get verification history error: {e}")
            return []


# 全域銀行 API 服務實例
bank_api_service = BankAPIService()

