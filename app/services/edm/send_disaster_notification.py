"""
災害補助平台 - Email 通知發送服務
用於發送申請核准/駁回通知給災民
"""
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jinja2
import sys
import base64
import traceback
import datetime
import time
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
from pathlib import Path
from typing import Dict, List, Optional

# 載入環境變數
load_dotenv()

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase 連線設定
SUPABASE_URL: str = os.environ.get('SUPABASE_URL')
SUPABASE_KEY: str = os.environ.get('SUPABASE_SERVICE_ROLE')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gmail 設定
rootdir = Path(__file__).parent.parent

sys.path.append(str(rootdir / 'gmaillib'))
from gmaillib.simplegmail import Gmail

# 使用災害補助專用的 Gmail 帳號
SENDER_EMAIL = os.environ.get('NOTIFICATION_EMAIL', '88wang23@gmail.com')
WORKING_DIR = os.environ.get('GMAIL_PROFILE_DIR', rootdir + '/edm/profiles/disaster')

# 設定模板路徑
TEMPLATE_DIR = Path(__file__).parent / 'templates'


class DisasterNotificationService:
    """災害補助通知服務"""
    
    def __init__(self):
        self.sender_email = SENDER_EMAIL
        self.working_dir = WORKING_DIR
        os.chdir(self.working_dir) if os.path.exists(self.working_dir) else None
        logger.info(f"通知服務初始化 - 發件人: {self.sender_email}")
    
    def send_approval_notification(self, 
                                   recipient_email: str,
                                   applicant_name: str,
                                   case_no: str,
                                   approved_amount: float,
                                   application_id: int) -> bool:
        """
        發送核准通知
        
        Args:
            recipient_email: 收件人 Email
            applicant_name: 申請人姓名
            case_no: 案件編號
            approved_amount: 核准金額
            application_id: 申請 ID
            
        Returns:
            是否發送成功
        """
        try:
            logger.info(f"準備發送核准通知給 {applicant_name} ({recipient_email})")
            
            # 準備郵件內容
            msgRoot = MIMEMultipart('related')
            msgRoot['Subject'] = f'【災害補助核准通知】案件編號: {case_no}'
            msgRoot['From'] = self.sender_email
            msgRoot['To'] = recipient_email
            
            # 準備模板變數
            template_data = {
                'applicant_name': applicant_name,
                'case_no': case_no,
                'approved_amount': f'{approved_amount:,.0f}',
                'notification_date': datetime.datetime.now().strftime('%Y年%m月%d日'),
                'application_id': application_id
            }
            
            # 渲染 HTML 模板
            html_content = self._render_template('approval_notification.html', template_data)
            
            msgHtml = MIMEText(html_content, 'html', 'utf-8')
            msgRoot.attach(msgHtml)
            msgRoot.add_header('reply-to', 'support@disaster-relief.gov.tw')
            
            # 發送郵件
            gmail = Gmail()
            raw = {"raw": base64.urlsafe_b64encode(msgRoot.as_string().encode()).decode()}
            gmail.send_raw(raw)
            
            logger.info(f"核准通知發送成功: {recipient_email}")
            
            # 記錄到資料庫
            self._log_notification(
                email=recipient_email,
                notification_type='approval',
                case_no=case_no,
                application_id=application_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"發送核准通知失敗: {e}")
            traceback.print_exc()
            return False
    
    def send_rejection_notification(self,
                                    recipient_email: str,
                                    applicant_name: str,
                                    case_no: str,
                                    rejection_reason: str,
                                    application_id: int) -> bool:
        """
        發送駁回通知
        
        Args:
            recipient_email: 收件人 Email
            applicant_name: 申請人姓名
            case_no: 案件編號
            rejection_reason: 駁回原因
            application_id: 申請 ID
            
        Returns:
            是否發送成功
        """
        try:
            logger.info(f"準備發送駁回通知給 {applicant_name} ({recipient_email})")
            
            # 準備郵件內容
            msgRoot = MIMEMultipart('related')
            msgRoot['Subject'] = f'【災害補助審核結果通知】案件編號: {case_no}'
            msgRoot['From'] = self.sender_email
            msgRoot['To'] = recipient_email
            
            # 準備模板變數
            template_data = {
                'applicant_name': applicant_name,
                'case_no': case_no,
                'rejection_reason': rejection_reason,
                'notification_date': datetime.datetime.now().strftime('%Y年%m月%d日'),
                'application_id': application_id
            }
            
            # 渲染 HTML 模板
            html_content = self._render_template('rejection_notification.html', template_data)
            
            msgHtml = MIMEText(html_content, 'html', 'utf-8')
            msgRoot.attach(msgHtml)
            msgRoot.add_header('reply-to', 'support@disaster-relief.gov.tw')
            
            # 發送郵件
            gmail = Gmail()
            raw = {"raw": base64.urlsafe_b64encode(msgRoot.as_string().encode()).decode()}
            gmail.send_raw(raw)
            
            logger.info(f"駁回通知發送成功: {recipient_email}")
            
            # 記錄到資料庫
            self._log_notification(
                email=recipient_email,
                notification_type='rejection',
                case_no=case_no,
                application_id=application_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"發送駁回通知失敗: {e}")
            traceback.print_exc()
            return False
    
    def _render_template(self, template_name: str, data: Dict) -> str:
        """渲染 Jinja2 模板"""
        template_loader = jinja2.FileSystemLoader(searchpath=str(TEMPLATE_DIR))
        template_env = jinja2.Environment(loader=template_loader)
        template = template_env.get_template(template_name)
        return template.render(**data)
    
    def _log_notification(self, 
                         email: str, 
                         notification_type: str,
                         case_no: str,
                         application_id: int):
        """記錄通知發送歷史到 Supabase"""
        try:
            # 檢查是否已存在相同通知
            response = supabase.table('notification_log').select('id') \
                .eq('email', email) \
                .eq('application_id', application_id) \
                .eq('notification_type', notification_type) \
                .execute()
            
            if response.data:
                logger.info(f"通知已存在，跳過記錄: {email} - {notification_type}")
                return
            
            # 插入新記錄
            supabase.table('notification_log').insert({
                'email': email,
                'notification_type': notification_type,
                'case_no': case_no,
                'application_id': application_id,
                'sent_at': datetime.datetime.now().isoformat()
            }).execute()
            
            logger.info(f"通知記錄已儲存: {email} - {notification_type}")
            
        except Exception as e:
            logger.error(f"儲存通知記錄失敗: {e}")
            traceback.print_exc()
    
    def get_pending_notifications(self) -> List[Dict]:
        """
        從 Supabase 獲取待發送的通知
        
        Returns:
            待通知的申請列表
        """
        try:
            # 查詢已核准但未發送通知的申請
            response = supabase.table('applications') \
                .select('id, case_no, applicant_name, applicant_id, approved_amount, status, users!applicants(email)') \
                .in_('status', ['approved', 'rejected']) \
                .execute()
            
            pending = []
            for app in response.data:
                # 檢查是否已發送通知
                log_check = supabase.table('notification_log') \
                    .select('id') \
                    .eq('application_id', app['id']) \
                    .eq('notification_type', app['status']) \
                    .execute()
                
                if not log_check.data:
                    # 提取用戶 email
                    user_email = app.get('users', {}).get('email') if app.get('users') else None
                    if user_email:
                        pending.append({
                            'application_id': app['id'],
                            'case_no': app['case_no'],
                            'applicant_name': app['applicant_name'],
                            'email': user_email,
                            'status': app['status'],
                            'approved_amount': app.get('approved_amount')
                        })
            
            logger.info(f"找到 {len(pending)} 筆待發送通知")
            return pending
            
        except Exception as e:
            logger.error(f"獲取待通知列表失敗: {e}")
            traceback.print_exc()
            return []
    
    def process_pending_notifications(self, delay_seconds: int = 5):
        """
        批次處理待發送的通知
        
        Args:
            delay_seconds: 每封郵件之間的延遲秒數
        """
        pending_list = self.get_pending_notifications()
        
        for notification in pending_list:
            try:
                if notification['status'] == 'approved':
                    success = self.send_approval_notification(
                        recipient_email=notification['email'],
                        applicant_name=notification['applicant_name'],
                        case_no=notification['case_no'],
                        approved_amount=notification['approved_amount'],
                        application_id=notification['application_id']
                    )
                elif notification['status'] == 'rejected':
                    # 獲取駁回原因
                    review = supabase.table('reviews') \
                        .select('rejection_reason') \
                        .eq('application_id', notification['application_id']) \
                        .order('created_at', desc=True) \
                        .limit(1) \
                        .execute()
                    
                    rejection_reason = review.data[0]['rejection_reason'] if review.data else '不符合申請資格'
                    
                    success = self.send_rejection_notification(
                        recipient_email=notification['email'],
                        applicant_name=notification['applicant_name'],
                        case_no=notification['case_no'],
                        rejection_reason=rejection_reason,
                        application_id=notification['application_id']
                    )
                
                if success:
                    logger.info(f"✅ 通知發送成功: {notification['case_no']}")
                    time.sleep(delay_seconds)
                else:
                    logger.error(f"❌ 通知發送失敗: {notification['case_no']}")
                    
            except Exception as e:
                logger.error(f"處理通知時發生錯誤: {e}")
                traceback.print_exc()


def main():
    """主程式 - 執行批次通知發送"""
    logger.info("=" * 50)
    logger.info("災害補助通知系統啟動")
    logger.info("=" * 50)
    
    service = DisasterNotificationService()
    service.process_pending_notifications(delay_seconds=5)
    
    logger.info("=" * 50)
    logger.info("批次通知發送完成")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
