"""
數位憑證驗證服務 V2 - 完整版
實作正確的數位憑證掃描流程

流程：
1. 網站產生 QR Code（包含 session_id 和 challenge）
2. 使用者用政府 APP 掃描
3. APP 向政府後端驗證
4. 網站輪詢或接收驗證結果
5. 完成登入
"""
import httpx
import json
import uuid
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.settings import get_settings

settings = get_settings()


class DigitalIDServiceV2:
    """完整的數位憑證驗證服務"""
    
    def __init__(self):
        # 政府 API 設定
        self.twfido_api_url = getattr(settings, 'TWFIDO_API_URL', 'https://twfido-sandbox.nat.gov.tw')
        self.digital_id_api_url = getattr(settings, 'DIGITAL_ID_API_URL', 'https://digital-id-sandbox.gov.tw')
        self.api_key = getattr(settings, 'DIGITAL_ID_API_KEY', '')
        
        # 網站回調 URL
        self.callback_url = getattr(settings, 'CALLBACK_URL', 'http://localhost:8080/api/v1/auth/digital-id/callback')
        
        # Session 儲存（生產環境應使用 Redis）
        self.sessions = {}
        
        self.timeout = 30.0
    
    def generate_qr_code_for_scan(self, session_type: str = "login") -> Dict[str, Any]:
        """
        產生供政府 APP 掃描的 QR Code
        
        Args:
            session_type: 'login' 或 'register'
            
        Returns:
            包含 QR Code 內容和 session_id
        """
        # 1. 產生唯一的 session ID
        session_id = str(uuid.uuid4())
        
        # 2. 產生挑戰碼（challenge）
        challenge = self._generate_challenge()
        
        # 3. 建立 session（有效期 5 分鐘）
        self.sessions[session_id] = {
            "session_id": session_id,
            "challenge": challenge,
            "session_type": session_type,
            "status": "pending",  # pending, verified, expired, failed
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "user_info": None
        }
        
        # 4. 組成 QR Code 內容（簡化版，避免超過容量）
        # 只包含最必要的資訊
        qr_code_data = {
            "sid": session_id,  # session_id 縮寫
            "ch": challenge[:32],  # 只取前 32 字元
            "ts": int(datetime.now().timestamp())  # 使用時間戳而非 ISO 格式
        }
        
        # 完整資料（給前端顯示用）
        full_data = {
            "type": "digital_id_auth",
            "version": "1.0",
            "session_id": session_id,
            "challenge": challenge,
            "callback_url": self.callback_url,
            "website": "災民補助申請系統",
            "purpose": "身份驗證",
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "session_id": session_id,
            "qr_code_data": json.dumps(qr_code_data, ensure_ascii=False),  # 簡化版給 QR Code
            "qr_code_url": f"twfido://verify?sid={session_id}",  # 簡化的 Deep link
            "full_data": full_data,  # 完整資料（可選）
            "expires_in": 300  # 5 分鐘
        }
    
    async def check_verification_status(self, session_id: str) -> Dict[str, Any]:
        """
        檢查驗證狀態（前端輪詢用）
        
        Args:
            session_id: Session ID
            
        Returns:
            驗證狀態和用戶資訊
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return {
                "status": "not_found",
                "message": "Session 不存在"
            }
        
        # 檢查是否過期
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.now() > expires_at:
            session["status"] = "expired"
            return {
                "status": "expired",
                "message": "QR Code 已過期，請重新產生"
            }
        
        # 返回當前狀態
        result = {
            "status": session["status"],
            "session_id": session_id
        }
        
        if session["status"] == "verified":
            result["user_info"] = session["user_info"]
        
        return result
    
    async def handle_verification_callback(
        self, 
        session_id: str, 
        verification_data: Dict
    ) -> Dict[str, Any]:
        """
        處理政府後端的驗證回調
        
        Args:
            session_id: Session ID
            verification_data: 政府後端返回的驗證資料
            
        Returns:
            處理結果
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return {
                "success": False,
                "error": "Session 不存在"
            }
        
        # 檢查是否過期
        expires_at = datetime.fromisoformat(session["expires_at"])
        if datetime.now() > expires_at:
            return {
                "success": False,
                "error": "Session 已過期"
            }
        
        # 驗證簽章（確保資料來自政府後端）
        if not self._verify_signature(verification_data):
            return {
                "success": False,
                "error": "簽章驗證失敗"
            }
        
        # 驗證 challenge
        if verification_data.get("challenge") != session["challenge"]:
            return {
                "success": False,
                "error": "Challenge 不符"
            }
        
        # 更新 session 狀態
        session["status"] = "verified"
        session["user_info"] = {
            "id_number": verification_data.get("national_id"),
            "full_name": verification_data.get("name"),
            "birth_date": verification_data.get("birth_date"),
            "verified_at": datetime.now().isoformat(),
            "verification_level": verification_data.get("level", "high")  # high, medium, low
        }
        
        return {
            "success": True,
            "message": "驗證成功"
        }
    
    async def verify_with_gov_api(
        self, 
        session_id: str,
        app_response: Dict
    ) -> Dict[str, Any]:
        """
        向政府 API 驗證（如果政府不支援 callback）
        
        Args:
            session_id: Session ID
            app_response: APP 返回的驗證資料
            
        Returns:
            驗證結果
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 呼叫政府驗證 API
                response = await client.post(
                    f"{self.twfido_api_url}/api/v1/verify",
                    json={
                        "session_id": session_id,
                        "response": app_response,
                        "api_key": self.api_key
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 更新 session
                    session = self.sessions.get(session_id)
                    if session:
                        session["status"] = "verified"
                        session["user_info"] = data.get("user_info")
                    
                    return {
                        "verified": True,
                        "user_info": data.get("user_info")
                    }
                else:
                    return {
                        "verified": False,
                        "error": "政府 API 驗證失敗"
                    }
        
        except Exception as e:
            print(f"Gov API verification error: {e}")
            return {
                "verified": False,
                "error": str(e)
            }
    
    def _generate_challenge(self) -> str:
        """產生挑戰碼"""
        random_data = f"{uuid.uuid4()}{datetime.now().isoformat()}"
        return hashlib.sha256(random_data.encode()).hexdigest()
    
    def _verify_signature(self, data: Dict) -> bool:
        """
        驗證政府後端的簽章
        
        生產環境應該：
        1. 使用政府提供的公鑰
        2. 驗證 JWT 簽章
        3. 檢查憑證鏈
        """
        # TODO: 實作真實的簽章驗證
        # 目前開發環境直接返回 True
        return True
    
    def cleanup_expired_sessions(self):
        """清理過期的 sessions"""
        now = datetime.now()
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if datetime.fromisoformat(session["expires_at"]) < now
        ]
        
        for sid in expired_sessions:
            del self.sessions[sid]
    
    # ==========================================
    # 模擬模式（測試用）
    # ==========================================
    
    async def mock_app_scan(self, session_id: str, mock_user: Dict) -> Dict[str, Any]:
        """
        模擬政府 APP 掃描和驗證（測試用）
        
        Args:
            session_id: Session ID
            mock_user: 模擬的用戶資料
            
        Returns:
            驗證結果
        """
        session = self.sessions.get(session_id)
        
        if not session:
            return {
                "success": False,
                "error": "Session 不存在"
            }
        
        # 模擬驗證成功
        session["status"] = "verified"
        session["user_info"] = {
            "id_number": mock_user.get("id_number", "A123456789"),
            "full_name": mock_user.get("full_name", "測試用戶"),
            "birth_date": mock_user.get("birth_date", "1990-01-01"),
            "verified_at": datetime.now().isoformat(),
            "verification_level": "high",
            "mock": True
        }
        
        return {
            "success": True,
            "message": "模擬驗證成功",
            "user_info": session["user_info"]
        }


# 全域實例
digital_id_service_v2 = DigitalIDServiceV2()


# 便捷函數
def generate_login_qr_code() -> Dict[str, Any]:
    """產生登入用 QR Code"""
    return digital_id_service_v2.generate_qr_code_for_scan("login")


async def check_login_status(session_id: str) -> Dict[str, Any]:
    """檢查登入狀態（輪詢）"""
    return await digital_id_service_v2.check_verification_status(session_id)


async def mock_verify(session_id: str, user_data: Dict) -> Dict[str, Any]:
    """模擬驗證（測試用）"""
    return await digital_id_service_v2.mock_app_scan(session_id, user_data)

