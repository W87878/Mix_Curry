#!/usr/bin/env python3
"""
簡單的 Email 發送測試腳本
用於測試災害補助通知系統的郵件功能
"""

import sys
import os
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.edm.send_disaster_notification import DisasterNotificationService
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_send_email():
    """測試發送 Email"""
    print("\n" + "="*60)
    print("🧪 災害補助通知系統 - Email 發送測試")
    print("="*60 + "\n")
    
    # 初始化服務
    try:
        service = DisasterNotificationService()
        logger.info("✅ 服務初始化成功")
    except Exception as e:
        logger.error(f"❌ 服務初始化失敗: {e}")
        return False
    
    # 獲取收件人 Email
    recipient_email = input("📧 請輸入測試收件人 Email (預設: 88wang23@gmail.com): ").strip()
    if not recipient_email:
        recipient_email = "88wang23@gmail.com"
    
    print("\n請選擇測試類型：")
    print("1. 核准通知")
    print("2. 駁回通知")
    
    choice = input("\n請輸入選項 (1 或 2): ").strip()
    
    if choice == "1":
        # 測試核准通知
        print("\n📤 準備發送核准通知...")
        test_data = {
            'recipient_email': recipient_email,
            'applicant_name': '測試用戶',
            'case_no': 'TEST-2025-001',
            'approved_amount': 50000,
            'application_id': 999
        }
        
        print(f"\n收件人: {test_data['recipient_email']}")
        print(f"申請人: {test_data['applicant_name']}")
        print(f"案件編號: {test_data['case_no']}")
        print(f"核准金額: NT$ {test_data['approved_amount']:,}")
        
        confirm = input("\n確定要發送嗎? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ 取消發送")
            return False
        
        try:
            success = service.send_approval_notification(**test_data)
            
            if success:
                print("\n" + "="*60)
                print("✅ 核准通知發送成功！")
                print("="*60)
                print(f"\n請檢查 {recipient_email} 的信箱")
                return True
            else:
                print("\n❌ 核准通知發送失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 發送失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    elif choice == "2":
        # 測試駁回通知
        print("\n📤 準備發送駁回通知...")
        test_data = {
            'recipient_email': recipient_email,
            'applicant_name': '測試用戶',
            'case_no': 'TEST-2025-002',
            'rejection_reason': '測試駁回原因：申請文件不齊全',
            'application_id': 998
        }
        
        print(f"\n收件人: {test_data['recipient_email']}")
        print(f"申請人: {test_data['applicant_name']}")
        print(f"案件編號: {test_data['case_no']}")
        print(f"駁回原因: {test_data['rejection_reason']}")
        
        confirm = input("\n確定要發送嗎? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ 取消發送")
            return False
        
        try:
            success = service.send_rejection_notification(**test_data)
            
            if success:
                print("\n" + "="*60)
                print("✅ 駁回通知發送成功！")
                print("="*60)
                print(f"\n請檢查 {recipient_email} 的信箱")
                return True
            else:
                print("\n❌ 駁回通知發送失敗")
                return False
                
        except Exception as e:
            logger.error(f"❌ 發送失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    else:
        print("❌ 無效的選項")
        return False

if __name__ == "__main__":
    try:
        test_send_email()
    except KeyboardInterrupt:
        print("\n\n⚠️  測試已取消")
    except Exception as e:
        logger.error(f"❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
