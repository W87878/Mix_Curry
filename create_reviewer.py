#!/usr/bin/env python3
"""
快速創建里長測試帳號
"""
import requests

API_BASE = "http://localhost:8080/api/v1"

def create_reviewer():
    print("🏛️ 創建里長測試帳號...")
    
    # 1. 先取得區域 ID
    districts_response = requests.get(f"{API_BASE}/districts/")
    if districts_response.status_code == 200:
        districts = districts_response.json()
        if districts:
            district_id = districts[0]['id']
            district_name = districts[0]['district_name']
            print(f"✓ 區域: {district_name}")
        else:
            print("❌ 沒有可用的區域")
            return
    else:
        print("❌ 無法取得區域列表")
        return
    
    # 2. 創建里長帳號
    reviewer_data = {
        "email": "mayor@tainan.gov.tw",
        "phone": "0912345678",
        "full_name": "王里長",
        "id_number": "B123456789",
        "role": "reviewer",
        "district_id": district_id
    }
    
    register_response = requests.post(
        f"{API_BASE}/auth/register",
        json=reviewer_data
    )
    
    if register_response.status_code == 200:
        print("\n✅ 里長帳號創建成功！")
        print("\n" + "="*50)
        print("📧 登入資訊：")
        print("="*50)
        print(f"Email: {reviewer_data['email']}")
        print(f"姓名: {reviewer_data['full_name']}")
        print(f"區域: {district_name}")
        print("\n💡 使用方式：")
        print(f"   訪問 http://localhost:8080/admin")
        print(f"   輸入 Email: {reviewer_data['email']}")
        print("="*50)
    else:
        error = register_response.json()
        if "已被註冊" in error.get('detail', ''):
            print("\n⚠️ 此帳號已存在，可以直接使用！")
            print("\n" + "="*50)
            print("📧 登入資訊：")
            print("="*50)
            print(f"Email: {reviewer_data['email']}")
            print("\n💡 使用方式：")
            print(f"   訪問 http://localhost:8080/admin")
            print(f"   輸入 Email: {reviewer_data['email']}")
            print("="*50)
        else:
            print(f"\n❌ 創建失敗: {error.get('detail', '未知錯誤')}")

if __name__ == "__main__":
    create_reviewer()

