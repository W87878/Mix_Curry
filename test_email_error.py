#!/usr/bin/env python3
"""
測試 Email 驗證錯誤
"""
import asyncio
import sys
from pathlib import Path

# 添加專案根目錄
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_send_email():
    """測試發送驗證郵件"""
    try:
        print("🧪 測試 Email 驗證功能")
        print("="*60)
        
        # 導入必要的模組
        from app.services.email_verification import send_verification_email, EmailVerificationService
        
        # 生成驗證碼
        test_email = "wangyouzhi248@gmail.com"
        code = EmailVerificationService.create_verification_code(test_email)
        
        print(f"\n✓ 驗證碼已生成: {code}")
        print(f"✓ 目標 Email: {test_email}")
        
        # 嘗試發送郵件
        print(f"\n📧 正在發送驗證郵件...")
        success = await send_verification_email(
            email=test_email,
            code=code,
            user_name="測試使用者"
        )
        
        if success:
            print("✅ 郵件發送成功！")
        else:
            print("❌ 郵件發送失敗")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_send_email())
    sys.exit(0 if result else 1)
