# 🚀 V2.0 升級指南

## 從 V1.0 升級到 V2.0

如果你已經有 V1.0 的系統在運行，請按照以下步驟升級到 V2.0。

---

## 📋 新功能清單

### V2.0 新增功能：

1. ✅ **身份驗證系統** - JWT Token + 角色權限管理
2. ✅ **區域管理** - 里/鄰區域管理，里長只能看自己轄區
3. ✅ **通知系統** - 簡訊 + Email + App 推送通知
4. ✅ **銀行 API 整合** - 帳戶驗證、重複申請檢查
5. ✅ **補件流程** - 里長可要求補件或安排現場勘查
6. ✅ **完整的前後台分離** - 災民端 + 里長端

---

## 🔧 升級步驟

### 1. 備份現有資料庫

```sql
-- 在 Supabase Dashboard 的 SQL Editor 執行
-- 或使用 pg_dump 備份整個資料庫
```

### 2. 更新程式碼

```bash
# 拉取最新程式碼
git pull origin main

# 更新依賴
pip install -r requirements.txt --upgrade
```

### 3. 更新資料庫 Schema

在 Supabase Dashboard 的 SQL Editor 執行以下 SQL（僅新增的部分）：

```sql
-- 1. 新增區域表
CREATE TABLE IF NOT EXISTS districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_code VARCHAR(20) UNIQUE NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    district VARCHAR(50) NOT NULL,
    village VARCHAR(50),
    neighborhood VARCHAR(50),
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 新增通知表
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    action_url TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    sent_via_email BOOLEAN DEFAULT FALSE,
    sent_via_sms BOOLEAN DEFAULT FALSE,
    sent_via_push BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    sms_sent_at TIMESTAMP WITH TIME ZONE,
    push_sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 新增銀行驗證記錄表
CREATE TABLE IF NOT EXISTS bank_verification_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    certificate_id UUID REFERENCES digital_certificates(id),
    verification_type VARCHAR(50) NOT NULL,
    bank_code VARCHAR(10),
    bank_account VARCHAR(50),
    account_holder_name VARCHAR(100),
    is_valid BOOLEAN NOT NULL,
    verification_message TEXT,
    error_code VARCHAR(20),
    api_endpoint VARCHAR(255),
    api_request JSONB,
    api_response JSONB,
    response_time_ms INTEGER,
    has_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_details JSONB,
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 更新 users 表（新增欄位）
ALTER TABLE users ADD COLUMN IF NOT EXISTS district_id UUID REFERENCES districts(id);
ALTER TABLE users ADD COLUMN IF NOT EXISTS digital_identity JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS twfido_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;

-- 5. 更新 applications 表（新增欄位）
ALTER TABLE applications ADD COLUMN IF NOT EXISTS district_id UUID REFERENCES districts(id);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS bank_code VARCHAR(10);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS bank_name VARCHAR(100);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS bank_account VARCHAR(50);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS account_holder_name VARCHAR(100);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS supplement_request TEXT;
ALTER TABLE applications ADD COLUMN IF NOT EXISTS assigned_reviewer_id UUID REFERENCES users(id);
ALTER TABLE applications ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITH TIME ZONE;

-- 6. 更新 digital_certificates 表（新增欄位）
ALTER TABLE digital_certificates ADD COLUMN IF NOT EXISTS gov_certificate_id VARCHAR(255);
ALTER TABLE digital_certificates ADD COLUMN IF NOT EXISTS gov_api_response JSONB;
ALTER TABLE digital_certificates ADD COLUMN IF NOT EXISTS verification_method VARCHAR(50);
ALTER TABLE digital_certificates ADD COLUMN IF NOT EXISTS disbursed_by UUID REFERENCES users(id);
ALTER TABLE digital_certificates ADD COLUMN IF NOT EXISTS disbursement_location TEXT;
ALTER TABLE digital_certificates ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE digital_certificates ADD COLUMN IF NOT EXISTS revoke_reason TEXT;

-- 7. 新增索引
CREATE INDEX IF NOT EXISTS idx_districts_district_code ON districts(district_code);
CREATE INDEX IF NOT EXISTS idx_districts_city ON districts(city);
CREATE INDEX IF NOT EXISTS idx_districts_is_active ON districts(is_active);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_district_id ON users(district_id);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_applications_district_id ON applications(district_id);
CREATE INDEX IF NOT EXISTS idx_applications_assigned_reviewer ON applications(assigned_reviewer_id);
CREATE INDEX IF NOT EXISTS idx_applications_disaster_date ON applications(disaster_date);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_application_id ON notifications(application_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_notification_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_bank_verification_application_id ON bank_verification_records(application_id);
CREATE INDEX IF NOT EXISTS idx_bank_verification_certificate_id ON bank_verification_records(certificate_id);
CREATE INDEX IF NOT EXISTS idx_bank_verification_type ON bank_verification_records(verification_type);
CREATE INDEX IF NOT EXISTS idx_bank_verification_is_valid ON bank_verification_records(is_valid);
CREATE INDEX IF NOT EXISTS idx_bank_verification_created_at ON bank_verification_records(created_at DESC);

-- 8. 啟用 RLS
ALTER TABLE districts ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_verification_records ENABLE ROW LEVEL SECURITY;

-- 9. 建立 RLS 政策
CREATE POLICY "Anyone can view active districts" ON districts
    FOR SELECT USING (is_active = TRUE);

CREATE POLICY "Users can view own notifications" ON notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications" ON notifications
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "System can create notifications" ON notifications
    FOR INSERT WITH CHECK (TRUE);

CREATE POLICY "Reviewers can view bank verification records" ON bank_verification_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() 
            AND role IN ('reviewer', 'admin')
        ) OR
        EXISTS (
            SELECT 1 FROM applications 
            WHERE applications.id = bank_verification_records.application_id 
            AND applications.applicant_id = auth.uid()
        )
    );

-- 10. 建立觸發器
CREATE TRIGGER update_districts_updated_at BEFORE UPDATE ON districts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 11. 建立自動指派審核員函數
CREATE OR REPLACE FUNCTION auto_assign_reviewer()
RETURNS TRIGGER AS $$
DECLARE
    reviewer_id UUID;
BEGIN
    SELECT id INTO reviewer_id
    FROM users
    WHERE role = 'reviewer' 
    AND district_id = NEW.district_id 
    AND is_active = TRUE
    LIMIT 1;
    
    IF reviewer_id IS NOT NULL THEN
        NEW.assigned_reviewer_id := reviewer_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_assign_reviewer 
BEFORE INSERT ON applications
FOR EACH ROW EXECUTE FUNCTION auto_assign_reviewer();

-- 12. 初始化預設區域資料
INSERT INTO districts (district_code, district_name, city, district, village) VALUES
('TN-CW-001', '中西區-民權里', '台南市', '中西區', '民權里'),
('TN-CW-002', '中西區-民生里', '台南市', '中西區', '民生里'),
('TN-EA-001', '東區-東門里', '台南市', '東區', '東門里'),
('TN-SO-001', '南區-南門里', '台南市', '南區', '南門里'),
('TN-NO-001', '北區-北門里', '台南市', '北區', '北門里')
ON CONFLICT (district_code) DO NOTHING;

-- 13. 更新 system_settings 表（如果是從 V1.0 升級）
ALTER TABLE system_settings ADD COLUMN IF NOT EXISTS setting_type VARCHAR(20) DEFAULT 'string';
ALTER TABLE system_settings ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;
ALTER TABLE system_settings ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id);

-- 14. 初始化系統設定
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('max_subsidy_amount', '100000', 'number', '單筆申請最高補助金額', TRUE),
('certificate_validity_days', '90', 'number', '憑證有效天數', TRUE),
('notification_enabled', 'true', 'boolean', '是否啟用通知系統', FALSE),
('bank_api_enabled', 'true', 'boolean', '是否啟用銀行 API 驗證', FALSE),
('gov_api_enabled', 'true', 'boolean', '是否啟用政府憑證 API', FALSE)
ON CONFLICT (setting_key) DO NOTHING;
```

### 4. 更新環境變數

在 `.env` 檔案中新增：

```bash
# 銀行 API 設定（可選）
BANK_API_URL=https://bank-api.example.com
BANK_API_KEY=your-bank-api-key

# 簡訊/Email 服務設定（可選）
# SMS_API_KEY=your-sms-api-key
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=your-email@example.com
# SMTP_PASSWORD=your-password
```

### 5. 重啟服務

```bash
# 停止舊服務
# Ctrl + C

# 啟動新服務
python main.py
```

### 6. 驗證升級

訪問以下 URL 確認新功能：

- http://localhost:8080/docs - 查看新的 API 端點
- http://localhost:8080/api/v1/auth/login - 測試登入功能
- http://localhost:8080/api/v1/districts/ - 查看區域列表
- http://localhost:8080/api/v1/notifications/ - 查看通知列表

---

## 🆕 新 API 端點

### 身份驗證
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
POST /api/v1/auth/logout
```

### 區域管理
```
GET    /api/v1/districts/
GET    /api/v1/districts/{district_id}
POST   /api/v1/districts/
PATCH  /api/v1/districts/{district_id}
DELETE /api/v1/districts/{district_id}
GET    /api/v1/districts/{district_id}/applications
GET    /api/v1/districts/{district_id}/stats
```

### 通知系統
```
GET    /api/v1/notifications/
GET    /api/v1/notifications/unread-count
PATCH  /api/v1/notifications/{notification_id}/read
POST   /api/v1/notifications/mark-all-read
```

---

## 📝 資料遷移注意事項

### 1. 現有使用者需要設定區域

如果你有現有的里長（reviewer）使用者，需要為他們設定 `district_id`：

```sql
UPDATE users
SET district_id = (SELECT id FROM districts WHERE district_code = 'TN-CW-001')
WHERE email = 'reviewer@example.com';
```

### 2. 現有申請案件需要關聯區域

```sql
-- 根據地址自動關聯區域（範例）
UPDATE applications
SET district_id = (SELECT id FROM districts WHERE district_code = 'TN-CW-001')
WHERE address LIKE '%中西區%民權%';
```

### 3. 測試新功能

```bash
# 建立測試使用者和資料
python command.py create-test-data

# 測試 API
python test_api.py
```

---

## 🐛 常見問題

### Q: 升級後無法登入？
A: V2.0 使用 JWT Token 驗證，需要重新登入並取得新的 Token。

### Q: 里長看不到案件？
A: 檢查里長的 `district_id` 是否已設定，且申請案件的 `district_id` 是否正確。

### Q: 通知系統不工作？
A: 檢查 `.env` 中的簡訊/Email 服務設定是否正確。

### Q: 資料庫執行 SQL 失敗？
A: 確認使用的是 `service_role` 金鑰，而非 `anon` 金鑰。

---

## 📚 延伸閱讀

- [FLOW_DIAGRAM.md](./FLOW_DIAGRAM.md) - 完整流程圖
- [FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md) - 前端整合指南
- [README.md](./README.md) - 完整專案說明

---

**🎉 升級完成！享受 V2.0 的新功能！**

