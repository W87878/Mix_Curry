"""
政府數位憑證服務 - 發行端 + 驗證端 API 整合
"""
import httpx
import json
import qrcode
import io
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.settings import get_settings

settings = get_settings()

# 政府數位憑證沙盒 API 端點
ISSUER_API_BASE = getattr(settings, 'ISSUER_API_BASE', "https://issuer-sandbox.wallet.gov.tw")
VERIFIER_API_BASE = getattr(settings, 'VERIFIER_API_BASE', "https://verifier-sandbox.wallet.gov.tw")

# API 金鑰（從環境變數讀取）
ISSUER_API_KEY = getattr(settings, 'ISSUER_API_KEY', '')
VERIFIER_API_KEY = getattr(settings, 'VERIFIER_API_KEY', '')

class GovWalletService:
    """政府數位憑證服務"""
    
    def __init__(self):
        self.issuer_base_url = ISSUER_API_BASE
        self.verifier_base_url = VERIFIER_API_BASE
        self.issuer_api_key = ISSUER_API_KEY
        self.verifier_api_key = VERIFIER_API_KEY
        self.timeout = 30.0
        self.use_real_api = bool(ISSUER_API_KEY)  # 有 API 金鑰時使用真實 API
    
    # ==========================================
    # 發行端 API (Issuer) - 真實政府 API
    # ==========================================
    
    async def generate_qrcode_data(
        self,
        vctid: str,
        issuance_date: str,
        expired_date: str,
        fields: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        呼叫政府發行端 API 產生 QR Code
        
        API: POST /api/qrcode/data
        
        Args:
            vctid: VC 憑證 ID（例如：00000000_vpms_20250506_0522）
            issuance_date: 發行日期（格式：YYYYMMDD）
            expired_date: 過期日期（格式：YYYYMMDD）
            fields: 欄位列表，每個欄位包含：
                - ename: 欄位名稱（如：name, company, email）
                - content: 欄位內容
        
        Returns:
            包含 QR Code 和其他資訊的字典
        """
        # 🔍 檢查是否有臨時身分證號碼（TEMP_ 或 GOOGLE_ 開頭）
        has_temp_id = any(
            field.get('ename') == 'id_number' and 
            (str(field.get('content', '')).startswith('TEMP_') or 
             str(field.get('content', '')).startswith('GOOGLE_'))
            for field in fields
        )
        
        if not self.use_real_api or has_temp_id:
            # 沒有 API 金鑰或有臨時身分證，返回模擬資料
            if has_temp_id:
                print(f"⚠️ 檢測到臨時身分證號碼，使用模擬模式")
            return self._mock_qrcode_data(vctid, fields)
        
        try:
            payload = {
                "vcUid": vctid,  # 注意：政府 API 使用 vcUid，不是 vctid
                "issuanceDate": issuance_date,
                "expiredDate": expired_date,
                "fields": fields
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.issuer_base_url}/api/qrcode/data",
                    json=payload,
                    headers={
                        "Access-Token": self.issuer_api_key,
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "qr_code_data": result.get("qrCode"),
                    "transaction_id": result.get("transactionId"),
                    "deep_link": result.get("deepLink"),
                    "message": "QR Code 產生成功（真實 API）"
                }
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            print(f"呼叫政府發行端 API 失敗: {e}")
            print(f"詳細錯誤: {error_detail}")
            return {
                "success": False,
                "error": str(e),
                "error_detail": error_detail,
                "message": f"政府 API 呼叫失敗: {error_detail}"
            }
        except Exception as e:
            print(f"呼叫政府發行端 API 失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"政府 API 呼叫失敗: {str(e)}"
            }
    
    async def issue_disaster_relief_qrcode(
        self,
        application_data: Dict[str, Any],
        approved_amount: float,
        case_no: str
    ) -> Dict[str, Any]:
        """
        為災民補助申請發行數位憑證 QR Code
        
        Args:
            application_data: 申請資料
            approved_amount: 核准金額
            case_no: 案件編號
        
        Returns:
            QR Code 資料
        """
        # 產生 vctid（VC 憑證 ID）
        vctid = f"{case_no}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        
        # 計算發行日期和過期日期
        now = datetime.now()
        issuance_date = now.strftime("%Y%m%d")
        expired_date = (now + timedelta(days=90)).strftime("%Y%m%d")  # 90 天後過期
        
        # 準備欄位資料
        fields = [
            {
                "ename": "expiredDate",
                "content": expired_date
            },
            {
                "ename": "name",
                "content": application_data.get('applicant_name', '')
            },
            {
                "ename": "idNumber",
                "content": application_data.get('id_number', '')
            },
            {
                "ename": "caseNumber",
                "content": case_no
            },
            {
                "ename": "approvedAmount",
                "content": str(approved_amount)
            },
            {
                "ename": "disasterType",
                "content": self._translate_disaster_type(
                    application_data.get('disaster_type', 'typhoon')
                )
            },
            {
                "ename": "issuer",
                "content": "災害應變中心"
            }
        ]
        
        # 呼叫真實 API
        result = await self.generate_qrcode_data(
            vctid=vctid,
            issuance_date=issuance_date,
            expired_date=expired_date,
            fields=fields
        )
        
        return result
    
    async def check_credential_nonce(self, transaction_id: str) -> Dict[str, Any]:
        """
        檢查用戶是否已掃描並存入 VC 卡片
        
        API: GET /api/credential/nonce/{transactionId}
        
        此 API 用於檢查用戶是否已掃描 QR Code 並將憑證存入數位皮夾。
        
        Returns:
            {
                "credential": "eyJhbGc..." (JWT Token, 表示用戶已存入)
                或
                空 response (表示用戶尚未掃描或尚未存入)
            }
        """
        if not self.issuer_api_key:
            # 沒有 API 金鑰，返回模擬資料
            return self._mock_credential_nonce(transaction_id)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.issuer_base_url}/api/credential/nonce/{transaction_id}",
                    headers={
                        "Access-Token": self.issuer_api_key
                    }
                )
                
                # 如果返回 200 且有 credential，表示用戶已存入
                if response.status_code == 200:
                    result = response.json()
                    
                    if result.get("credential"):
                        # 解析 JWT Token 中的 jti 欄位
                        credential_jwt = result.get("credential")
                        print(f"✅ 用戶已存入憑證: {credential_jwt[:50]}...")
                        
                        return {
                            "success": True,
                            "claimed": True,
                            "credential": credential_jwt,
                            "message": "用戶已掃描並存入憑證"
                        }
                    else:
                        # 沒有 credential，用戶尚未掃描
                        return {
                            "success": True,
                            "claimed": False,
                            "message": "用戶尚未掃描或尚未存入憑證"
                        }
                
                # 其他狀態碼（如 400, 404）
                elif response.status_code == 400:
                    error_data = response.json()
                    return {
                        "success": False,
                        "claimed": False,
                        "error": error_data,
                        "message": f"查詢失敗: {error_data.get('message', 'QR Code未建構')}"
                    }
                else:
                    return {
                        "success": False,
                        "claimed": False,
                        "message": f"查詢失敗: HTTP {response.status_code}"
                    }
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            print(f"檢查憑證領取狀態失敗: {e}")
            print(f"詳細錯誤: {error_detail}")
            return {
                "success": False,
                "claimed": False,
                "error": error_detail,
                "message": f"政府 API 呼叫失敗: {error_detail}"
            }
        except Exception as e:
            print(f"檢查憑證領取狀態失敗: {e}")
            return {
                "success": False,
                "claimed": False,
                "error": str(e),
                "message": f"檢查失敗: {str(e)}"
            }
    
    def _mock_credential_nonce(self, transaction_id: str) -> Dict[str, Any]:
        """模擬憑證領取狀態檢查（開發用）"""
        # 模擬：前 5 次查詢返回「尚未領取」，第 6 次之後返回「已領取」
        import random
        if random.random() > 0.8:  # 20% 機率模擬已領取
            return {
                "success": True,
                "claimed": True,
                "credential": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.mock_credential_data",
                "message": "用戶已掃描並存入憑證（模擬）"
            }
        else:
            return {
                "success": True,
                "claimed": False,
                "message": "用戶尚未掃描或尚未存入憑證（模擬）"
            }

    def _mock_qrcode_data(self, vctid: str, fields: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        模擬 QR Code 資料（開發用）
        生成真實的 QR Code 圖片
        """
        # 準備 QR Code 內容
        qr_content = json.dumps({
            "vctid": vctid,
            "fields": fields,
            "mock": True,
            "timestamp": datetime.now().isoformat()
        })
        
        # 生成 QR Code 圖片
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_content)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 轉換為 base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        transaction_id = f"mock_{vctid[:20]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "success": True,
            "qr_code_data": img_base64,  # 返回 base64 編碼的圖片
            "transaction_id": transaction_id,
            "deep_link": f"twfido://verify?vctid={vctid}",
            "message": "QR Code 產生成功（模擬模式）"
        }
    
    # ==========================================
    # 驗證端 API (Verifier) - 真實政府 API
    # ==========================================
    
    async def generate_vp_qrcode(
        self,
        ref: str,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        產生 VP 驗證 QR Code（7-11 機台用）
        
        API: GET /api/oidvp/qrcode?ref=xxx&transactionId=xxx
        
        Args:
            ref: VP 驗證服務代碼（例如：00000000_subsidy_667）
            transaction_id: 交易 ID（隨機產生，不超過50字元）
        
        Returns:
            包含 qrcodeImage, authUri, transactionId 的字典
        """
        if not self.verifier_api_key:
            # 沒有 API 金鑰，返回模擬資料
            return self._mock_vp_qrcode(ref, transaction_id)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.verifier_base_url}/api/oidvp/qrcode",
                    params={
                        "ref": ref,
                        "transactionId": transaction_id
                    },
                    headers={
                        "Access-Token": self.verifier_api_key
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "qrcode_image": result.get("qrcodeImage"),
                    "auth_uri": result.get("authUri"),
                    "transaction_id": result.get("transactionId"),
                    "message": "VP QR Code 產生成功（真實 API）"
                }
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            print(f"呼叫政府驗證端 API 失敗: {e}")
            print(f"詳細錯誤: {error_detail}")
            return {
                "success": False,
                "error": str(e),
                "error_detail": error_detail,
                "message": f"政府 API 呼叫失敗: {error_detail}"
            }
        except Exception as e:
            print(f"呼叫政府驗證端 API 失敗: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"政府 API 呼叫失敗: {str(e)}"
            }
    
    async def verify_vp_result(
        self,
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        驗證 VP 掃描結果
        
        API: POST /api/oidvp/result
        
        Args:
            transaction_id: 從 generate_vp_qrcode 取得的 transactionId
        
        Returns:
            驗證結果，包含 verifyResult (bool)
        """
        if not self.verifier_api_key:
            # 沒有 API 金鑰，返回模擬資料
            return self._mock_vp_result(transaction_id)
        
        try:
            payload = {
                "transactionId": transaction_id
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.verifier_base_url}/api/oidvp/result",
                    json=payload,
                    headers={
                        "Access-Token": self.verifier_api_key,
                        "Content-Type": "application/json"
                    }
                )
                
                response.raise_for_status()
                result = response.json()
                
                return {
                    "success": True,
                    "verify_result": result.get("verifyResult", False),
                    "credential_data": result.get("data")[0],
                    "message": "驗證成功（真實 API）"
                }
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text if hasattr(e, 'response') else str(e)
            print(f"呼叫政府驗證端 API 失敗: {e}")
            print(f"詳細錯誤: {error_detail}")
            return {
                "success": False,
                "verify_result": False,
                "error": str(e),
                "error_detail": error_detail,
                "message": f"政府 API 呼叫失敗: {error_detail}"
            }
        except Exception as e:
            print(f"呼叫政府驗證端 API 失敗: {e}")
            return {
                "success": False,
                "verify_result": False,
                "error": str(e),
                "message": f"政府 API 呼叫失敗: {str(e)}"
            }
    
    def _mock_vp_qrcode(self, ref: str, transaction_id: str) -> Dict[str, Any]:
        """模擬 VP QR Code 產生（開發用）
        生成真實的 QR Code 圖片
        """
        # 準備 VP 驗證 QR Code 內容
        auth_uri = f"twfido://verify?ref={ref}&txn={transaction_id}"
        
        # 生成 QR Code 圖片
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(auth_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 轉換為 base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "success": True,
            "qrcode_image": img_base64,  # 返回 base64 編碼的圖片
            "auth_uri": auth_uri,
            "transaction_id": transaction_id,
            "message": "VP QR Code 產生成功（模擬模式）"
        }
    
    def _mock_vp_result(self, transaction_id: str) -> Dict[str, Any]:
        """模擬 VP 驗證結果（開發用）"""
        return {
            "success": True,
            "verify_result": True,
            "credential_data": {
                "name": "王小明",
                "id_number": "A123456789",
                "phone_number": "0912345678",
                "address": "台南市中西區民生路100號",
                "approved_amount": 50000
            },
            "message": "驗證成功（模擬模式）"
        }
    
    # ==========================================
    # 輔助函數
    # ==========================================
    
    def _translate_disaster_type(self, disaster_type: str) -> str:
        """翻譯災害類型"""
        translations = {
            "typhoon": "颱風",
            "flood": "水災",
            "earthquake": "地震",
            "landslide": "土石流",
            "fire": "火災"
        }
        return translations.get(disaster_type, disaster_type)
    
    def _translate_subsidy_type(self, subsidy_type: str) -> str:
        """翻譯補助類型"""
        translations = {
            "housing": "房屋修繕",
            "living": "生活補助",
            "medical": "醫療補助",
            "business": "營業損失"
        }
        return translations.get(subsidy_type, subsidy_type)


# 單例模式
_gov_wallet_service = None

def get_gov_wallet_service() -> GovWalletService:
    """取得政府數位憑證服務實例"""
    global _gov_wallet_service
    if _gov_wallet_service is None:
        _gov_wallet_service = GovWalletService()
    return _gov_wallet_service

