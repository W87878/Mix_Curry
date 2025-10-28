#!/usr/bin/env python3
"""
測試 Gmail 發送功能
"""
import asyncio
import sys
import os
from pathlib import Path

# 設定工作目錄
os.chdir(Path(__file__).parent)
sys.path.insert(0, str(Path(__file__).parent))

async def test_gmail():
    """測試發送郵件"""
    try:
        print("🧪 測試 Gmail 發送功能")
        print("="*60)
        
        # 導入發送函數
        from app.services.edm.send_disaster_notification import send_custom_email, SENDER_EMAIL, WORKING_DIR
        
        print(f"✓ 發件人: {SENDER_EMAIL}")
        print(f"✓ 工作目錄: {WORKING_DIR}")
        print(f"✓ 目錄存在: {os.path.exists(WORKING_DIR)}")
        
        # 測試發送
        test_email = "wangyouzhi248@gmail.com"
        subject = "測試郵件 - 驗證碼系統"
        html_content = """
        <html>
        <body>
            <h1>測試郵件</h1>
            <p>這是一封測試郵件，用於驗證 Gmail API 是否正常工作。</p>
            <p><strong>驗證碼：123456</strong></p>
        </body>
        </html>
        """
        
        print(f"\n📧 正在發送測試郵件到: {test_email}")
        
        success = await send_custom_email(
            to_email=test_email,
            subject=subject,
            html_content=html_content
        )
        
        if success:
            print("\n✅ 郵件發送成功！")
        else:
            print("\n❌ 郵件發送失敗")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_gmail())
    sys.exit(0 if result else 1)
