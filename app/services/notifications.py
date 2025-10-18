"""
通知系統服務模組
實作簡訊、Email、App 推送通知功能
"""
from datetime import datetime
from typing import Optional, Dict, List, Any
from app.models.database import db_service
import httpx

class NotificationService:
    """通知系統服務"""
    
    # 通知類型定義
    NOTIFICATION_TYPES = {
        "application_submitted": {
            "title": "申請已提交",
            "template": "您的申請案件 {case_no} 已成功提交，我們將盡快審核。",
        },
        "application_approved": {
            "title": "申請已核准",
            "template": "恭喜！您的申請案件 {case_no} 已核准，核准金額：${approved_amount}。",
        },
        "application_rejected": {
            "title": "申請已駁回",
            "template": "很抱歉，您的申請案件 {case_no} 已駁回。駁回原因：{reason}。",
        },
        "supplement_required": {
            "title": "需要補件",
            "template": "您的申請案件 {case_no} 需要補充資料。補件說明：{requirement}。",
        },
        "supplement_completed": {
            "title": "災民已補件",
            "template": "申請案件 {case_no} 的災民已完成補件，請查看。",
        },
        "inspection_scheduled": {
            "title": "現場勘查已安排",
            "template": "您的申請案件 {case_no} 已安排現場勘查。勘查時間：{inspection_date}。",
        },
        "certificate_issued": {
            "title": "憑證已發行",
            "template": "您的補助憑證已發行，請查看 QR Code 並前往發放窗口領取補助。",
        },
        "subsidy_disbursed": {
            "title": "補助已發放",
            "template": "您的補助款 ${amount} 已發放完成。",
        },
        "review_assigned": {
            "title": "新的審核案件",
            "template": "您有一個新的待審核案件 {case_no}，請盡快處理。",
        },
    }
    
    def __init__(self):
        self.sms_enabled = True  # TODO: 從系統設定讀取
        self.email_enabled = True
        self.push_enabled = True
    
    async def create_notification(
        self,
        user_id: str,
        notification_type: str,
        application_id: Optional[str] = None,
        data: Optional[Dict] = None,
        send_immediately: bool = True
    ) -> Dict:
        """
        建立通知
        
        Args:
            user_id: 接收通知的使用者 ID
            notification_type: 通知類型
            application_id: 相關申請案件 ID
            data: 通知資料（用於填充模板）
            send_immediately: 是否立即發送
            
        Returns:
            通知記錄
        """
        if notification_type not in self.NOTIFICATION_TYPES:
            raise ValueError(f"Invalid notification type: {notification_type}")
        
        # 取得通知模板
        template = self.NOTIFICATION_TYPES[notification_type]
        title = template["title"]
        content = template["template"].format(**(data or {}))
        
        # 建立通知記錄
        notification_data = {
            "user_id": user_id,
            "application_id": application_id,
            "notification_type": notification_type,
            "title": title,
            "content": content,
            "action_url": f"/applications/{application_id}" if application_id else None,
            "is_read": False,
        }
        
        notification = db_service.client.table('notifications').insert(
            notification_data
        ).execute()
        
        if notification.data and send_immediately:
            # 立即發送通知
            await self.send_notification(notification.data[0])
        
        return notification.data[0] if notification.data else None
    
    async def send_notification(self, notification: Dict):
        """
        發送通知（透過各種通道）
        
        Args:
            notification: 通知記錄
        """
        user_id = notification['user_id']
        
        # 取得使用者資料
        user = db_service.get_user_by_id(user_id)
        if not user:
            return
        
        notification_id = notification['id']
        update_data = {}
        
        # 發送簡訊
        if self.sms_enabled and user.get('phone'):
            success = await self._send_sms(
                user['phone'],
                notification['content']
            )
            if success:
                update_data['sent_via_sms'] = True
                update_data['sms_sent_at'] = datetime.now().isoformat()
        
        # 發送 Email
        if self.email_enabled and user.get('email'):
            success = await self._send_email(
                user['email'],
                notification['title'],
                notification['content']
            )
            if success:
                update_data['sent_via_email'] = True
                update_data['email_sent_at'] = datetime.now().isoformat()
        
        # 發送 App 推送
        if self.push_enabled:
            success = await self._send_push(
                user_id,
                notification['title'],
                notification['content']
            )
            if success:
                update_data['sent_via_push'] = True
                update_data['push_sent_at'] = datetime.now().isoformat()
        
        # 更新通知記錄
        if update_data:
            db_service.client.table('notifications').update(
                update_data
            ).eq('id', notification_id).execute()
    
    async def _send_sms(self, phone: str, message: str) -> bool:
        """
        發送簡訊（整合簡訊服務商 API）
        
        Args:
            phone: 手機號碼
            message: 簡訊內容
            
        Returns:
            是否成功
        """
        try:
            # TODO: 整合實際的簡訊服務商 API
            # 例如：台灣大哥大簡訊 API、三竹簡訊等
            
            print(f"📱 發送簡訊到 {phone}: {message}")
            
            # 示例：呼叫簡訊 API
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         "https://sms-api.example.com/send",
            #         json={
            #             "phone": phone,
            #             "message": message,
            #             "api_key": settings.SMS_API_KEY
            #         }
            #     )
            #     return response.status_code == 200
            
            return True
        except Exception as e:
            print(f"簡訊發送失敗: {e}")
            return False
    
    async def _send_email(self, email: str, subject: str, content: str) -> bool:
        """
        發送 Email
        
        Args:
            email: 電子郵件地址
            subject: 郵件主旨
            content: 郵件內容
            
        Returns:
            是否成功
        """
        try:
            # TODO: 整合 Email 服務（例如：SendGrid, AWS SES）
            
            print(f"📧 發送 Email 到 {email}: {subject}")
            print(f"   內容: {content}")
            
            # 示例：使用 SMTP
            # import smtplib
            # from email.mime.text import MIMEText
            # 
            # msg = MIMEText(content)
            # msg['Subject'] = subject
            # msg['From'] = settings.SMTP_FROM
            # msg['To'] = email
            # 
            # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            #     server.starttls()
            #     server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            #     server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Email 發送失敗: {e}")
            return False
    
    async def _send_push(self, user_id: str, title: str, body: str) -> bool:
        """
        發送 App 推送通知
        
        Args:
            user_id: 使用者 ID
            title: 通知標題
            body: 通知內容
            
        Returns:
            是否成功
        """
        try:
            # TODO: 整合推送服務（例如：Firebase Cloud Messaging）
            
            print(f"🔔 發送推送通知給使用者 {user_id}: {title}")
            
            # 示例：FCM
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         "https://fcm.googleapis.com/fcm/send",
            #         headers={
            #             "Authorization": f"key={settings.FCM_SERVER_KEY}",
            #             "Content-Type": "application/json"
            #         },
            #         json={
            #             "to": user_fcm_token,
            #             "notification": {
            #                 "title": title,
            #                 "body": body
            #             }
            #         }
            #     )
            #     return response.status_code == 200
            
            return True
        except Exception as e:
            print(f"推送通知發送失敗: {e}")
            return False
    
    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """
        取得使用者的通知列表
        
        Args:
            user_id: 使用者 ID
            unread_only: 是否只取得未讀通知
            limit: 限制數量
            
        Returns:
            通知列表
        """
        query = db_service.client.table('notifications') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .limit(limit)
        
        if unread_only:
            query = query.eq('is_read', False)
        
        result = query.execute()
        return result.data if result.data else []
    
    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """
        標記通知為已讀
        
        Args:
            notification_id: 通知 ID
            user_id: 使用者 ID
            
        Returns:
            是否成功
        """
        try:
            result = db_service.client.table('notifications').update({
                'is_read': True,
                'read_at': datetime.now().isoformat()
            }).eq('id', notification_id).eq('user_id', user_id).execute()
            
            return bool(result.data)
        except Exception as e:
            print(f"標記通知失敗: {e}")
            return False
    
    def mark_all_as_read(self, user_id: str) -> bool:
        """
        標記所有通知為已讀
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            是否成功
        """
        try:
            result = db_service.client.table('notifications').update({
                'is_read': True,
                'read_at': datetime.now().isoformat()
            }).eq('user_id', user_id).eq('is_read', False).execute()
            
            return True
        except Exception as e:
            print(f"標記所有通知失敗: {e}")
            return False
    
    def get_unread_count(self, user_id: str) -> int:
        """
        取得未讀通知數量
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            未讀數量
        """
        try:
            result = db_service.client.table('notifications') \
                .select('id', count='exact') \
                .eq('user_id', user_id) \
                .eq('is_read', False) \
                .execute()
            
            return result.count if result.count else 0
        except Exception as e:
            print(f"取得未讀數量失敗: {e}")
            return 0


# ==========================================
# 通知快捷方法
# ==========================================

async def notify_application_submitted(
    applicant_id: str,
    reviewer_id: str,
    case_no: str,
    application_id: str
):
    """通知：申請已提交"""
    service = NotificationService()
    
    # 通知災民
    await service.create_notification(
        user_id=applicant_id,
        notification_type="application_submitted",
        application_id=application_id,
        data={"case_no": case_no}
    )
    
    # 通知里長
    if reviewer_id:
        await service.create_notification(
            user_id=reviewer_id,
            notification_type="review_assigned",
            application_id=application_id,
            data={"case_no": case_no}
        )


async def notify_supplement_required(
    applicant_id: str,
    case_no: str,
    application_id: str,
    requirement: str
):
    """通知：需要補件"""
    service = NotificationService()
    await service.create_notification(
        user_id=applicant_id,
        notification_type="supplement_required",
        application_id=application_id,
        data={"case_no": case_no, "requirement": requirement}
    )


async def notify_application_approved(
    applicant_id: str,
    case_no: str,
    application_id: str,
    approved_amount: float
):
    """通知：申請已核准"""
    service = NotificationService()
    await service.create_notification(
        user_id=applicant_id,
        notification_type="application_approved",
        application_id=application_id,
        data={"case_no": case_no, "approved_amount": f"{approved_amount:,.0f}"}
    )


async def notify_application_rejected(
    applicant_id: str,
    case_no: str,
    application_id: str,
    reason: str
):
    """通知：申請已駁回"""
    service = NotificationService()
    await service.create_notification(
        user_id=applicant_id,
        notification_type="application_rejected",
        application_id=application_id,
        data={"case_no": case_no, "reason": reason}
    )


# 全域通知服務實例
notification_service = NotificationService()

