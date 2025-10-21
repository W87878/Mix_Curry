from fastapi import APIRouter
from app.settings import get_settings

router = APIRouter(prefix="/config", tags=["config"])

@router.get("/frontend")
async def get_frontend_config():
    """提供前端所需的配置資訊"""
    settings = get_settings()
    
    # 只提供前端需要的配置，不暴露敏感資訊
    return {
        "api_base_url": settings.API_BASE_URL,
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }
