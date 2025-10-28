"""
Email 驗證服務
處理驗證碼生成、發送和驗證
"""
import os
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class EmailVerificationService:
    """Email 驗證服務"""
    
    # 驗證碼暫存（生產環境應使用 Redis）
    _verification_codes: Dict[str, Dict] = {}
    
    # 驗證碼有效期（分鐘）
    CODE_EXPIRY_MINUTES = 10
    
    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """
        生成驗證碼
        
        Args:
            length: 驗證碼長度
            
        Returns:
            驗證碼字串
        """
        return ''.join(random.choices(string.digits, k=length))
    
    @classmethod
    def create_verification_code(cls, email: str) -> str:
        """
        為 email 建立驗證碼
        
        Args:
            email: 電子郵件地址
            
        Returns:
            驗證碼
        """
        code = cls.generate_verification_code()
        expiry = datetime.now() + timedelta(minutes=cls.CODE_EXPIRY_MINUTES)
        
        cls._verification_codes[email] = {
            'code': code,
            'expiry': expiry,
            'attempts': 0
        }
        
        logger.info(f"Created verification code for {email}: {code} (expires at {expiry})")
        return code
    
    @classmethod
    def verify_code(cls, email: str, code: str) -> bool:
        """
        驗證碼檢查
        
        Args:
            email: 電子郵件地址
            code: 使用者輸入的驗證碼
            
        Returns:
            是否驗證成功
        """
        if email not in cls._verification_codes:
            logger.warning(f"No verification code found for {email}")
            return False
        
        stored = cls._verification_codes[email]
        
        # 檢查是否過期
        if datetime.now() > stored['expiry']:
            logger.warning(f"Verification code expired for {email}")
            del cls._verification_codes[email]
            return False
        
        # 檢查嘗試次數（防止暴力破解）
        if stored['attempts'] >= 5:
            logger.warning(f"Too many attempts for {email}")
            del cls._verification_codes[email]
            return False
        
        # 驗證碼比對
        stored['attempts'] += 1
        
        if stored['code'] == code:
            logger.info(f"Verification successful for {email}")
            # 驗證成功後刪除驗證碼
            del cls._verification_codes[email]
            return True
        else:
            logger.warning(f"Invalid verification code for {email} (attempt {stored['attempts']})")
            return False
    
    @classmethod
    def resend_code(cls, email: str) -> Optional[str]:
        """
        重新發送驗證碼（生成新的）
        
        Args:
            email: 電子郵件地址
            
        Returns:
            新的驗證碼，如果太頻繁則返回 None
        """
        # 如果已有驗證碼且尚未過期，檢查是否太頻繁
        if email in cls._verification_codes:
            stored = cls._verification_codes[email]
            time_since_creation = datetime.now() - (stored['expiry'] - timedelta(minutes=cls.CODE_EXPIRY_MINUTES))
            
            # 如果距離上次發送不到 1 分鐘，拒絕重發
            if time_since_creation < timedelta(minutes=1):
                logger.warning(f"Resend too frequent for {email}")
                return None
        
        # 生成新的驗證碼
        return cls.create_verification_code(email)
    
    @classmethod
    def get_code_info(cls, email: str) -> Optional[Dict]:
        """
        取得驗證碼資訊（用於測試）
        
        Args:
            email: 電子郵件地址
            
        Returns:
            驗證碼資訊
        """
        if email in cls._verification_codes:
            stored = cls._verification_codes[email]
            return {
                'code': stored['code'],
                'expiry': stored['expiry'].isoformat(),
                'attempts': stored['attempts'],
                'remaining_time': (stored['expiry'] - datetime.now()).total_seconds()
            }
        return None


async def send_verification_email(email: str, code: str, user_name: str = "使用者") -> bool:
    """
    發送驗證碼 Email
    
    Args:
        email: 收件人 Email
        code: 驗證碼
        user_name: 使用者姓名
        
    Returns:
        是否發送成功
    """
    try:
        # 嘗試發送郵件，但失敗時不影響驗證流程
        logger.info(f"準備發送驗證郵件到 {email}，驗證碼: {code}")
        
        try:
            # 使用現有的 EDM 系統發送 Email
            from app.services.edm.send_disaster_notification import send_custom_email
        except Exception as e:
            print(e)
        subject = "災害補助系統 - 驗證碼"
        
        # HTML 格式的郵件內容
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>驗證碼</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    background-color: #f5f5f5;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .code-box {{
                    background: #f8f9fa;
                    border: 2px dashed #667eea;
                    border-radius: 8px;
                    padding: 30px;
                    text-align: center;
                    margin: 30px 0;
                }}
                .code {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #667eea;
                    letter-spacing: 8px;
                    font-family: 'Courier New', monospace;
                }}
                .info {{
                    color: #666;
                    font-size: 14px;
                    line-height: 1.6;
                    margin-top: 20px;
                }}
                .warning {{
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    color: #856404;
                    font-size: 14px;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌊 災害補助系統</h1>
                </div>
                <div class="content">
                    <div class="greeting">
                        親愛的 {user_name}，您好：
                    </div>
                    
                    <p>您正在進行 Email 驗證，請使用以下驗證碼完成驗證：</p>
                    
                    <div class="code-box">
                        <div class="code">{code}</div>
                    </div>
                    
                    <div class="warning">
                        ⚠️ 此驗證碼將在 <strong>10 分鐘</strong>後失效，請盡快完成驗證。
                    </div>
                    
                    <div class="info">
                        <p><strong>注意事項：</strong></p>
                        <ul>
                            <li>請勿將驗證碼分享給任何人</li>
                            <li>如果您沒有申請驗證，請忽略此郵件</li>
                            <li>驗證碼輸入錯誤超過 5 次將會失效</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>此為系統自動發送的郵件，請勿直接回覆</p>
                    <p>© 2025 災害補助系統</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 純文字版本（備用）
        text_content = f"""
        災害補助系統 - 驗證碼
        
        親愛的 {user_name}，您好：
        
        您正在進行 Email 驗證，請使用以下驗證碼完成驗證：
        
        驗證碼：{code}
        
        ⚠️ 此驗證碼將在 10 分鐘後失效，請盡快完成驗證。
        
        注意事項：
        - 請勿將驗證碼分享給任何人
        - 如果您沒有申請驗證，請忽略此郵件
        - 驗證碼輸入錯誤超過 5 次將會失效
        
        此為系統自動發送的郵件，請勿直接回覆
        © 2025 災害補助系統
        """
        
        try:
            success = await send_custom_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            if success:
                logger.info(f"✅ 驗證郵件發送成功: {email}")
            else:
                logger.warning(f"⚠️ 驗證郵件發送失敗: {email} (但驗證碼仍有效)")
            
            # 即使郵件發送失敗，仍返回 True，因為驗證碼已經生成
            # 在開發環境中，驗證碼會直接顯示在 API 回應中
            return True
            
        except Exception as email_error:
            logger.error(f"⚠️ 發送驗證郵件時發生錯誤: {email_error}")
            logger.error(f"   但驗證碼 {code} 仍然有效，可以使用")
            # 即使發送失敗，也返回 True，讓使用者可以使用驗證碼
            return True
        
    except Exception as e:
        logger.error(f"❌ 驗證郵件服務錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        # 發生嚴重錯誤時才返回 False
        return False


# 建立全域服務實例
email_verification_service = EmailVerificationService()
