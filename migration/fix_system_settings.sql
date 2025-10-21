-- ==========================================
-- 修正 system_settings 表結構
-- ==========================================

/*
-- 方案 1: 如果你要保留現有資料，執行以下 ALTER TABLE
ALTER TABLE system_settings ADD COLUMN IF NOT EXISTS setting_type VARCHAR(20) DEFAULT 'string';
ALTER TABLE system_settings ADD COLUMN IF NOT EXISTS is_public BOOLEAN DEFAULT FALSE;
ALTER TABLE system_settings ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id);

-- 然後可以安全地執行 INSERT
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('max_subsidy_amount', '100000', 'number', '單筆申請最高補助金額', TRUE),
('certificate_validity_days', '90', 'number', '憑證有效天數', TRUE),
('notification_enabled', 'true', 'boolean', '是否啟用通知系統', FALSE),
('bank_api_enabled', 'true', 'boolean', '是否啟用銀行 API 驗證', FALSE),
('gov_api_enabled', 'true', 'boolean', '是否啟用政府憑證 API', FALSE)
ON CONFLICT (setting_key) DO NOTHING;
*/
-- ==========================================
-- 方案 2: 如果你想要完全重建表（會刪除所有資料）
-- ==========================================

-- 取消註解以下代碼來執行方案 2

DROP TABLE IF EXISTS system_settings CASCADE;

CREATE TABLE system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(20) DEFAULT 'string', -- string, number, boolean, json
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE, -- 是否可公開存取
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 啟用 RLS
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;

-- 建立觸發器
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 插入初始資料
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('max_subsidy_amount', '100000', 'number', '單筆申請最高補助金額', TRUE),
('certificate_validity_days', '90', 'number', '憑證有效天數', TRUE),
('notification_enabled', 'true', 'boolean', '是否啟用通知系統', FALSE),
('bank_api_enabled', 'true', 'boolean', '是否啟用銀行 API 驗證', FALSE),
('gov_api_enabled', 'true', 'boolean', '是否啟用政府憑證 API', FALSE);


