#!/usr/bin/env python3
"""
V2.0 API 測試腳本
測試新的身份驗證、區域管理和通知系統
"""
import requests
import json

BASE_URL = "http://localhost:8080"

def print_response(title, response):
    """美化輸出回應"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    print(f"狀態碼: {response.status_code}")
    try:
        print(f"回應: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"回應: {response.text}")

def main():
    print("🚀 開始測試 V2.0 新功能...")
    
    # 1. 註冊新使用者
    print("\n\n🔹 步驟 1: 註冊災民使用者")
    register_data = {
        "email": "victim@example.com",
        "phone": "0912345678",
        "full_name": "王小明",
        "id_number": "A123456789",
        "role": "applicant"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    print_response("註冊結果", response)
    
    # 2. 登入
    print("\n\n🔹 步驟 2: 使用者登入")
    login_data = {
        "email": "victim@example.com",
        "password": "",  # 目前沒有實作密碼驗證
        "login_type": "password"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print_response("登入結果", response)
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        # 設定 Authorization header
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        # 3. 取得當前使用者資訊
        print("\n\n🔹 步驟 3: 取得當前使用者資訊")
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
        print_response("使用者資訊", response)
        
        # 4. 取得區域列表
        print("\n\n🔹 步驟 4: 取得區域列表")
        response = requests.get(f"{BASE_URL}/api/v1/districts/")
        print_response("區域列表", response)
        
        # 5. 取得通知列表
        print("\n\n🔹 步驟 5: 取得通知列表")
        response = requests.get(f"{BASE_URL}/api/v1/notifications/", headers=headers)
        print_response("通知列表", response)
        
        # 6. 取得未讀通知數量
        print("\n\n🔹 步驟 6: 取得未讀通知數量")
        response = requests.get(f"{BASE_URL}/api/v1/notifications/unread-count", headers=headers)
        print_response("未讀通知數量", response)
        
        print("\n\n" + "="*60)
        print("✅ 測試完成！")
        print("="*60)
        print(f"\n💡 您的 Access Token（24小時有效）:")
        print(f"{access_token}\n")
        print("💡 可以在 Swagger UI 中使用這個 Token 測試其他 API")
        print(f"   訪問: {BASE_URL}/docs")
        print("   點擊右上角 🔒 Authorize 按鈕")
        print(f"   輸入: Bearer {access_token}")
        
    else:
        print("\n❌ 登入失敗，無法繼續測試")

if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ 連線失敗！請確認服務是否在 http://localhost:8080 運行")
        print("   啟動服務: python main.py")
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")

