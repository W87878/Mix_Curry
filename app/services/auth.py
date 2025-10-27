"""
身份驗證服務模組
實作 JWT Token 驗證、角色權限管理、數位身份驗證
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.settings import get_settings
from app.models.database import db_service

settings = get_settings()

# JWT 設定
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 小時
REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7 天

# 密碼加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer Token
security = HTTPBearer()


class AuthService:
    """身份驗證服務"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        建立 JWT Access Token
        
        Args:
            data: Token 資料（包含 user_id, role 等）
            expires_delta: 過期時間
            
        Returns:
            JWT Token 字串
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """
        建立 JWT Refresh Token
        
        Args:
            data: Token 資料
            
        Returns:
            JWT Refresh Token 字串
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        驗證 JWT Token
        
        Args:
            token: JWT Token 字串
            
        Returns:
            Token payload
            
        Raises:
            HTTPException: Token 無效或過期
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的認證憑證",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def hash_password(password: str) -> str:
        """密碼加密"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """驗證密碼"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[Dict]:
        """
        驗證使用者（帳號密碼）
        
        Args:
            email: 電子郵件
            password: 密碼
            
        Returns:
            使用者資料 或 None
        """
        try:
            user = db_service.get_user_by_email(email)
            if not user:
                return None
            
            # TODO: 實作密碼驗證（目前資料庫沒有 password 欄位）
            # if not AuthService.verify_password(password, user.get('password')):
            #     return None
            
            # 更新最後登入時間
            db_service.client.table('users').update({
                'last_login_at': datetime.now().isoformat()
            }).eq('id', user['id']).execute()
            
            return user
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    @staticmethod
    async def verify_digital_identity(id_number: str, digital_credential: Dict) -> bool:
        """
        驗證數位身份（整合 TW FidO 或政府數位憑證）
        
        Args:
            id_number: 身分證字號
            digital_credential: 數位憑證資料
            
        Returns:
            驗證結果
        """
        # TODO: 整合 TW FidO API
        # 這裡暫時返回 True，實際需要呼叫政府數位憑證 API
        try:
            # 示例：呼叫 TW FidO API
            # response = await twfido_api.verify(id_number, digital_credential)
            # return response['verified']
            
            # 暫時模擬驗證
            return True
        except Exception as e:
            print(f"Digital identity verification error: {e}")
            return False


# ==========================================
# 依賴注入：取得當前使用者
# ==========================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    取得當前登入的使用者
    
    Args:
        credentials: HTTP Bearer Token
        
    Returns:
        使用者資料
        
    Raises:
        HTTPException: 認證失敗
    """
    token = credentials.credentials
    payload = AuthService.verify_token(token)
    
    # Support both "user_id" (traditional) and "sub" (Google OAuth) fields
    user_id = payload.get("user_id") or payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證憑證",
        )
    
    try:
        user = db_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="使用者不存在",
            )
        
        if not user.get('is_active'):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="帳戶已被停用",
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"認證失敗: {str(e)}",
        )


# ==========================================
# 角色權限檢查
# ==========================================

class RoleChecker:
    """角色權限檢查器"""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: Dict = Depends(get_current_user)) -> Dict:
        """
        檢查使用者角色
        
        Args:
            current_user: 當前使用者
            
        Returns:
            使用者資料
            
        Raises:
            HTTPException: 權限不足
        """
        user_role = current_user.get('role')
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足。需要角色: {', '.join(self.allowed_roles)}",
            )
        return current_user


# 預定義的角色檢查器
require_applicant = RoleChecker(["applicant", "reviewer", "admin"])
require_reviewer = RoleChecker(["reviewer", "admin"])
require_admin = RoleChecker(["admin"])


# ==========================================
# 區域權限檢查
# ==========================================

class DistrictChecker:
    """區域權限檢查器（里長只能查看自己轄區）"""
    
    @staticmethod
    def check_district_access(
        user: Dict,
        application: Dict
    ) -> bool:
        """
        檢查使用者是否有權限存取該申請案件
        
        Args:
            user: 使用者資料
            application: 申請案件資料
            
        Returns:
            是否有權限
        """
        # 管理員可以存取所有案件
        if user.get('role') == 'admin':
            return True
        
        # 申請人可以存取自己的案件
        if user.get('id') == application.get('applicant_id'):
            return True
        
        # 里長只能存取自己轄區的案件
        if user.get('role') == 'reviewer':
            return user.get('district_id') == application.get('district_id')
        
        return False


async def check_application_access(
    application_id: str,
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    檢查申請案件存取權限
    
    Args:
        application_id: 申請案件 ID
        current_user: 當前使用者
        
    Returns:
        申請案件資料
        
    Raises:
        HTTPException: 權限不足或案件不存在
    """
    try:
        application = db_service.get_application_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="申請案件不存在",
            )
        
        if not DistrictChecker.check_district_access(current_user, application):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您沒有權限存取此申請案件",
            )
        
        return application
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查詢申請案件失敗: {str(e)}",
        )


# ==========================================
# 全域認證服務實例
# ==========================================

auth_service = AuthService()

