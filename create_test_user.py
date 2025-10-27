"""
創建測試用戶用於郵件通知測試
"""
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 測試用戶資料
TEST_USER = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "wangyouzhi248@gmail.com",
    "full_name": "王小明",
    "id_number": "A123456789",
    "phone": "0912345678",
    "role": "applicant",
    "is_active": True,
    "is_verified": True
}

# 測試申請案件
TEST_APPLICATION = {
    "id": "00000000-0000-0000-0000-000000000002",
    "case_no": "DISASTER-2025-TEST-001",
    "applicant_id": "00000000-0000-0000-0000-000000000001",
    "applicant_name": "王小明",
    "id_number": "A123456789",
    "phone": "0912345678",
    "address": "台南市中西區民權路一段100號",
    "disaster_date": "2025-01-15",
    "disaster_type": "水災",
    "damage_description": "房屋淹水，家具損毀",
    "damage_location": "台南市中西區民權路一段100號",
    "estimated_loss": 50000.00,
    "subsidy_type": "房屋修繕",
    "requested_amount": 30000.00,
    "status": "approved",
    "approved_amount": 30000.00
}

def create_test_data():
    """創建測試用戶和申請案件"""
    print("🚀 開始創建測試資料...")
    
    # 1. 檢查用戶是否已存在
    try:
        existing_user = supabase.table("users").select("*").eq("id", TEST_USER["id"]).execute()
        if existing_user.data:
            print(f"✅ 測試用戶已存在: {TEST_USER['email']}")
        else:
            # 創建測試用戶
            result = supabase.table("users").insert(TEST_USER).execute()
            print(f"✅ 測試用戶創建成功: {TEST_USER['email']}")
            print(f"   User ID: {TEST_USER['id']}")
    except Exception as e:
        print(f"❌ 創建測試用戶失敗: {e}")
        return False
    
    # 2. 檢查申請案件是否已存在
    try:
        existing_app = supabase.table("applications").select("*").eq("id", TEST_APPLICATION["id"]).execute()
        if existing_app.data:
            print(f"✅ 測試申請案件已存在: {TEST_APPLICATION['case_no']}")
        else:
            # 創建測試申請案件
            result = supabase.table("applications").insert(TEST_APPLICATION).execute()
            print(f"✅ 測試申請案件創建成功: {TEST_APPLICATION['case_no']}")
            print(f"   Application ID: {TEST_APPLICATION['id']}")
    except Exception as e:
        print(f"❌ 創建測試申請案件失敗: {e}")
        return False
    
    print("\n" + "="*50)
    print("📋 測試資料摘要")
    print("="*50)
    print(f"用戶 ID: {TEST_USER['id']}")
    print(f"用戶姓名: {TEST_USER['full_name']}")
    print(f"用戶 Email: {TEST_USER['email']}")
    print(f"申請案件 ID: {TEST_APPLICATION['id']}")
    print(f"案件編號: {TEST_APPLICATION['case_no']}")
    print(f"核准金額: NT$ {TEST_APPLICATION['approved_amount']:,.0f}")
    print("="*50)
    
    return True

def clean_test_data():
    """清理測試資料"""
    print("\n🗑️  清理測試資料...")
    
    try:
        # 刪除通知記錄
        supabase.table("notifications").delete().eq("user_id", TEST_USER["id"]).execute()
        print("✅ 已清理通知記錄")
        
        # 刪除申請案件
        supabase.table("applications").delete().eq("id", TEST_APPLICATION["id"]).execute()
        print("✅ 已清理測試申請案件")
        
        # 刪除測試用戶
        supabase.table("users").delete().eq("id", TEST_USER["id"]).execute()
        print("✅ 已清理測試用戶")
        
    except Exception as e:
        print(f"⚠️  清理資料時發生錯誤: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean_test_data()
    else:
        create_test_data()
        print("\n💡 提示：")
        print("   - 現在可以執行 'python quick_test_email.py' 測試郵件發送")
        print("   - 執行 'python create_test_user.py clean' 可以清理測試資料")
