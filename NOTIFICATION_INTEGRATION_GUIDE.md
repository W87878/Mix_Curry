# 🔔 通知系統整合指南

## 快速整合到現有審核流程

### 1. 在審核 API 中整合

編輯 `/app/routers/reviews.py`，在審核通過/駁回後自動發送通知：

```python
from app.services.edm.send_disaster_notification import DisasterNotificationService

# 在檔案開頭初始化服務
notification_service = DisasterNotificationService()

@router.post("/approve/{application_id}")
async def approve_application(
    application_id: int,
    approved_amount: float,
    current_user: dict = Depends(require_reviewer)
):
    # ...原有的審核邏輯...
    
    # 更新申請狀態為已核准
    # ...
    
    # 🆕 發送核准通知
    try:
        # 取得申請人資料
        app_response = supabase.table('applications')\
            .select('*, users!applicants(email)')\
            .eq('id', application_id)\
            .single()\
            .execute()
        
        if app_response.data:
            app = app_response.data
            user_email = app['users']['email']
            
            # 發送通知
            notification_service.send_approval_notification(
                recipient_email=user_email,
                applicant_name=app['applicant_name'],
                case_no=app['case_no'],
                approved_amount=approved_amount,
                application_id=application_id
            )
            logger.info(f"✉️ 核准通知已發送到 {user_email}")
    except Exception as e:
        logger.error(f"發送通知失敗: {e}")
        # 不影響審核流程，只記錄錯誤
    
    return {"success": True, "message": "審核通過並已發送通知"}


@router.post("/reject/{application_id}")
async def reject_application(
    application_id: int,
    rejection_reason: str,
    current_user: dict = Depends(require_reviewer)
):
    # ...原有的駁回邏輯...
    
    # 更新申請狀態為已駁回
    # ...
    
    # 🆕 發送駁回通知
    try:
        # 取得申請人資料
        app_response = supabase.table('applications')\
            .select('*, users!applicants(email)')\
            .eq('id', application_id)\
            .single()\
            .execute()
        
        if app_response.data:
            app = app_response.data
            user_email = app['users']['email']
            
            # 發送通知
            notification_service.send_rejection_notification(
                recipient_email=user_email,
                applicant_name=app['applicant_name'],
                case_no=app['case_no'],
                rejection_reason=rejection_reason,
                application_id=application_id
            )
            logger.info(f"✉️ 駁回通知已發送到 {user_email}")
    except Exception as e:
        logger.error(f"發送通知失敗: {e}")
        # 不影響審核流程，只記錄錯誤
    
    return {"success": True, "message": "已駁回並發送通知"}
```

### 2. 創建通知記錄表

在 Supabase 執行以下 SQL：

```sql
-- 創建通知記錄表
CREATE TABLE IF NOT EXISTS notification_log (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    case_no VARCHAR(50) NOT NULL,
    application_id BIGINT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 索引
    INDEX idx_notification_email (email),
    INDEX idx_notification_app_id (application_id),
    INDEX idx_notification_type (notification_type),
    
    -- 外鍵
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
);

-- 防止重複發送的唯一約束
CREATE UNIQUE INDEX idx_unique_notification 
ON notification_log (application_id, notification_type);

-- 註解
COMMENT ON TABLE notification_log IS '通知發送記錄表';
COMMENT ON COLUMN notification_log.notification_type IS '通知類型: approval, rejection';
COMMENT ON COLUMN notification_log.case_no IS '案件編號';
```

### 3. 設定自動化批次處理（可選）

如果想要系統自動掃描並發送通知，可以使用 cron：

#### 使用 cron (Linux/Mac)

```bash
# 編輯 crontab
crontab -e

# 每小時執行一次
0 * * * * cd /Users/steve.wang/Mix_Curry && python app/services/edm/send_disaster_notification.py >> /var/log/disaster-notifications.log 2>&1
```

#### 使用 systemd timer (Linux)

創建 `/etc/systemd/system/disaster-notifications.service`:

```ini
[Unit]
Description=災害補助通知發送服務
After=network.target

[Service]
Type=oneshot
User=your_user
WorkingDirectory=/Users/steve.wang/Mix_Curry
ExecStart=/usr/bin/python3 app/services/edm/send_disaster_notification.py
StandardOutput=append:/var/log/disaster-notifications.log
StandardError=append:/var/log/disaster-notifications.log

[Install]
WantedBy=multi-user.target
```

創建 `/etc/systemd/system/disaster-notifications.timer`:

```ini
[Unit]
Description=災害補助通知發送定時器
Requires=disaster-notifications.service

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

啟用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable disaster-notifications.timer
sudo systemctl start disaster-notifications.timer
```

### 4. 測試整合

```bash
# 執行測試腳本
python test_notification_system.py

# 或直接測試批次處理
python app/services/edm/send_disaster_notification.py
```

### 5. 監控和日誌

```bash
# 查看通知發送日誌
tail -f /var/log/disaster-notifications.log

# 查看最近的錯誤
grep ERROR /var/log/disaster-notifications.log | tail -20

# 查看發送統計
python -c "
from supabase import create_client
import os
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE'))
result = supabase.table('notification_log').select('notification_type').execute()
print(f'總共發送: {len(result.data)} 封通知')
"
```

## 🎯 最佳實踐

### 1. 錯誤處理

- ✅ 通知發送失敗不應影響主要業務流程
- ✅ 記錄所有錯誤到日誌
- ✅ 可以設定重試機制

### 2. 效能優化

- ✅ 批次發送時加入延遲（避免被封鎖）
- ✅ 限制每次處理的數量
- ✅ 使用非同步發送（如果需要）

### 3. 安全性

- ✅ 不要在 Email 中包含敏感資訊
- ✅ 驗證收件人 Email 格式
- ✅ 提供取消訂閱選項

### 4. 用戶體驗

- ✅ Email 內容清晰易懂
- ✅ 提供明確的下一步操作指引
- ✅ 包含客服聯絡資訊

## 📊 監控指標

建議追蹤以下指標：

1. **發送成功率**
   - 成功發送數 / 總嘗試發送數
   
2. **平均發送時間**
   - 從審核通過到發送完成的時間

3. **退信率**
   - 無效 Email 或被拒絕的比例

4. **用戶互動率**
   - 點擊 Email 中連結的比例

## 🔧 故障排除

### 問題 1：通知沒有發送

**檢查項目：**
- [ ] 確認 Gmail API 認證正確
- [ ] 檢查環境變數設定
- [ ] 查看錯誤日誌
- [ ] 驗證收件人 Email 格式

### 問題 2：重複發送

**解決方案：**
- notification_log 表的唯一約束會防止重複
- 檢查是否有多個程序同時執行

### 問題 3：發送速度太慢

**解決方案：**
- 減少每封 Email 之間的延遲
- 使用多線程（注意 Gmail API 限制）
- 考慮使用專業 Email 服務（如 SendGrid）

## 🚀 進階功能

### 1. 整合簡訊通知

```python
# 可以擴展服務支援簡訊
def send_sms_notification(phone: str, message: str):
    # 使用台灣簡訊服務商 API
    pass
```

### 2. LINE 訊息推播

```python
# 整合 LINE Notify
def send_line_notification(line_token: str, message: str):
    # 使用 LINE Notify API
    pass
```

### 3. 通知偏好設定

```python
# 讓用戶選擇通知方式
class NotificationPreference:
    email: bool = True
    sms: bool = False
    line: bool = False
```

## ✅ 檢查清單

部署前確認：

- [ ] 環境變數已設定
- [ ] Gmail API 已配置
- [ ] notification_log 表已創建
- [ ] Email 模板已客製化
- [ ] 測試腳本執行成功
- [ ] cron job 已設定（如需要）
- [ ] 日誌目錄有寫入權限
- [ ] 客服聯絡資訊已更新

完成以上步驟後，通知系統就可以正常運作了！🎉
