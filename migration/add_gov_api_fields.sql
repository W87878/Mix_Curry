-- ==========================================
-- 添加政府 API 相關欄位到 applications 表
-- ==========================================

-- 添加政府數位憑證相關欄位
ALTER TABLE applications 
ADD COLUMN IF NOT EXISTS gov_qr_code_data TEXT,  -- 政府發行端返回的 QR Code
ADD COLUMN IF NOT EXISTS gov_transaction_id VARCHAR(255),  -- 政府的 transaction ID
ADD COLUMN IF NOT EXISTS gov_deep_link TEXT,  -- Deep link for APP
ADD COLUMN IF NOT EXISTS gov_vc_uid VARCHAR(255),  -- VC 憑證 ID
ADD COLUMN IF NOT EXISTS disbursed_at TIMESTAMP WITH TIME ZONE,  -- 補助發放時間
ADD COLUMN IF NOT EXISTS vp_transaction_id VARCHAR(255);  -- VP 驗證的 transaction ID

-- 添加索引以提升查詢效能
CREATE INDEX IF NOT EXISTS idx_applications_gov_transaction_id ON applications(gov_transaction_id);
CREATE INDEX IF NOT EXISTS idx_applications_vp_transaction_id ON applications(vp_transaction_id);
CREATE INDEX IF NOT EXISTS idx_applications_status_disbursed ON applications(status) WHERE status = 'disbursed';

-- 註解
COMMENT ON COLUMN applications.gov_qr_code_data IS '政府發行端 API 返回的 QR Code 資料（Base64）';
COMMENT ON COLUMN applications.gov_transaction_id IS '政府發行端 API 的 transaction ID';
COMMENT ON COLUMN applications.gov_deep_link IS 'Deep link 用於開啟數位憑證 APP';
COMMENT ON COLUMN applications.gov_vc_uid IS 'VC 憑證模板 ID（例如：00000000_subsidy_666）';
COMMENT ON COLUMN applications.disbursed_at IS '補助實際發放的時間（VP 驗證成功後）';
COMMENT ON COLUMN applications.vp_transaction_id IS 'VP 驗證端的 transaction ID（7-11 機台產生）';

