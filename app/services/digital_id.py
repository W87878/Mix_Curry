"""
數位憑證驗證服務
整合政府 TW FidO 和數位身分證 API
"""
import httpx
import json
from typing import Optional, Dict, Any
from datetime import datetime
from app.settings import get_settings

settings = get_settings()


class DigitalIDService:
    """數位身分證驗證服務"""
    
    def __init__(self):
        # TODO: 從環境變數讀取
        self.twfido_api_url = getattr(settings, 'TWFIDO_API_URL', 'https://twfido-sandbox.nat.gov.tw')
        self.digital_id_api_url = getattr(settings, 'DIGITAL_ID_API_URL', 'https://digital-id-sandbox.gov.tw')
        self.api_key = getattr(settings, 'DIGITAL_ID_API_KEY', '')
        self.timeout = 30.0
    
    async def verify_qr_code(self, qr_code_data: str) -> Dict[str, Any]:
        """
        驗證數位憑證 QR Code
        
        Args:
            qr_code_data: QR Code 掃描的原始資料
            
        Returns:
            驗證結果，包含用戶資訊
        """
        result = {
            "verified": False,
            "user_info": None,
            "error": None
        }
        
        try:
            # 解析 QR Code 資料
            qr_data = self._parse_qr_code(qr_code_data)
            
            if not qr_data:
                result["error"] = "無效的 QR Code 格式"
                return result
            
            # 呼叫政府驗證 API
            verified_data = await self._verify_with_gov_api(qr_data)
            
            if verified_data:
                result["verified"] = True
                result["user_info"] = {
                    "id_number": verified_data.get("id_number"),
                    "full_name": verified_data.get("name"),
                    "birth_date": verified_data.get("birth_date"),
                    "gender": verified_data.get("gender"),
                    "address": verified_data.get("address"),
                    "verified_at": datetime.now().isoformat()
                }
            else:
                result["error"] = "政府憑證驗證失敗"
        
        except Exception as e:
            result["error"] = f"驗證過程發生錯誤: {str(e)}"
            print(f"Digital ID verification error: {e}")
        
        return result
    
    async def verify_with_twfido(self, credential_data: Dict) -> Dict[str, Any]:
        """
        使用 TW FidO 驗證數位憑證
        
        Args:
            credential_data: TW FidO 憑證資料
            
        Returns:
            驗證結果
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.twfido_api_url}/api/v1/verify",
                    json=credential_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "verified": data.get("verified", False),
                        "user_info": data.get("user_info"),
                        "confidence_level": data.get("confidence_level")
                    }
                else:
                    return {
                        "verified": False,
                        "error": "TW FidO 驗證失敗"
                    }
        
        except Exception as e:
            print(f"TW FidO verification error: {e}")
            return {
                "verified": False,
                "error": str(e)
            }
    
    async def verify_digital_id_card(self, card_data: Dict) -> Dict[str, Any]:
        """
        驗證新式數位身分證
        
        Args:
            card_data: 數位身分證資料
            
        Returns:
            驗證結果
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.digital_id_api_url}/api/v1/verify-card",
                    json=card_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "verified": True,
                        "user_info": {
                            "id_number": data.get("national_id"),
                            "full_name": data.get("name"),
                            "birth_date": data.get("birth_date"),
                            "gender": data.get("gender"),
                            "address": data.get("address")
                        }
                    }
                else:
                    return {
                        "verified": False,
                        "error": "身分證驗證失敗"
                    }
        
        except Exception as e:
            print(f"Digital ID card verification error: {e}")
            return {
                "verified": False,
                "error": str(e)
            }
    
    def _parse_qr_code(self, qr_code_data: str) -> Optional[Dict]:
        """解析 QR Code 資料"""
        try:
            # 嘗試解析為 JSON
            data = json.loads(qr_code_data)
            return data
        except json.JSONDecodeError:
            # 嘗試其他格式
            # 例如：ID:A123456789|NAME:王小明|DATE:2024-01-01
            if '|' in qr_code_data:
                parts = qr_code_data.split('|')
                data = {}
                for part in parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        data[key.lower()] = value
                return data
        except Exception as e:
            print(f"QR code parse error: {e}")
        
        return None
    
    async def _verify_with_gov_api(self, qr_data: Dict) -> Optional[Dict]:
        """呼叫政府驗證 API（實際整合）"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.digital_id_api_url}/api/v1/verify",
                    json=qr_data,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Gov API verification error: {e}")
        
        return None
    
    async def mock_verify(self, qr_code_data: str) -> Dict[str, Any]:
        """
        模擬驗證（開發/測試用）
        
        在沒有實際政府 API 的情況下使用
        """
        result = {
            "verified": False,
            "user_info": None,
            "error": None
        }
        
        try:
            # 解析 QR Code
            qr_data = self._parse_qr_code(qr_code_data)
            
            if qr_data:
                # 模擬驗證成功
                result["verified"] = True
                result["user_info"] = {
                    "id_number": qr_data.get("id", qr_data.get("id_number", "A123456789")),
                    "full_name": qr_data.get("name", qr_data.get("full_name", "測試用戶")),
                    "birth_date": qr_data.get("birth_date", qr_data.get("date", "1990-01-01")),
                    "gender": qr_data.get("gender", "M"),
                    "address": qr_data.get("address", ""),
                    "verified_at": datetime.now().isoformat(),
                    "mock": True  # 標記為模擬資料
                }
            else:
                result["error"] = "無效的 QR Code 格式"
        
        except Exception as e:
            result["error"] = f"模擬驗證錯誤: {str(e)}"
        
        return result
    
    def generate_mock_qr_code(
        self, 
        id_number: str, 
        full_name: str,
        birth_date: str = "1990-01-01"
    ) -> str:
        """
        生成模擬 QR Code 資料（測試用）
        
        Args:
            id_number: 身分證字號
            full_name: 姓名
            birth_date: 出生日期
            
        Returns:
            QR Code 資料字串
        """
        data = {
            "id": id_number,
            "name": full_name,
            "date": birth_date,
            "type": "digital_id",
            "issued_at": datetime.now().isoformat()
        }
        return json.dumps(data, ensure_ascii=False)


# 全域實例
digital_id_service = DigitalIDService()


# 便捷函數
async def verify_digital_credential(qr_code_data: str, use_mock: bool = None) -> Dict[str, Any]:
    """
    驗證數位憑證（統一入口）
    
    Args:
        qr_code_data: QR Code 資料
        use_mock: 是否使用模擬模式（None 則自動判斷）
        
    Returns:
        驗證結果
    """
    if use_mock is None:
        # 開發模式自動使用模擬
        use_mock = settings.DEBUG
    
    if use_mock:
        return await digital_id_service.mock_verify(qr_code_data)
    else:
        return await digital_id_service.verify_qr_code(qr_code_data)


def generate_test_credential(id_number: str, full_name: str) -> str:
    """
    生成測試用數位憑證
    
    用於開發和測試
    """
    return digital_id_service.generate_mock_qr_code(id_number, full_name)

