#!/usr/bin/env python3
"""
快速 Email 測試 - 直接發送測試郵件
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.edm.send_disaster_notification import DisasterNotificationService

def quick_test():
    """快速測試發送郵件"""
    print("🚀 開始測試郵件發送...")
    
    # 初始化服務
    service = DisasterNotificationService()
    
    # 測試數據 - 使用 UUID 格式（需先執行 create_test_user.py）
    test_data = {
        'recipient_email': 'wangyouzhi248@gmail.com',
        'applicant_name': '王小明',
        'case_no': 'DISASTER-2025-TEST-001',
        'approved_amount': 30000,
        'application_id': '00000000-0000-0000-0000-000000000002',  # 申請 ID
        'user_id': '00000000-0000-0000-0000-000000000001'  # 用戶 ID
    }
    
    print(f"\n📧 收件人: {test_data['recipient_email']}")
    print(f"👤 申請人: {test_data['applicant_name']}")
    print(f"📋 案件編號: {test_data['case_no']}")
    print(f"💰 核准金額: NT$ {test_data['approved_amount']:,}")
    print(f"🆔 測試 UUID: {test_data['application_id']}\n")
    
    # 發送核准通知
    print("📤 正在發送核准通知...")
    success = service.send_approval_notification(**test_data)
    
    if success:
        print("\n✅ 成功！請檢查信箱: wangyouzhi248@gmail.com")
        print("📊 已記錄到 Supabase notifications 表")
    else:
        print("\n❌ 發送失敗，請查看錯誤訊息")
    
    return success

if __name__ == "__main__":
    try:
        quick_test()
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
