# EDM 通知系統改造完成總結

## 🎯 改造目標

將原本用於房地產行業的 EDM 發信系統，改造成適用於災害補助平台的通知系統。

## ✅ 完成的改動

### 1. 核心程式重構

**原檔案：** `send_notification.py`  
**新檔案：** `send_disaster_notification.py`

#### 移除的內容：
- ❌ MySQL/dataset 相關套件（已全部使用 Supabase）
- ❌ 房地產行業標籤查詢邏輯
- ❌ 多個 Gmail 帳號輪替機制
- ❌ 採訪邀約相關內容
- ❌ 行業過濾邏輯
- ❌ 硬編碼的圖片路徑

#### 新增的功能：
- ✅ `DisasterNotificationService` 類別 - 封裝通知服務
- ✅ `send_approval_notification()` - 發送核准通知
- ✅ `send_rejection_notification()` - 發送駁回通知
- ✅ `get_pending_notifications()` - 從 Supabase 獲取待通知列表
- ✅ `process_pending_notifications()` - 批次處理通知
- ✅ 防重複發送機制
- ✅ 完整的錯誤處理和日誌記錄

### 2. Email 模板更新

#### 核准通知模板 (`approval_notification.html`)
- ✅ 災害補助專用設計
- ✅ 顯示案件編號、核准金額
- ✅ 數位憑證領取步驟說明
- ✅ 客服聯絡資訊

#### 駁回通知模板 (`rejection_notification.html`)
- ✅ 駁回原因顯示
- ✅ 後續處理建議
- ✅ 客服資訊

### 3. 資料庫整合

從 Supabase 取得的資料：
```sql
-- 取得申請人資料
SELECT a.id, a.case_no, a.applicant_name, 
       a.approved_amount, a.status,
       u.email
FROM applications a
JOIN users u ON a.applicant_id = u.id
WHERE a.status IN ('approved', 'rejected')
```

新增資料表：
```sql
CREATE TABLE notification_log (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    notification_type VARCHAR(50),  -- 'approval' 或 'rejection'
    case_no VARCHAR(50),
    application_id INTEGER,
    sent_at TIMESTAMP DEFAULT NOW()
);
```

## 📝 使用說明

### 方式 1：直接執行批次處理

```bash
cd /Users/steve.wang/Mix_Curry
python app/services/edm/send_disaster_notification.py
```

### 方式 2：在程式碼中整合

```python
from app.services.edm.send_disaster_notification import DisasterNotificationService

service = DisasterNotificationService()

# 發送單一通知
service.send_approval_notification(
    recipient_email="user@example.com",
    applicant_name="王小明",
    case_no="2025-001",
    approved_amount=50000,
    application_id=123
)

# 批次處理
service.process_pending_notifications()
```

### 方式 3：整合到審核流程

在 `app/routers/reviews.py` 中整合：

```python
from app.services.edm.send_disaster_notification import DisasterNotificationService

@router.post("/approve/{application_id}")
async def approve_application(application_id: int, ...):
    # ... 審核通過邏輯 ...
    
    # 發送通知
    notification_service = DisasterNotificationService()
    notification_service.send_approval_notification(
        recipient_email=user_email,
        applicant_name=application.applicant_name,
        case_no=application.case_no,
        approved_amount=approved_amount,
        application_id=application_id
    )
```

## 🔧 環境設定

### 必要的環境變數

在 `.env` 檔案中新增：

```env
# Supabase 設定（已存在）
SUPABASE_URL=https://bqxwfhidqjoackptocxb.supabase.co
SUPABASE_SERVICE_ROLE=your_service_role_key

# Email 通知設定（新增）
NOTIFICATION_EMAIL=disaster-relief@choozmo.com
GMAIL_PROFILE_DIR=/root/gmail_test/profiles/disaster
```

### Gmail API 設定

1. 確保 `gmaillib` 目錄存在
2. 設定 Gmail OAuth 認證
3. 將認證檔案放在 `GMAIL_PROFILE_DIR` 指定的路徑

## 📊 改造前後對比

| 項目 | 改造前 | 改造後 |
|------|--------|--------|
| 資料來源 | MySQL + edm_industry_tag 表 | Supabase applications + users 表 |
| 通知類型 | 房地產採訪邀約 | 災害補助核准/駁回 |
| 收件人來源 | 行業標籤過濾 | 申請人 Email |
| 防重複機制 | emaillog + edm_blacklist | notification_log |
| 模板內容 | 房地產議題分析 | 災害補助通知 |
| 發送機制 | 固定間隔（500秒） | 可配置間隔（預設5秒） |

## 🚀 部署建議

### 1. 設定定時任務

使用 cron job 每小時執行一次：

```bash
0 * * * * cd /Users/steve.wang/Mix_Curry && python app/services/edm/send_disaster_notification.py >> /var/log/disaster-notifications.log 2>&1
```

### 2. 監控日誌

```bash
# 查看執行日誌
tail -f /var/log/disaster-notifications.log

# 查看錯誤
grep ERROR /var/log/disaster-notifications.log
```

### 3. 效能優化

- 限制每次批次處理的數量（避免一次發送太多）
- 增加發送失敗重試機制
- 記錄發送統計數據

## ⚠️ 注意事項

1. **Gmail 發送限制**
   - 免費帳號：每天 500 封
   - G Suite：每天 2000 封
   
2. **防止被視為垃圾郵件**
   - 控制發送頻率
   - 確保收件人同意接收
   - 提供取消訂閱選項

3. **安全性**
   - 不要在程式碼中硬編碼敏感資訊
   - 使用環境變數管理 API 金鑰
   - 定期更新 OAuth token

## 🎉 總結

✅ 成功將房地產 EDM 系統改造為災害補助通知系統  
✅ 移除了所有不必要的依賴和邏輯  
✅ 整合 Supabase 資料庫  
✅ 提供完整的錯誤處理和日誌  
✅ 支援批次處理和防重複發送  

現在系統可以自動從 Supabase 中找到所有已核准/駁回的申請，並發送相應的 Email 通知給災民！
