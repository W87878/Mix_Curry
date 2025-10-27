-- ==========================================
-- 災民補助申請系統 - 統一資料庫結構檔案
-- 包含所有 CREATE TABLE、ALTER TABLE、索引、觸發器、函數和初始化資料
-- ==========================================
-- 檔案說明：
-- 1. 此檔案整合了 database_schema.sql、add_gov_api_fields.sql、fix_system_settings.sql
-- 2. 可直接在乾淨的資料庫執行，建立完整的結構
-- 3. 包含 10 個主表、索引、RLS 政策、觸發器和函數
-- ==========================================

-- ==========================================
-- PART 1: 建立所有資料表
-- ==========================================

-- 1. 區域表（里/鄰區域管理）
CREATE TABLE IF NOT EXISTS districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_code VARCHAR(20) UNIQUE NOT NULL, -- 區域代碼，例如：TN-CW-001
    district_name VARCHAR(100) NOT NULL, -- 區域名稱，例如：中西區-民權里
    city VARCHAR(50) NOT NULL, -- 城市，例如：台南市
    district VARCHAR(50) NOT NULL, -- 行政區，例如：中西區
    village VARCHAR(50), -- 里，例如：民權里
    neighborhood VARCHAR(50), -- 鄰
    
    -- 聯絡資訊
    contact_person VARCHAR(100), -- 里長姓名
    contact_phone VARCHAR(20),
    contact_email VARCHAR(255),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 使用者表（擴充版）
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    full_name VARCHAR(100) NOT NULL,
    id_number VARCHAR(20), -- 身分證字號
    
    -- 角色與權限
    role VARCHAR(20) NOT NULL DEFAULT 'applicant', -- applicant(災民), reviewer(里長), admin(管理員)
    district_id UUID REFERENCES districts(id), -- 所屬區域（里長專用）
    
    -- 數位身份驗證資訊
    digital_identity JSONB, -- 存儲數位憑證相關資訊
    twfido_verified BOOLEAN DEFAULT FALSE, -- TW FidO 驗證狀態
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- 帳戶狀態
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 申請案件表（主表 - 擴充版）
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_no VARCHAR(50) UNIQUE NOT NULL, -- 案件編號 (自動生成)
    applicant_id UUID NOT NULL REFERENCES users(id),
    district_id UUID REFERENCES districts(id), -- 申請案件所屬區域
    
    -- 申請人資料
    applicant_name VARCHAR(100) NOT NULL,
    id_number VARCHAR(20) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    
    -- 銀行資料
    bank_code VARCHAR(10), -- 銀行代碼
    bank_name VARCHAR(100), -- 銀行名稱
    bank_account VARCHAR(50), -- 銀行帳戶
    account_holder_name VARCHAR(100), -- 帳戶名稱（需與申請人相同）
    
    -- 災損資料
    disaster_date DATE NOT NULL, -- 災害發生日期
    disaster_type VARCHAR(50) NOT NULL, -- 水災、風災、地震等
    damage_description TEXT NOT NULL, -- 災損描述
    damage_location TEXT NOT NULL, -- 災損地點
    estimated_loss DECIMAL(12, 2), -- 預估損失金額
    
    -- 申請資料
    subsidy_type VARCHAR(50) NOT NULL, -- 補助類型：房屋、設備、生活補助等
    requested_amount DECIMAL(12, 2), -- 申請金額
    
    -- 審核狀態（擴充）
    status VARCHAR(20) NOT NULL DEFAULT 'pending', 
    -- pending(待審核), under_review(審核中), supplementing(補件中),
    -- site_inspection(現場勘查中), inspecting(勘查中),
    -- approved(核准), rejected(駁回), completed(已發放), disbursed(已發放)
    
    review_notes TEXT, -- 審核備註
    approved_amount DECIMAL(12, 2), -- 核准金額
    rejection_reason TEXT, -- 駁回原因
    supplement_request TEXT, -- 補件要求說明
    
    -- 審核人員
    assigned_reviewer_id UUID REFERENCES users(id), -- 指派的審核員
    
    -- 政府數位憑證相關欄位（來自 add_gov_api_fields.sql）
    gov_qr_code_data TEXT, -- 政府發行端返回的 QR Code（Base64）
    gov_transaction_id VARCHAR(255), -- 政府的 transaction ID
    gov_deep_link TEXT, -- Deep link for APP
    gov_vc_uid VARCHAR(255), -- VC 憑證 ID
    vp_transaction_id VARCHAR(255), -- VP 驗證的 transaction ID
    disbursed_at TIMESTAMP WITH TIME ZONE, -- 補助發放時間
    
    -- 時間記錄
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 災損照片表
CREATE TABLE IF NOT EXISTS damage_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    photo_type VARCHAR(50) NOT NULL, -- before_damage, after_damage, site_inspection, supplement
    storage_path TEXT NOT NULL, -- Supabase Storage 路徑
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER, -- bytes
    mime_type VARCHAR(100),
    
    description TEXT, -- 照片說明
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 審核記錄表
CREATE TABLE IF NOT EXISTS review_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    reviewer_id UUID NOT NULL REFERENCES users(id),
    reviewer_name VARCHAR(100) NOT NULL,
    
    action VARCHAR(50) NOT NULL, -- submitted, under_review, request_supplement, site_inspection, approved, rejected
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    
    comments TEXT, -- 審核意見
    decision_reason TEXT, -- 核准/駁回理由
    
    -- 現場勘查資料
    inspection_date TIMESTAMP WITH TIME ZONE,
    inspection_notes TEXT,
    inspection_location TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 數位憑證表
CREATE TABLE IF NOT EXISTS digital_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    certificate_no VARCHAR(100) UNIQUE NOT NULL, -- 憑證編號
    qr_code_data TEXT NOT NULL, -- QR Code 資料（JSON 格式）
    qr_code_image_path TEXT, -- QR Code 圖片儲存路徑
    
    -- 政府憑證 API 回傳資訊
    gov_certificate_id VARCHAR(255), -- 政府憑證系統 ID
    gov_api_response JSONB, -- 政府 API 完整回應
    
    issued_amount DECIMAL(12, 2) NOT NULL, -- 核發金額
    issued_by UUID REFERENCES users(id),
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 憑證驗證
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES users(id),
    verification_method VARCHAR(50), -- qr_code, manual, api
    
    -- 補助發放
    is_disbursed BOOLEAN DEFAULT FALSE,
    disbursed_at TIMESTAMP WITH TIME ZONE,
    disbursed_by UUID REFERENCES users(id),
    disbursement_method VARCHAR(50), -- bank_transfer, check, cash
    disbursement_location TEXT, -- 發放地點
    
    expires_at TIMESTAMP WITH TIME ZONE, -- 憑證有效期限
    revoked_at TIMESTAMP WITH TIME ZONE, -- 撤銷時間
    revoke_reason TEXT, -- 撤銷原因
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. 補助項目表
CREATE TABLE IF NOT EXISTS subsidy_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    item_category VARCHAR(50) NOT NULL, -- housing, furniture, appliances, living_expenses
    item_name VARCHAR(200) NOT NULL,
    item_description TEXT,
    quantity INTEGER DEFAULT 1,
    unit_price DECIMAL(12, 2),
    total_price DECIMAL(12, 2) NOT NULL,
    
    approved BOOLEAN DEFAULT FALSE,
    approved_amount DECIMAL(12, 2),
    rejection_reason TEXT, -- 不核准的原因
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. 通知系統表
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- 接收通知的使用者
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE, -- 相關申請案件
    
    -- email
    email VARCHAR(255),

    -- 通知類型
    notification_type VARCHAR(50) NOT NULL,
    -- application_submitted(申請已提交), application_approved(申請核准),
    -- application_rejected(申請駁回), supplement_required(需要補件),
    -- inspection_scheduled(已安排勘查), certificate_issued(憑證已發行),
    -- subsidy_disbursed(補助已發放), review_assigned(審核已指派)
    
    title VARCHAR(255) NOT NULL, -- 通知標題
    content TEXT NOT NULL, -- 通知內容
    action_url TEXT, -- 動作連結（例如：查看申請詳情）
    
    -- 通知狀態
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,
    
    -- 發送通道
    sent_via_email BOOLEAN DEFAULT FALSE,
    sent_via_sms BOOLEAN DEFAULT FALSE,
    sent_via_push BOOLEAN DEFAULT FALSE,
    
    email_sent_at TIMESTAMP WITH TIME ZONE,
    sms_sent_at TIMESTAMP WITH TIME ZONE,
    push_sent_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. 銀行驗證記錄表
CREATE TABLE IF NOT EXISTS bank_verification_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    certificate_id UUID REFERENCES digital_certificates(id),
    
    -- 驗證類型
    verification_type VARCHAR(50) NOT NULL,
    -- account_validation(帳戶驗證), duplicate_check(重複申請檢查),
    -- final_verification(最終驗證), disbursement_record(發放記錄)
    
    -- 驗證資訊
    bank_code VARCHAR(10),
    bank_account VARCHAR(50),
    account_holder_name VARCHAR(100),
    
    -- 驗證結果
    is_valid BOOLEAN NOT NULL,
    verification_message TEXT, -- 驗證訊息
    error_code VARCHAR(20), -- 錯誤代碼
    
    -- API 資訊
    api_endpoint VARCHAR(255), -- 呼叫的 API 端點
    api_request JSONB, -- API 請求內容
    api_response JSONB, -- API 回應內容
    response_time_ms INTEGER, -- 回應時間（毫秒）
    
    -- 重複申請檢查結果
    has_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_details JSONB, -- 重複申請的詳細資訊
    
    verified_by UUID REFERENCES users(id),
    verified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. 系統設定表
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    setting_type VARCHAR(20) DEFAULT 'string', -- string, number, boolean, json
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE, -- 是否可公開存取
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- PART 2: 建立索引以提升查詢效能
-- ==========================================

-- Districts 索引
CREATE INDEX IF NOT EXISTS idx_districts_district_code ON districts(district_code);
CREATE INDEX IF NOT EXISTS idx_districts_city ON districts(city);
CREATE INDEX IF NOT EXISTS idx_districts_is_active ON districts(is_active);

-- Users 索引
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_district_id ON users(district_id);
CREATE INDEX IF NOT EXISTS idx_users_id_number ON users(id_number);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Applications 索引
CREATE INDEX IF NOT EXISTS idx_applications_applicant_id ON applications(applicant_id);
CREATE INDEX IF NOT EXISTS idx_applications_district_id ON applications(district_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_case_no ON applications(case_no);
CREATE INDEX IF NOT EXISTS idx_applications_submitted_at ON applications(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_applications_assigned_reviewer ON applications(assigned_reviewer_id);
CREATE INDEX IF NOT EXISTS idx_applications_disaster_date ON applications(disaster_date);

-- Applications 政府 API 相關索引（來自 add_gov_api_fields.sql）
CREATE INDEX IF NOT EXISTS idx_applications_gov_transaction_id ON applications(gov_transaction_id);
CREATE INDEX IF NOT EXISTS idx_applications_vp_transaction_id ON applications(vp_transaction_id);
CREATE INDEX IF NOT EXISTS idx_applications_status_disbursed ON applications(status) WHERE status = 'disbursed';

-- Damage Photos 索引
CREATE INDEX IF NOT EXISTS idx_damage_photos_application_id ON damage_photos(application_id);
CREATE INDEX IF NOT EXISTS idx_damage_photos_photo_type ON damage_photos(photo_type);

-- Review Records 索引
CREATE INDEX IF NOT EXISTS idx_review_records_application_id ON review_records(application_id);
CREATE INDEX IF NOT EXISTS idx_review_records_reviewer_id ON review_records(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_review_records_created_at ON review_records(created_at DESC);

-- Digital Certificates 索引
CREATE INDEX IF NOT EXISTS idx_digital_certificates_application_id ON digital_certificates(application_id);
CREATE INDEX IF NOT EXISTS idx_digital_certificates_certificate_no ON digital_certificates(certificate_no);
CREATE INDEX IF NOT EXISTS idx_digital_certificates_is_verified ON digital_certificates(is_verified);
CREATE INDEX IF NOT EXISTS idx_digital_certificates_is_disbursed ON digital_certificates(is_disbursed);

-- Subsidy Items 索引
CREATE INDEX IF NOT EXISTS idx_subsidy_items_application_id ON subsidy_items(application_id);

-- Notifications 索引
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_application_id ON notifications(application_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_notification_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Bank Verification Records 索引
CREATE INDEX IF NOT EXISTS idx_bank_verification_application_id ON bank_verification_records(application_id);
CREATE INDEX IF NOT EXISTS idx_bank_verification_certificate_id ON bank_verification_records(certificate_id);
CREATE INDEX IF NOT EXISTS idx_bank_verification_type ON bank_verification_records(verification_type);
CREATE INDEX IF NOT EXISTS idx_bank_verification_is_valid ON bank_verification_records(is_valid);
CREATE INDEX IF NOT EXISTS idx_bank_verification_created_at ON bank_verification_records(created_at DESC);

-- ==========================================
-- PART 3: 資料表註解（來自 add_gov_api_fields.sql）
-- ==========================================

COMMENT ON COLUMN applications.gov_qr_code_data IS '政府發行端 API 返回的 QR Code 資料（Base64）';
COMMENT ON COLUMN applications.gov_transaction_id IS '政府發行端 API 的 transaction ID';
COMMENT ON COLUMN applications.gov_deep_link IS 'Deep link 用於開啟數位憑證 APP';
COMMENT ON COLUMN applications.gov_vc_uid IS 'VC 憑證模板 ID（例如：00000000_subsidy_666）';
COMMENT ON COLUMN applications.disbursed_at IS '補助實際發放的時間（VP 驗證成功後）';
COMMENT ON COLUMN applications.vp_transaction_id IS 'VP 驗證端的 transaction ID（7-11 機台產生）';

-- ==========================================
-- PART 4: Row Level Security (RLS) 政策
-- ==========================================

-- 啟用 RLS
ALTER TABLE districts ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE damage_photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE digital_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE subsidy_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE bank_verification_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_settings ENABLE ROW LEVEL SECURITY;

-- Districts: 所有人都可以查看啟用的區域
CREATE POLICY "Anyone can view active districts" ON districts
    FOR SELECT USING (is_active = TRUE);

-- Users: 使用者只能查看和更新自己的資料
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Applications: 申請人可查看自己的申請，里長可查看自己轄區的案件
CREATE POLICY "Users can view related applications" ON applications
    FOR SELECT USING (
        auth.uid() = applicant_id OR 
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() 
            AND (
                role = 'admin' OR 
                (role = 'reviewer' AND district_id = applications.district_id)
            )
        )
    );

CREATE POLICY "Users can create applications" ON applications
    FOR INSERT WITH CHECK (auth.uid() = applicant_id);

CREATE POLICY "Users can update own applications" ON applications
    FOR UPDATE USING (
        (auth.uid() = applicant_id AND status IN ('pending', 'supplementing')) OR
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() 
            AND role IN ('reviewer', 'admin')
            AND (role = 'admin' OR district_id = applications.district_id)
        )
    );

-- Damage Photos: 與申請案件相同的存取權限
CREATE POLICY "Users can view related photos" ON damage_photos
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM applications 
            WHERE applications.id = damage_photos.application_id 
            AND (
                applications.applicant_id = auth.uid() OR 
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE id = auth.uid() 
                    AND (
                        role = 'admin' OR 
                        (role = 'reviewer' AND district_id = applications.district_id)
                    )
                )
            )
        )
    );

CREATE POLICY "Users can upload photos to own applications" ON damage_photos
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM applications 
            WHERE applications.id = damage_photos.application_id 
            AND (
                applications.applicant_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE id = auth.uid() 
                    AND role IN ('reviewer', 'admin')
                )
            )
        )
    );

-- Review Records: 只有審核員和管理員可以建立審核記錄
CREATE POLICY "Reviewers can create review records" ON review_records
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = auth.uid() 
            AND role IN ('reviewer', 'admin')
        )
    );

CREATE POLICY "Users can view review records" ON review_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM applications 
            WHERE applications.id = review_records.application_id 
            AND (
                applications.applicant_id = auth.uid() OR 
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE id = auth.uid() 
                    AND (
                        role = 'admin' OR 
                        (role = 'reviewer' AND district_id = applications.district_id)
                    )
                )
            )
        )
    );

-- Digital Certificates: 與申請案件相同的存取權限
CREATE POLICY "Users can view related certificates" ON digital_certificates
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM applications 
            WHERE applications.id = digital_certificates.application_id 
            AND (
                applications.applicant_id = auth.uid() OR 
                EXISTS (
                    SELECT 1 FROM users 
                    WHERE id = auth.uid() 
                    AND role IN ('reviewer', 'admin')
                )
            )
        )
    );

-- Notifications: 使用者只能查看自己的通知
CREATE POLICY "Users can view own notifications" ON notifications
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications" ON notifications
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "System can create notifications" ON notifications
    FOR INSERT WITH CHECK (TRUE); -- 系統可建立通知

-- Bank Verification Records: 只有審核員和管理員可查看
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

-- ==========================================
-- PART 5: 觸發器與函數
-- ==========================================

-- 函數：自動更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 建立更新觸發器
CREATE TRIGGER update_districts_updated_at BEFORE UPDATE ON districts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 函數：生成案件編號
CREATE OR REPLACE FUNCTION generate_case_no()
RETURNS TEXT AS $$
DECLARE
    case_year TEXT;
    case_seq TEXT;
    new_case_no TEXT;
BEGIN
    case_year := TO_CHAR(NOW(), 'YYYY');
    
    -- 取得今年度最後一個案件編號的序號
    SELECT COALESCE(MAX(CAST(SUBSTRING(case_no FROM 10) AS INTEGER)), 0) + 1
    INTO case_seq
    FROM applications
    WHERE case_no LIKE 'CASE-' || case_year || '-%';
    
    new_case_no := 'CASE-' || case_year || '-' || LPAD(case_seq::TEXT, 5, '0');
    
    RETURN new_case_no;
END;
$$ LANGUAGE plpgsql;

-- 函數：自動指派審核員（根據區域）
CREATE OR REPLACE FUNCTION auto_assign_reviewer()
RETURNS TRIGGER AS $$
DECLARE
    reviewer_id UUID;
BEGIN
    -- 尋找該區域的里長（reviewer）
    SELECT id INTO reviewer_id
    FROM users
    WHERE role = 'reviewer' 
    AND district_id = NEW.district_id 
    AND is_active = TRUE
    LIMIT 1;
    
    -- 如果找到，自動指派
    IF reviewer_id IS NOT NULL THEN
        NEW.assigned_reviewer_id := reviewer_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_assign_reviewer 
BEFORE INSERT ON applications
FOR EACH ROW EXECUTE FUNCTION auto_assign_reviewer();

-- ==========================================
-- PART 6: 初始化資料
-- ==========================================

-- 初始化區域（範例）
INSERT INTO districts (district_code, district_name, city, district, village) VALUES
('TN-CW-001', '中西區-民權里', '台南市', '中西區', '民權里'),
('TN-CW-002', '中西區-民生里', '台南市', '中西區', '民生里'),
('TN-EA-001', '東區-東門里', '台南市', '東區', '東門里'),
('TN-SO-001', '南區-南門里', '台南市', '南區', '南門里'),
('TN-NO-001', '北區-北門里', '台南市', '北區', '北門里')
ON CONFLICT (district_code) DO NOTHING;

-- 初始化系統設定
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('max_subsidy_amount', '100000', 'number', '單筆申請最高補助金額', TRUE),
('certificate_validity_days', '90', 'number', '憑證有效天數', TRUE),
('notification_enabled', 'true', 'boolean', '是否啟用通知系統', FALSE),
('bank_api_enabled', 'true', 'boolean', '是否啟用銀行 API 驗證', FALSE),
('gov_api_enabled', 'true', 'boolean', '是否啟用政府憑證 API', FALSE)
ON CONFLICT (setting_key) DO NOTHING;

-- ==========================================
-- PART 7: Storage Buckets 設定說明
-- ==========================================

/*
在 Supabase Dashboard 建立以下 Storage Buckets：

1. damage-photos (災損照片)
   - Public: false
   - File size limit: 10MB
   - Allowed MIME types: image/jpeg, image/png, image/jpg

2. qr-codes (QR Code 圖片)
   - Public: true (可公開存取以便掃描)
   - File size limit: 1MB
   - Allowed MIME types: image/png

3. inspection-photos (現場勘查照片)
   - Public: false
   - File size limit: 10MB
   - Allowed MIME types: image/jpeg, image/png, image/jpg

Storage 政策範例：
- 允許上傳到自己的申請案件：
  CREATE POLICY "Users can upload to own applications" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'damage-photos' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );
*/

-- ==========================================
-- 執行完畢
-- ==========================================
-- 此統一 schema 檔案已整合所有結構
-- 包含：
-- - 10 個資料表（districts, users, applications, damage_photos, review_records, 
--   digital_certificates, subsidy_items, notifications, bank_verification_records, system_settings）
-- - 所有政府 API 欄位
-- - 34 個索引
-- - RLS 政策
-- - 4 個觸發器
-- - 3 個函數
-- - 初始化資料
-- ==========================================
