"""
政府數位憑證沙盒 API 整合服務
整合發行端和驗證端 API
"""
import httpx
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.settings import get_settings

settings = get_settings()

# 政府數位憑證沙盒 API 端點
ISSUER_API_BASE = "https://issuer-sandbox.wallet.gov.tw"
VERIFIER_API_BASE = "https://verifier-sandbox.wallet.gov.tw"

class GovWalletService:
    """政府數位憑證服務"""
    
    def __init__(self):
        self.issuer_base_url = ISSUER_API_BASE
        self.verifier_base_url = VERIFIER_API_BASE
        self.timeout = 30.0
    
    # ==========================================
    # 發行端 API (Issuer)
    # ==========================================
    
    async def issue_credential(
        self,
        credential_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        發行數位憑證
        
        Args:
            credential_data: 憑證資料，包含：
                - credentialSubject: 憑證主體資料
                - type: 憑證類型
                - issuer: 發行者資訊
                - expirationDate: 過期日期
        
        Returns:
            包含憑證 ID 和 QR Code 資料的字典
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.issuer_base_url}/api/v1/credentials/issue",
                    json=credential_data,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"發行憑證失敗: {e}")
            raise Exception(f"政府 API 發行憑證失敗: {str(e)}")
    
    async def create_disaster_relief_credential(
        self,
        application_data: Dict[str, Any],
        approved_amount: float,
        case_no: str
    ) -> Dict[str, Any]:
        """
        建立災民補助數位憑證
        
        Args:
            application_data: 申請案件資料
            approved_amount: 核准金額
            case_no: 案件編號
        
        Returns:
            憑證資料和 QR Code
        """
        # 準備憑證資料（符合政府 API 格式）
        credential_data = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://wallet.gov.tw/credentials/disaster-relief/v1"
            ],
            "type": ["VerifiableCredential", "DisasterReliefCredential"],
            "issuer": {
                "id": "did:tw:gov:disaster-relief",
                "name": "災害應變中心"
            },
            "issuanceDate": datetime.now().isoformat(),
            "expirationDate": (datetime.now() + timedelta(days=365)).isoformat(),
            "credentialSubject": {
                "id": f"did:tw:citizen:{application_data['id_number']}",
                "caseNumber": case_no,
                "applicantName": application_data['applicant_name'],
                "idNumber": application_data['id_number'],
                "disasterType": self._translate_disaster_type(application_data.get('disaster_type', 'typhoon')),
                "disasterDate": application_data.get('disaster_date', ''),
                "approvedAmount": approved_amount,
                "currency": "TWD",
                "address": application_data.get('address', ''),
                "damageDescription": application_data.get('damage_description', ''),
                "subsidyType": self._translate_subsidy_type(application_data.get('subsidy_type', 'housing'))
            }
        }
        
        # 呼叫政府 API 發行憑證
        result = await self.issue_credential(credential_data)
        return result
    
    async def generate_qr_code_for_credential(
        self,
        credential_id: str
    ) -> Dict[str, Any]:
        """
        為憑證生成 QR Code（用於出示）
        
        Args:
            credential_id: 憑證 ID
        
        Returns:
            QR Code 資料
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.issuer_base_url}/api/v1/credentials/{credential_id}/qrcode",
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"生成 QR Code 失敗: {e}")
            raise Exception(f"生成 QR Code 失敗: {str(e)}")
    
    async def add_credential_to_wallet(
        self,
        credential_data: Dict[str, Any],
        wallet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        將憑證加入數位憑證皮夾
        
        Args:
            credential_data: 憑證資料
            wallet_id: 皮夾 ID（選填）
        
        Returns:
            加入結果
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "credential": credential_data,
                    "walletId": wallet_id
                }
                response = await client.post(
                    f"{self.issuer_base_url}/api/v1/wallet/add",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"加入憑證失敗: {e}")
            raise Exception(f"加入憑證失敗: {str(e)}")
    
    # ==========================================
    # 驗證端 API (Verifier)
    # ==========================================
    
    async def verify_credential(
        self,
        credential_or_qr_data: str
    ) -> Dict[str, Any]:
        """
        驗證數位憑證
        
        Args:
            credential_or_qr_data: 憑證 JSON 字串或 QR Code 掃描資料
        
        Returns:
            驗證結果
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.verifier_base_url}/api/v1/verify",
                    json={"credential": credential_or_qr_data},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                # 檢查驗證結果
                if result.get('verified') == True:
                    return {
                        "success": True,
                        "verified": True,
                        "credential": result.get('credential', {}),
                        "message": "憑證驗證成功"
                    }
                else:
                    return {
                        "success": False,
                        "verified": False,
                        "reason": result.get('reason', '憑證驗證失敗'),
                        "message": "憑證驗證失敗"
                    }
        except httpx.HTTPError as e:
            print(f"驗證憑證失敗: {e}")
            return {
                "success": False,
                "verified": False,
                "reason": str(e),
                "message": "驗證 API 呼叫失敗"
            }
    
    async def create_verification_request(
        self,
        required_credentials: list,
        purpose: str = "災民補助發放驗證"
    ) -> Dict[str, Any]:
        """
        建立驗證請求（用於發放補助時）
        
        Args:
            required_credentials: 需要的憑證類型列表
            purpose: 驗證目的
        
        Returns:
            驗證請求資料（包含 QR Code）
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "purpose": purpose,
                    "requiredCredentials": required_credentials,
                    "verifier": {
                        "id": "did:tw:gov:disaster-relief-verifier",
                        "name": "災害應變中心（發放窗口）"
                    }
                }
                response = await client.post(
                    f"{self.verifier_base_url}/api/v1/verification/request",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"建立驗證請求失敗: {e}")
            raise Exception(f"建立驗證請求失敗: {str(e)}")
    
    async def scan_qr_code_for_verification(
        self,
        qr_data: str
    ) -> Dict[str, Any]:
        """
        掃描 QR Code 並驗證憑證
        
        Args:
            qr_data: QR Code 掃描後的資料
        
        Returns:
            驗證結果和憑證內容
        """
        # 解析 QR Code 資料
        try:
            qr_json = json.loads(qr_data) if isinstance(qr_data, str) else qr_data
        except:
            return {
                "success": False,
                "message": "QR Code 格式錯誤"
            }
        
        # 驗證憑證
        verification_result = await self.verify_credential(qr_data)
        
        if verification_result.get('verified'):
            credential = verification_result.get('credential', {})
            credential_subject = credential.get('credentialSubject', {})
            
            return {
                "success": True,
                "verified": True,
                "case_number": credential_subject.get('caseNumber'),
                "applicant_name": credential_subject.get('applicantName'),
                "id_number": credential_subject.get('idNumber'),
                "approved_amount": credential_subject.get('approvedAmount'),
                "disaster_type": credential_subject.get('disasterType'),
                "expiration_date": credential.get('expirationDate'),
                "credential_data": credential
            }
        else:
            return {
                "success": False,
                "verified": False,
                "reason": verification_result.get('reason', '憑證驗證失敗')
            }
    
    # ==========================================
    # 輔助方法
    # ==========================================
    
    def _translate_disaster_type(self, disaster_type: str) -> str:
        """翻譯災害類型為中文"""
        type_map = {
            "flood": "水災",
            "typhoon": "颱風",
            "earthquake": "地震",
            "fire": "火災",
            "other": "其他"
        }
        return type_map.get(disaster_type, disaster_type)
    
    def _translate_subsidy_type(self, subsidy_type: str) -> str:
        """翻譯補助類型為中文"""
        type_map = {
            "housing": "房屋補助",
            "equipment": "設備補助",
            "living": "生活補助",
            "business": "營業補助"
        }
        return type_map.get(subsidy_type, subsidy_type)

# 全域服務實例
gov_wallet_service = GovWalletService()

