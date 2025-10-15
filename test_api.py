"""
API 快速測試腳本
用於測試災民補助申請系統的基本功能
"""
import requests
import json
from datetime import date

# API Base URL
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"

def print_response(title, response):
    """格式化輸出回應"""
    print(f"\n{'='*60}")
    print(f"📌 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(response.text)

def test_health():
    """測試健康檢查"""
    response = requests.get(f"{BASE_URL}/health")
    print_response("健康檢查", response)
    return response.status_code == 200

def test_create_user():
    """測試建立使用者"""
    user_data = {
        "email": "test.user@example.com",
        "phone": "0912345678",
        "full_name": "測試災民",
        "id_number": "A123456789",
        "role": "applicant"
    }
    
    response = requests.post(f"{API_V1}/users/", json=user_data)
    print_response("建立災民使用者", response)
    
    if response.status_code == 201:
        return response.json()['data']['id']
    return None

def test_create_reviewer():
    """測試建立審核員"""
    reviewer_data = {
        "email": "reviewer@example.com",
        "phone": "0987654321",
        "full_name": "測試審核員",
        "id_number": "B987654321",
        "role": "reviewer"
    }
    
    response = requests.post(f"{API_V1}/users/", json=reviewer_data)
    print_response("建立審核員使用者", response)
    
    if response.status_code == 201:
        return response.json()['data']['id']
    return None

def test_create_application(applicant_id):
    """測試建立申請案件"""
    application_data = {
        "applicant_id": applicant_id,
        "applicant_name": "測試災民",
        "id_number": "A123456789",
        "phone": "0912345678",
        "address": "台南市中西區民權路100號",
        "disaster_date": "2025-10-10",
        "disaster_type": "flood",
        "damage_description": "一樓淹水約50公分，客廳家具、電器設備受損嚴重，包括冰箱、洗衣機、沙發等。",
        "damage_location": "台南市中西區民權路100號1樓",
        "subsidy_type": "housing",
        "requested_amount": 50000,
        "estimated_loss": 80000
    }
    
    response = requests.post(f"{API_V1}/applications/", json=application_data)
    print_response("建立申請案件", response)
    
    if response.status_code == 201:
        return response.json()['data']['id'], response.json()['data']['case_no']
    return None, None

def test_get_application(application_id):
    """測試取得申請案件"""
    response = requests.get(f"{API_V1}/applications/{application_id}")
    print_response("取得申請案件詳情", response)

def test_approve_application(application_id, reviewer_id):
    """測試核准申請"""
    params = {
        "reviewer_id": reviewer_id,
        "reviewer_name": "測試審核員",
        "approved_amount": 45000,
        "decision_reason": "經現場勘查，災損情形屬實，核准補助新台幣45,000元整。"
    }
    
    response = requests.post(
        f"{API_V1}/reviews/approve/{application_id}",
        params=params
    )
    print_response("核准申請案件", response)

def test_create_certificate(application_id, reviewer_id):
    """測試建立數位憑證"""
    params = {
        "issued_by": reviewer_id,
        "expires_days": 365
    }
    
    response = requests.post(
        f"{API_V1}/certificates/",
        params={**params, "application_id": application_id}
    )
    print_response("建立數位憑證", response)
    
    if response.status_code == 201:
        return response.json()['data']['certificate_no']
    return None

def test_verify_certificate(certificate_no, reviewer_id):
    """測試驗證憑證"""
    verify_data = {
        "certificate_no": certificate_no,
        "verified_by": reviewer_id
    }
    
    response = requests.post(f"{API_V1}/certificates/verify", json=verify_data)
    print_response("驗證數位憑證", response)

def test_scan_qr_code(certificate_no):
    """測試掃描 QR Code"""
    response = requests.post(f"{API_V1}/certificates/scan/{certificate_no}")
    print_response("掃描 QR Code", response)

def test_get_stats():
    """測試取得統計資料"""
    response = requests.get(f"{API_V1}/stats")
    print_response("系統統計資料", response)

def main():
    """主測試流程"""
    print("\n" + "="*60)
    print("🚀 災民補助申請系統 API 測試")
    print("="*60)
    
    # 1. 健康檢查
    if not test_health():
        print("\n❌ 健康檢查失敗！請確認服務是否正常運行。")
        return
    
    print("\n✅ 健康檢查通過！\n")
    
    # 2. 建立測試使用者
    print("\n📝 第一步：建立測試使用者")
    applicant_id = test_create_user()
    if not applicant_id:
        print("\n⚠️  使用者可能已存在，繼續測試...")
        # 如果已存在，可以手動輸入 ID 或跳過
    
    reviewer_id = test_create_reviewer()
    if not reviewer_id:
        print("\n⚠️  審核員可能已存在，繼續測試...")
    
    # 如果無法建立使用者，詢問是否要輸入現有 ID
    if not applicant_id:
        print("\n請輸入現有的災民 ID（或按 Enter 跳過）：")
        user_input = input().strip()
        if user_input:
            applicant_id = user_input
        else:
            print("\n⚠️  跳過後續測試")
            return
    
    if not reviewer_id:
        print("\n請輸入現有的審核員 ID（或按 Enter 跳過）：")
        user_input = input().strip()
        if user_input:
            reviewer_id = user_input
    
    # 3. 建立申請案件
    print("\n📝 第二步：建立申請案件")
    application_id, case_no = test_create_application(applicant_id)
    if not application_id:
        print("\n❌ 建立申請案件失敗！")
        return
    
    print(f"\n✅ 申請案件建立成功！案件編號：{case_no}")
    
    # 4. 取得申請案件詳情
    print("\n📝 第三步：查詢申請案件")
    test_get_application(application_id)
    
    # 5. 核准申請
    if reviewer_id:
        print("\n📝 第四步：核准申請案件")
        test_approve_application(application_id, reviewer_id)
        
        # 6. 建立數位憑證
        print("\n📝 第五步：建立數位憑證")
        certificate_no = test_create_certificate(application_id, reviewer_id)
        if certificate_no:
            print(f"\n✅ 數位憑證建立成功！憑證編號：{certificate_no}")
            
            # 7. 驗證憑證
            print("\n📝 第六步：驗證數位憑證")
            test_verify_certificate(certificate_no, reviewer_id)
            
            # 8. 掃描 QR Code
            print("\n📝 第七步：模擬掃描 QR Code")
            test_scan_qr_code(certificate_no)
    
    # 9. 取得統計資料
    print("\n📝 最後：查看系統統計")
    test_get_stats()
    
    print("\n" + "="*60)
    print("🎉 測試完成！")
    print("="*60)
    print("\n提示：")
    print("- 可以在瀏覽器開啟 http://localhost:8000/docs 查看完整 API 文件")
    print("- 可以在 Supabase Dashboard 查看資料庫內容")
    print("- 如需測試照片上傳，請使用 Swagger UI 的 /api/v1/photos/upload 端點")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  測試已中斷")
    except requests.exceptions.ConnectionError:
        print("\n\n❌ 無法連接到 API 服務！")
        print("請確認：")
        print("1. FastAPI 服務是否正在運行（python main.py）")
        print("2. 服務是否在 http://localhost:8000 上運行")
    except Exception as e:
        print(f"\n\n❌ 發生錯誤：{str(e)}")

