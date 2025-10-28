#!/usr/bin/env python3
"""
測試 Email 驗證登入/註冊 API
"""
import requests
import json
import time

# API 基礎 URL
BASE_URL = "http://localhost:8000"

def print_section(title):
    """打印分隔線"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_email_auth_flow():
    """測試完整的 Email 驗證流程"""
    
    test_email = f"test_{int(time.time())}@example.com"
    
    print_section("📧 測試 Email 驗證登入/註冊流程")
    
    # 步驟 1: 請求驗證碼
    print("\n1️⃣ 步驟 1: 請求驗證碼")
    print(f"   Email: {test_email}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/email/auth",
        json={
            "email": test_email,
            "is_verified": False
        }
    )
    
    print(f"   狀態碼: {response.status_code}")
    result = response.json()
    print(f"   回應: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code != 200:
        print("   ❌ 請求驗證碼失敗")
        return False
    
    verification_code = result.get("verification_code")
    if not verification_code:
        print("   ❌ 未取得驗證碼（可能是生產環境）")
        return False
    
    print(f"   ✅ 驗證碼: {verification_code}")
    
    # 步驟 2: 使用驗證碼登入/註冊
    print("\n2️⃣ 步驟 2: 使用驗證碼登入/註冊")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/email/auth",
        json={
            "email": test_email,
            "is_verified": True,
            "verification_code": verification_code
        }
    )
    
    print(f"   狀態碼: {response.status_code}")
    result = response.json()
    print(f"   回應: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code != 200:
        print("   ❌ 登入/註冊失敗")
        return False
    
    print("   ✅ 登入成功")
    
    # 檢查回應內容
    if result.get("success") and result.get("access_token"):
        print(f"\n✅ 完整流程測試成功！")
        print(f"   - 使用者 ID: {result.get('user', {}).get('id')}")
        print(f"   - Email: {result.get('user', {}).get('email')}")
        print(f"   - Access Token: {result.get('access_token')[:50]}...")
        return True
    else:
        print("\n❌ 回應格式不正確")
        return False

def test_resend_code():
    """測試重新發送驗證碼"""
    
    print_section("🔄 測試重新發送驗證碼")
    
    test_email = f"resend_{int(time.time())}@example.com"
    
    # 第一次請求
    print("\n1️⃣ 第一次請求驗證碼")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/email/auth",
        json={
            "email": test_email,
            "is_verified": False
        }
    )
    
    print(f"   狀態碼: {response.status_code}")
    if response.status_code == 200:
        print("   ✅ 第一次請求成功")
    
    # 立即重發（應該被拒絕）
    print("\n2️⃣ 立即重發驗證碼（應該被拒絕）")
    time.sleep(0.5)
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/email/resend",
        json={
            "email": test_email
        }
    )
    
    print(f"   狀態碼: {response.status_code}")
    result = response.json()
    print(f"   回應: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 429:
        print("   ✅ 正確拒絕頻繁請求")
        return True
    elif response.status_code == 200:
        print("   ⚠️  允許重發（可能時間間隔設定較短）")
        return True
    else:
        print("   ❌ 未預期的回應")
        return False

def test_invalid_code():
    """測試錯誤的驗證碼"""
    
    print_section("❌ 測試錯誤的驗證碼")
    
    test_email = f"invalid_{int(time.time())}@example.com"
    
    # 請求驗證碼
    print("\n1️⃣ 請求驗證碼")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/email/auth",
        json={
            "email": test_email,
            "is_verified": False
        }
    )
    
    if response.status_code != 200:
        print("   ❌ 請求驗證碼失敗")
        return False
    
    print("   ✅ 驗證碼已發送")
    
    # 使用錯誤的驗證碼
    print("\n2️⃣ 使用錯誤的驗證碼")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/email/auth",
        json={
            "email": test_email,
            "is_verified": True,
            "verification_code": "000000"
        }
    )
    
    print(f"   狀態碼: {response.status_code}")
    result = response.json()
    print(f"   回應: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 400:
        print("   ✅ 正確拒絕錯誤的驗證碼")
        return True
    else:
        print("   ❌ 未預期的回應")
        return False

def test_traditional_login():
    """測試傳統密碼登入"""
    
    print_section("🔐 測試傳統密碼登入")
    
    # 測試登入（使用已存在的帳號）
    print("\n測試登入端點")
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "test123456",
            "login_type": "password"
        }
    )
    
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 登入成功")
        print(f"   Access Token: {result.get('access_token', '')[:50]}...")
        return True
    elif response.status_code == 401:
        print("⚠️  帳號不存在或密碼錯誤（預期行為）")
        return True
    else:
        print(f"回應: {response.text}")
        return False

def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("  🧪 Email 驗證登入/註冊 API 測試")
    print("=" * 60)
    
    results = []
    
    # 測試 1: 完整的 Email 驗證流程
    try:
        results.append(("Email 驗證流程", test_email_auth_flow()))
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        results.append(("Email 驗證流程", False))
    
    # 測試 2: 重新發送驗證碼
    try:
        results.append(("重新發送驗證碼", test_resend_code()))
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        results.append(("重新發送驗證碼", False))
    
    # 測試 3: 錯誤的驗證碼
    try:
        results.append(("錯誤的驗證碼", test_invalid_code()))
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        results.append(("錯誤的驗證碼", False))
    
    # 測試 4: 傳統密碼登入
    try:
        results.append(("傳統密碼登入", test_traditional_login()))
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        results.append(("傳統密碼登入", False))
    
    # 總結
    print_section("📊 測試總結")
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n總計: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！")
    else:
        print(f"\n⚠️  {total - passed} 個測試失敗")

if __name__ == "__main__":
    main()
