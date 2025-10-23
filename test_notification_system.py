#!/usr/bin/env python3
"""
災害補助通知系統測試腳本
測試 Email 發送功能是否正常
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.services.edm.send_disaster_notification import DisasterNotificationService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_approval_notification():
    """測試核准通知"""
    logger.info("=" * 50)
    logger.info("測試核准通知發送")
    logger.info("=" * 50)
    
    service = DisasterNotificationService()
    
    # 測試資料
    test_data = {
        'recipient_email': 'test@example.com',  # 請改為您的測試 Email
        'applicant_name': '測試用戶',
        'case_no': 'TEST-2025-001',
        'approved_amount': 50000,
        'application_id': 999
    }
    
    logger.info(f"準備發送測試通知到: {test_data['recipient_email']}")
    
    success = service.send_approval_notification(**test_data)
    
    if success:
        logger.info("✅ 核准通知測試成功")
    else:
        logger.error("❌ 核准通知測試失敗")
    
    return success

def test_rejection_notification():
    """測試駁回通知"""
    logger.info("=" * 50)
    logger.info("測試駁回通知發送")
    logger.info("=" * 50)
    
    service = DisasterNotificationService()
    
    # 測試資料
    test_data = {
        'recipient_email': 'test@example.com',  # 請改為您的測試 Email
        'applicant_name': '測試用戶',
        'case_no': 'TEST-2025-002',
        'rejection_reason': '這是測試駁回通知',
        'application_id': 998
    }
    
    logger.info(f"準備發送測試通知到: {test_data['recipient_email']}")
    
    success = service.send_rejection_notification(**test_data)
    
    if success:
        logger.info("✅ 駁回通知測試成功")
    else:
        logger.error("❌ 駁回通知測試失敗")
    
    return success

def test_pending_notifications():
    """測試獲取待發送通知"""
    logger.info("=" * 50)
    logger.info("測試獲取待發送通知列表")
    logger.info("=" * 50)
    
    service = DisasterNotificationService()
    
    pending = service.get_pending_notifications()
    
    logger.info(f"找到 {len(pending)} 筆待發送通知")
    
    for notification in pending[:5]:  # 只顯示前 5 筆
        logger.info(f"  - {notification['case_no']}: {notification['applicant_name']} ({notification['email']})")
    
    return True

def main():
    """主程式"""
    print("\n🧪 災害補助通知系統測試")
    print("=" * 60)
    
    choice = input("""
請選擇測試項目：
1. 測試核准通知
2. 測試駁回通知  
3. 測試獲取待發送通知列表
4. 執行所有測試
5. 退出

請輸入選項 (1-5): """)
    
    if choice == '1':
        test_approval_notification()
    elif choice == '2':
        test_rejection_notification()
    elif choice == '3':
        test_pending_notifications()
    elif choice == '4':
        test_pending_notifications()
        print("\n等待 3 秒...\n")
        import time
        time.sleep(3)
        test_approval_notification()
        time.sleep(3)
        test_rejection_notification()
    elif choice == '5':
        print("退出測試")
        return
    else:
        print("無效的選項")
        return
    
    print("\n✅ 測試完成！")

if __name__ == "__main__":
    main()
