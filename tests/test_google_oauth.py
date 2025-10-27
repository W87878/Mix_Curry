#!/usr/bin/env python3
"""
Google OAuth 登入測試腳本
"""
import os
from dotenv import load_dotenv

load_dotenv()

def check_google_oauth_config():
    """檢查 Google OAuth 配置"""
    print("=" * 60)
    print("Google OAuth 配置檢查")
    print("=" * 60)
    
    # 檢查環境變數
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    
    print("\n📋 環境變數檢查：")
    print(f"GOOGLE_CLIENT_ID: {'✅ 已設定' if client_id else '❌ 未設定'}")
    if client_id:
        print(f"  值: {client_id[:20]}...{client_id[-20:] if len(client_id) > 40 else ''}")
    
    print(f"GOOGLE_CLIENT_SECRET: {'✅ 已設定' if client_secret else '❌ 未設定'}")
    if client_secret:
        print(f"  值: {client_secret[:10]}...{client_secret[-10:] if len(client_secret) > 20 else ''}")
    
    print(f"GOOGLE_REDIRECT_URI: {'✅ 已設定' if redirect_uri else '⚠️ 使用預設值'}")
    if redirect_uri:
        print(f"  值: {redirect_uri}")
    else:
        print(f"  預設: http://localhost:8080/api/v1/auth/google/callback")
    
    # 檢查服務
    print("\n🔧 服務檢查：")
    try:
        from app.services.google_oauth import google_oauth_service
        print("✅ Google OAuth 服務已載入")
        
        # 測試產生授權 URL
        try:
            auth_url = google_oauth_service.get_authorization_url()
            print("✅ 可以產生授權 URL")
            print(f"   URL: {auth_url[:80]}...")
        except Exception as e:
            print(f"❌ 無法產生授權 URL: {str(e)}")
            
    except Exception as e:
        print(f"❌ 無法載入 Google OAuth 服務: {str(e)}")
    
    # 檢查路由
    print("\n🛣️ 路由檢查：")
    try:
        from main import app
        google_routes = [
            route for route in app.routes 
            if hasattr(route, 'path') and '/google' in route.path
        ]
        
        if google_routes:
            print(f"✅ 找到 {len(google_routes)} 個 Google 相關路由")
            for route in google_routes:
                methods = ','.join(route.methods) if hasattr(route, 'methods') and route.methods else 'N/A'
                print(f"   {methods:10} {route.path}")
        else:
            print("❌ 未找到 Google 相關路由")
            
    except Exception as e:
        print(f"❌ 無法檢查路由: {str(e)}")
    
    # 總結
    print("\n" + "=" * 60)
    print("📝 設定建議：")
    print("=" * 60)
    
    if not client_id or not client_secret:
        print("\n⚠️ 缺少 Google OAuth 憑證")
        print("請前往 Google Cloud Console 建立 OAuth 憑證：")
        print("1. https://console.cloud.google.com/")
        print("2. 建立 OAuth 用戶端 ID")
        print("3. 將憑證加入 .env 檔案")
        print()
        print("範例：")
        print("GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com")
        print("GOOGLE_CLIENT_SECRET=xxx")
        print("GOOGLE_REDIRECT_URI=http://localhost:8080/api/v1/auth/google/callback")
    else:
        print("\n✅ 配置完成！")
        print("\n下一步：")
        print("1. 啟動伺服器: uvicorn main:app --reload")
        print("2. 開啟測試頁面: http://localhost:8080/static/google_login_test.html")
        print("3. 點擊登入按鈕測試")


def test_oauth_endpoints():
    """測試 OAuth 端點"""
    import httpx
    
    print("\n" + "=" * 60)
    print("🧪 端點測試")
    print("=" * 60)
    
    base_url = "http://localhost:8080"
    
    # 測試登入端點（應該會重定向）
    print("\n測試 GET /api/v1/auth/google/login")
    try:
        response = httpx.get(f"{base_url}/api/v1/auth/google/login", follow_redirects=False)
        if response.status_code in [301, 302, 303, 307, 308]:
            print(f"✅ 正確重定向 (HTTP {response.status_code})")
            print(f"   Location: {response.headers.get('location', 'N/A')[:100]}...")
        else:
            print(f"⚠️ 未預期的狀態碼: {response.status_code}")
    except Exception as e:
        print(f"❌ 錯誤: {str(e)}")
        print("   請確認伺服器正在執行")


if __name__ == "__main__":
    check_google_oauth_config()
    
    # 詢問是否測試端點
    print("\n" + "=" * 60)
    response = input("是否測試 OAuth 端點？(需要伺服器正在執行) [y/N]: ")
    if response.lower() == 'y':
        test_oauth_endpoints()
    
    print("\n✨ 檢查完成")
