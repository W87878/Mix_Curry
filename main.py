"""
災民補助申請系統 - FastAPI 主程式
颱風水災受災戶透過數位憑證領取補助
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.settings import get_settings
from app.routers import applications, users, reviews, certificates, photos
from contextlib import asynccontextmanager
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up application...")
    yield
    # Shutdown
    print("Shutting down application...")

# 取得設定
settings = get_settings()

# 建立 FastAPI 應用程式
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## 災民補助申請系統 API
    
    這是一個基於 FastAPI 和 Supabase 的災民補助申請管理系統。
    
    ### 主要功能：
    
    * **使用者管理** - 災民、審核員、管理員的帳號管理
    * **申請案件** - 災民填寫申請表單、上傳災損照片
    * **審核流程** - 審核員審核、現場勘查、核准/駁回
    * **數位憑證** - 產生 QR Code 憑證、驗證、發放補助
    * **照片管理** - 災損照片、現場勘查照片的上傳與管理
    
    ### 技術架構：
    
    * **後端框架**: FastAPI
    * **資料庫**: Supabase (PostgreSQL)
    * **檔案儲存**: Supabase Storage
    * **QR Code**: qrcode + Pillow
    
    ### 開發團隊：
    
    基於台南市政府災民補助申請表單設計
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境請改為特定網域
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(users.router, prefix="/api/v1")
app.include_router(applications.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(certificates.router, prefix="/api/v1")
app.include_router(photos.router, prefix="/api/v1")

# 掛載靜態檔案（如果存在）
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 根路由
@app.get("/")
async def root():
    """API 根路徑"""
    return {
        "message": "歡迎使用災民補助申請系統 API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "api_prefix": "/api/v1",
        "test_page": "/test"
    }

# 測試頁面
@app.get("/test")
async def test_page():
    """API 測試頁面"""
    static_file = os.path.join(os.path.dirname(__file__), "static", "test_api.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    else:
        raise HTTPException(status_code=404, detail="測試頁面不存在")

# 健康檢查
@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

# 統計資料端點
@app.get("/api/v1/stats")
async def get_statistics():
    """取得系統統計資料"""
    try:
        from app.models.database import db_service
        
        # 取得各狀態的案件數量
        pending = db_service.get_applications_by_status("pending", 1000)
        under_review = db_service.get_applications_by_status("under_review", 1000)
        approved = db_service.get_applications_by_status("approved", 1000)
        rejected = db_service.get_applications_by_status("rejected", 1000)
        completed = db_service.get_applications_by_status("completed", 1000)
        
        # 計算總核准金額和已發放金額
        total_approved_amount = sum(float(app.get('approved_amount', 0) or 0) for app in approved + completed)
        total_disbursed_amount = sum(float(app.get('approved_amount', 0) or 0) for app in completed)
        
        stats = {
            "total_applications": len(pending) + len(under_review) + len(approved) + len(rejected) + len(completed),
            "pending_applications": len(pending),
            "under_review_applications": len(under_review),
            "approved_applications": len(approved),
            "rejected_applications": len(rejected),
            "completed_applications": len(completed),
            "total_approved_amount": total_approved_amount,
            "total_disbursed_amount": total_disbursed_amount
        }
        
        return {
            "success": True,
            "message": "統計資料取得成功",
            "data": stats
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"發生錯誤: {str(e)}")

# 全域異常處理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全域異常處理器"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "伺服器發生錯誤",
            "detail": str(exc) if settings.DEBUG else "請聯絡系統管理員"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
