#!/usr/bin/env python3
"""
Email 驗證登入流程測試腳本
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_email_verification_flow():
    """測試完整的 Email 驗證登入流程"""
    
    print("\n" + "="*60)
    print("🧪 測試 Email 驗證登入流程")
    print("="*60)
    
    # 測試 Email
    test_email = "test@example.com"
    
    # ========================================
    # 步驟 1：發送驗證碼
    # ========================================
    print("\n📤 步驟 1：發送驗證碼")
    print(f"   Email: {test_email}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/email/auth",
        json={
            "email": test_email,
            "is_verified": False
        }
    )
    
    print(f"   狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功！")
        print(f"   驗證碼: {data['verification_code']}")
        verification_code = data['verification_code']
    else:
        print(f"   ❌ 失敗: {response.text}")
        return
    
    # ========================================
    # 步驟 2：前端驗證（正確的驗證碼）
    # ========================================
    print("\n✅ 步驟 2：使用正確的驗證碼登入")
    print(f"   驗證碼: {verification_code}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": test_email,
            "login_type": "password",
            "verify": True  # 前端驗證成功
        }
    )
    
    print(f"   狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 登入成功！")
        print(f"   用戶 ID: {data['user']['id']}")
        print(f"   Email: {data['user']['email']}")
        print(f"   Access Token: {data['access_token'][:50]}...")
    else:
        print(f"   ❌ 失敗: {response.text}")
    
    # ========================================
    # 步驟 3：測試錯誤的驗證碼（前端驗證失敗）
    # ========================================
    print("\n❌ 步驟 3：使用錯誤的驗證碼（前端驗證失敗）")
    
    # 先發送新的驗證碼
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/email/auth",
        json={
            "email": "test2@example.com",
            "is_verified": False
        }
    )
    
    # 用 verify=False 登入（前端比對失敗）
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": "test2@example.com",
            "login_type": "password",
            "verify": False  # 前端驗證失敗
        }
    )
    
    print(f"   狀態碼: {response.status_code}")
    
    if response.status_code == 400:
        print(f"   ✅ 正確返回錯誤（預期行為）")
        print(f"   錯誤訊息: {response.json()['detail']}")
    else:
        print(f"   ❌ 應該返回 400 錯誤")
    
    # ========================================
    # 步驟 4：測試重新發送驗證碼
    # ========================================
    print("\n🔄 步驟 4：測試重新發送驗證碼")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/email/resend",
        json={
            "email": test_email
        }
    )
    
    print(f"   狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ 成功！")
        print(f"   新驗證碼: {data['verification_code']}")
    else:
        print(f"   ❌ 失敗: {response.text}")
    
    print("\n" + "="*60)
    print("✅ 測試完成！")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        test_email_verification_flow()
    except requests.exceptions.ConnectionError:
        print("\n❌ 無法連接到伺服器")
        print("請確認伺服器正在運行:")
        print("  uvicorn main:app --reload --port 8080\n")
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}\n")
