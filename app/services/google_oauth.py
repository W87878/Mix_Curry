"""
Google OAuth 服務
處理 Gmail 登入整合
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import httpx
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GoogleOAuthService:
    """Google OAuth 服務類別"""
    
    def __init__(self):
        """初始化 Google OAuth 服務"""
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/api/v1/auth/google/callback")
        
        if not self.client_id or not self.client_secret:
            logger.warning("未設定 GOOGLE_CLIENT_ID 或 GOOGLE_CLIENT_SECRET")
        
        self.authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_endpoint = "https://oauth2.googleapis.com/token"
        self.userinfo_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
        
        # OAuth scopes
        self.scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile"
        ]
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        取得 Google OAuth 授權 URL
        
        Args:
            state: 狀態參數（用於防止 CSRF 攻擊）
            
        Returns:
            授權 URL
        """
        if not self.client_id:
            raise ValueError("未設定 GOOGLE_CLIENT_ID")
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "access_type": "offline",
            "prompt": "consent"
        }
        
        if state:
            params["state"] = state
        
        # 構建 URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{self.authorization_endpoint}?{query_string}"
        
        logger.info(f"Generated authorization URL: {auth_url}")
        return auth_url
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        用授權碼換取存取權杖
        
        Args:
            code: Google OAuth 授權碼
            
        Returns:
            包含 access_token, refresh_token 等資訊的字典
            
        Raises:
            HTTPException: 如果請求失敗
        """
        if not self.client_id or not self.client_secret:
            raise ValueError("未設定 GOOGLE_CLIENT_ID 或 GOOGLE_CLIENT_SECRET")
        
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_endpoint,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Token exchange failed: {response.text}")
                    raise Exception(f"Token exchange failed: {response.text}")
                
                token_data = response.json()
                logger.info("Successfully exchanged code for token")
                return token_data
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {str(e)}")
            raise
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        取得使用者資訊
        
        Args:
            access_token: Google 存取權杖
            
        Returns:
            使用者資訊字典
            
        Raises:
            HTTPException: 如果請求失敗
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_endpoint,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code != 200:
                    logger.error(f"Get user info failed: {response.text}")
                    raise Exception(f"Get user info failed: {response.text}")
                
                user_info = response.json()
                logger.info(f"Retrieved user info for: {user_info.get('email')}")
                return user_info
                
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise
    
    def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        驗證 Google ID Token
        
        Args:
            id_token: Google ID Token (JWT)
            
        Returns:
            解碼後的 Token payload
            
        Note:
            在生產環境中應該驗證簽章，這裡簡化處理
        """
        try:
            # 注意：這裡沒有驗證簽章，僅解碼
            # 在生產環境中應該使用 google.auth 來驗證
            payload = jwt.decode(
                id_token,
                options={"verify_signature": False}
            )
            
            logger.info(f"ID Token verified for: {payload.get('email')}")
            return payload
            
        except Exception as e:
            logger.error(f"Error verifying ID token: {str(e)}")
            raise
    
    async def login_or_create_user(self, user_info: Dict[str, Any], db_service) -> Dict[str, Any]:
        """
        根據 Google 使用者資訊登入或建立新使用者
        
        Args:
            user_info: Google 使用者資訊
            db_service: 資料庫服務
            
        Returns:
            使用者資料字典
        """
        email = user_info.get("email")
        if not email:
            raise ValueError("Google 使用者資訊中沒有 email")
        
        # 嘗試查詢現有使用者
        try:
            existing_user = db_service.get_user_by_email(email)
            
            if existing_user:
                # 更新最後登入時間
                update_data = {
                    "last_login_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                # 如果使用者沒有 full_name，從 Google 更新
                if not existing_user.get("full_name") and user_info.get("name"):
                    update_data["full_name"] = user_info.get("name")
                
                db_service.client.table("users").update(update_data).eq("id", existing_user["id"]).execute()
                
                logger.info(f"User logged in via Google: {email}")
                return existing_user
            
        except Exception as e:
            logger.info(f"User not found, will create new: {email}")
        
        # 建立新使用者
        try:
            # 從 Google 資料提取資訊
            full_name = user_info.get("name", user_info.get("email", "").split("@")[0])
            google_id = user_info.get("id", email.replace("@", "_").replace(".", "_"))
            
            new_user_data = {
                "email": email,
                "full_name": full_name,
                "role": "applicant",  # 預設角色為申請人
                "is_active": True,
                "is_verified": False,  # Google 登入後仍需填寫申請表單才算完全驗證
                "twfido_verified": False,
                "last_login_at": datetime.now().isoformat(),
                "digital_identity": {
                    "provider": "google",
                    "google_id": user_info.get("id"),
                    "picture": user_info.get("picture"),
                    "verified_email": user_info.get("verified_email", False)
                }
            }
            
            # ⚠️ 重要：id_number 和 phone 是臨時值
            # 使用者在填寫申請表單時，會更新為真實的身分證字號和手機號碼
            # 格式：GOOGLE_XXXXX 表示透過 Google 登入，待填寫申請表單時更新
            new_user_data["id_number"] = "" # 空字串，待填寫表單時更新
            new_user_data["phone"] = ""  # 空字串，待填寫表單時更新
            
            result = db_service.client.table("users").insert(new_user_data).execute()
            
            if result.data and len(result.data) > 0:
                new_user = result.data[0]
                logger.info(f"Created new user via Google: {email}")
                return new_user
            else:
                raise Exception("Failed to create user")
                
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise


# 建立全域服務實例
google_oauth_service = GoogleOAuthService()


def get_google_oauth_service() -> GoogleOAuthService:
    """取得 Google OAuth 服務實例（用於依賴注入）"""
    return google_oauth_service
