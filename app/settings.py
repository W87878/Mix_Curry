from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Supabase 設定
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE: str = ""
    SUPABASE_ANON_KEY: Optional[str] = ""
    
    # FastAPI 設定
    APP_NAME: str = "災民補助申請系統"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # JWT 設定
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 政府數位憑證 API 設定
    ISSUER_API_BASE: str = "https://issuer-sandbox.wallet.gov.tw"
    ISSUER_API_KEY: str = "bE3uHSqJzz5GSHVHh6PGpTXPyCIjEtHA"
    VERIFIER_API_BASE: str = "https://verifier-sandbox.wallet.gov.tw"
    VERIFIER_API_KEY: str = "BLrdNlMkYL2vsCvudEsbd7N5tRlX58HS"
    
    # Storage 設定
    DAMAGE_PHOTOS_BUCKET: str = "damage-photos"
    QR_CODES_BUCKET: str = "qr-codes"
    INSPECTION_PHOTOS_BUCKET: str = "inspection-photos"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 忽略額外的環境變數

@lru_cache()
def get_settings() -> Settings:
    return Settings()