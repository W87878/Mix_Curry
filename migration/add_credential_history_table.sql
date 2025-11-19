-- ==========================================
-- 新增憑證使用歷史記錄表
-- 用於記錄憑證發行（領取）和驗證的完整歷史
-- ==========================================

-- 建立 credential_history 表
CREATE TABLE IF NOT EXISTS credential_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 關聯資料
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    certificate_id UUID REFERENCES digital_certificates(id),
    
    -- 動作類型
    action_type VARCHAR(50) NOT NULL, -- credential_issued(憑證發行/領取), credential_verified(憑證驗證)
    action_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(), -- 動作發生時間
    
    -- 申請人基本資料（快照，避免 JOIN）
    applicant_name VARCHAR(100) NOT NULL, -- 申請人姓名
    id_number VARCHAR(20) NOT NULL, -- 身分證字號
    
    -- 災害資料
    disaster_type VARCHAR(50) NOT NULL, -- 災害類型：flood(水災), typhoon(颱風), earthquake(地震)等
    disaster_address TEXT NOT NULL, -- 受災地址
    approved_amount DECIMAL(12, 2), -- 核准金額
    
    -- 機構資訊（兩個欄位，其中一個會是 NULL）
    issuer_organization VARCHAR(200), -- 發行機構（領取憑證時記錄，如：「台南市政府災害救助中心」）
    verifier_organization VARCHAR(200), -- 驗證機構（711驗證時記錄，如：「7-11 中正門市」）
    
    -- 狀態
    status VARCHAR(20) NOT NULL, -- issued(已發行/已領取), verified(已驗證)
    
    -- 技術資料
    transaction_id VARCHAR(255), -- 政府 API 的 transaction ID
    verification_location JSONB, -- 驗證地點詳細資訊（經緯度、地址等）
    device_info JSONB, -- 裝置資訊（可選）
    
    -- 備註
    notes TEXT, -- 備註
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 建立索引以提升查詢效能
CREATE INDEX IF NOT EXISTS idx_credential_history_application_id ON credential_history(application_id);
CREATE INDEX IF NOT EXISTS idx_credential_history_user_id ON credential_history(user_id);
CREATE INDEX IF NOT EXISTS idx_credential_history_certificate_id ON credential_history(certificate_id);
CREATE INDEX IF NOT EXISTS idx_credential_history_action_type ON credential_history(action_type);
CREATE INDEX IF NOT EXISTS idx_credential_history_status ON credential_history(status);
CREATE INDEX IF NOT EXISTS idx_credential_history_action_time ON credential_history(action_time DESC);
CREATE INDEX IF NOT EXISTS idx_credential_history_transaction_id ON credential_history(transaction_id);
CREATE INDEX IF NOT EXISTS idx_credential_history_id_number ON credential_history(id_number);

-- 啟用 Row Level Security (RLS)
ALTER TABLE credential_history ENABLE ROW LEVEL SECURITY;

-- RLS 政策：使用者只能查看自己的歷史記錄
CREATE POLICY "使用者可查看自己的憑證歷史" ON credential_history
    FOR SELECT
    USING (auth.uid() = user_id);

-- RLS 政策：管理員可以查看所有記錄
CREATE POLICY "管理員可查看所有憑證歷史" ON credential_history
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = auth.uid()
            AND users.role = 'admin'
        )
    );

-- RLS 政策：系統可以插入記錄（使用 service_role）
CREATE POLICY "系統可插入憑證歷史" ON credential_history
    FOR INSERT
    WITH CHECK (true);

-- 添加表格註解
COMMENT ON TABLE credential_history IS '憑證使用歷史記錄表 - 記錄憑證發行（領取）和驗證的完整歷史';
COMMENT ON COLUMN credential_history.action_type IS '動作類型：credential_issued(憑證發行/領取), credential_verified(憑證驗證)';
COMMENT ON COLUMN credential_history.status IS '狀態：issued(已發行/已領取), verified(已驗證)';
COMMENT ON COLUMN credential_history.issuer_organization IS '發行機構（領取憑證時記錄，如：台南市政府災害救助中心）';
COMMENT ON COLUMN credential_history.verifier_organization IS '驗證機構（711驗證時記錄，如：7-11 中正門市）';
COMMENT ON COLUMN credential_history.verification_location IS '驗證地點詳細資訊（JSONB格式，包含經緯度、地址等）';

-- 完成訊息
DO $$
BEGIN
    RAISE NOTICE '✅ credential_history 表已成功建立';
    RAISE NOTICE '📊 包含以下功能：';
    RAISE NOTICE '   - 記錄憑證發行（使用者領取）';
    RAISE NOTICE '   - 記錄憑證驗證（711機台驗證）';
    RAISE NOTICE '   - 區分發行機構和驗證機構';
    RAISE NOTICE '   - 支援地點資訊記錄';
    RAISE NOTICE '   - 已啟用 RLS 安全政策';
END $$;
