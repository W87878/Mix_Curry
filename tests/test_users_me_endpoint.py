#!/usr/bin/env python3
"""
測試 /api/v1/users/me 端點
"""
import requests
import sys

# 測試配置
BASE_URL = "http://localhost:8080"
TEST_EMAIL = "test@example.com"

print("=" * 60)
print("測試 /api/v1/users/me 端點")
print("=" * 60)

# 1. 先登入取得 token
print("\n1️⃣ 登入取得 token...")
try:
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "",
            "login_type": "password"
        }
    )
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data.get("access_token")
        print(f"✅ 登入成功，token: {token[:20]}...")
    else:
        print(f"❌ 登入失敗: {login_response.status_code}")
        print(f"   回應: {login_response.text}")
        
        # 嘗試註冊
        print("\n   嘗試註冊新帳號...")
        register_response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json={
                "email": TEST_EMAIL,
                "full_name": "測試使用者",
                "id_number": "A123456789",
                "phone": "0912345678",
                "role": "applicant"
            }
        )
        
        if register_response.status_code in [200, 201]:
            print("   ✅ 註冊成功，重新登入...")
            login_response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": "",
                    "login_type": "password"
                }
            )
            login_data = login_response.json()
            token = login_data.get("access_token")
            print(f"   ✅ 登入成功")
        else:
            print(f"   ❌ 註冊失敗: {register_response.text}")
            sys.exit(1)
            
except Exception as e:
    print(f"❌ 錯誤: {e}")
    sys.exit(1)

# 2. 測試 /api/v1/users/me
print("\n2️⃣ 測試 /api/v1/users/me...")
try:
    response = requests.get(
        f"{BASE_URL}/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    print(f"   狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("   ✅ 成功取得使用者資料")
        print(f"   使用者: {data.get('data', {}).get('email')}")
        print(f"   姓名: {data.get('data', {}).get('full_name')}")
        print(f"   角色: {data.get('data', {}).get('role')}")
    else:
        print(f"   ❌ 失敗")
        print(f"   回應: {response.text}")
        
except Exception as e:
    print(f"   ❌ 錯誤: {e}")
    sys.exit(1)

# 3. 測試沒有 token 的情況
print("\n3️⃣ 測試沒有 token（應該失敗）...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/users/me")
    
    if response.status_code == 401:
        print("   ✅ 正確回傳 401 Unauthorized")
    else:
        print(f"   ⚠️ 預期 401，實際: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ 錯誤: {e}")

print("\n" + "=" * 60)
print("✅ 測試完成")
print("=" * 60)
