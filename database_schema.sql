-- ==========================================
-- 災民補助申請系統 - Supabase 資料庫結構
-- ==========================================

-- 1. 使用者表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    full_name VARCHAR(100) NOT NULL,
    id_number VARCHAR(20) UNIQUE NOT NULL, -- 身分證字號
    role VARCHAR(20) NOT NULL DEFAULT 'applicant', -- applicant, reviewer, admin
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 申請案件表（主表）
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_no VARCHAR(50) UNIQUE NOT NULL, -- 案件編號 (自動生成)
    applicant_id UUID NOT NULL REFERENCES users(id),
    
    -- 申請人資料
    applicant_name VARCHAR(100) NOT NULL,
    id_number VARCHAR(20) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL,
    
    -- 災損資料
    disaster_date DATE NOT NULL, -- 災害發生日期
    disaster_type VARCHAR(50) NOT NULL, -- 水災、風災、地震等
    damage_description TEXT NOT NULL, -- 災損描述
    damage_location TEXT NOT NULL, -- 災損地點
    estimated_loss DECIMAL(12, 2), -- 預估損失金額
    
    -- 申請資料
    subsidy_type VARCHAR(50) NOT NULL, -- 補助類型：房屋、設備、生活補助等
    requested_amount DECIMAL(12, 2), -- 申請金額
    
    -- 審核狀態
    status VARCHAR(20) NOT NULL DEFAULT 'pending', 
    -- pending(待審核), under_review(審核中), site_inspection(現場勘查中), 
    -- approved(核准), rejected(駁回), completed(已發放)
    
    review_notes TEXT, -- 審核備註
    approved_amount DECIMAL(12, 2), -- 核准金額
    
    -- 時間記錄
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 災損照片表
CREATE TABLE IF NOT EXISTS damage_photos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    photo_type VARCHAR(50) NOT NULL, -- before_damage, after_damage, site_inspection
    storage_path TEXT NOT NULL, -- Supabase Storage 路徑
    file_name VARCHAR(255) NOT NULL,
    file_size INTEGER, -- bytes
    mime_type VARCHAR(100),
    
    description TEXT, -- 照片說明
    uploaded_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 審核記錄表
CREATE TABLE IF NOT EXISTS review_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    reviewer_id UUID NOT NULL REFERENCES users(id),
    reviewer_name VARCHAR(100) NOT NULL,
    
    action VARCHAR(50) NOT NULL, -- submitted, under_review, site_inspection, approved, rejected
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    
    comments TEXT, -- 審核意見
    decision_reason TEXT, -- 核准/駁回理由
    
    -- 現場勘查資料
    inspection_date TIMESTAMP WITH TIME ZONE,
    inspection_notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 數位憑證表
CREATE TABLE IF NOT EXISTS digital_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    
    certificate_no VARCHAR(100) UNIQUE NOT NULL, -- 憑證編號
    qr_code_data TEXT NOT NULL, -- QR Code 資料（JSON 格式）
    qr_code_image_path TEXT, -- QR Code 圖片儲存路徑
    
    issued_amount DECIMAL(12, 2) NOT NULL, -- 核發金額
    issued_by UUID REFERENCES users(id),
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 憑證驗證
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP WITH TIME ZONE,
    verified_by UUID REFERENCES users(id),
    
    -- 補助發放
    is_disbursed BOOLEAN DEFAULT FALSE,
    disbursed_at TIMESTAMP WITH TIME ZONE,
    disbursement_method VARCHAR(50), -- bank_transfer, check, cash
    
    expires_at TIMESTAMP WITH TIME ZONE, -- 憑證有效期限
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 補助項目表
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
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. 系統設定表
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- 建立索引以提升查詢效能
-- ==========================================

CREATE INDEX idx_applications_applicant_id ON applications(applicant_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_case_no ON applications(case_no);
CREATE INDEX idx_applications_submitted_at ON applications(submitted_at DESC);

CREATE INDEX idx_damage_photos_application_id ON damage_photos(application_id);
CREATE INDEX idx_review_records_application_id ON review_records(application_id);
CREATE INDEX idx_review_records_reviewer_id ON review_records(reviewer_id);

CREATE INDEX idx_digital_certificates_application_id ON digital_certificates(application_id);
CREATE INDEX idx_digital_certificates_certificate_no ON digital_certificates(certificate_no);
CREATE INDEX idx_digital_certificates_is_verified ON digital_certificates(is_verified);

CREATE INDEX idx_subsidy_items_application_id ON subsidy_items(application_id);

-- ==========================================
-- Row Level Security (RLS) 政策
-- ==========================================

-- 啟用 RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE damage_photos ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE digital_certificates ENABLE ROW LEVEL SECURITY;
ALTER TABLE subsidy_items ENABLE ROW LEVEL SECURITY;

-- Users: 使用者只能查看和更新自己的資料
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Applications: 申請人可查看自己的申請，審核員可查看所有
CREATE POLICY "Users can view own applications" ON applications
    FOR SELECT USING (
        auth.uid() = applicant_id OR 
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('reviewer', 'admin'))
    );

CREATE POLICY "Users can create applications" ON applications
    FOR INSERT WITH CHECK (auth.uid() = applicant_id);

CREATE POLICY "Users can update own applications" ON applications
    FOR UPDATE USING (
        auth.uid() = applicant_id AND status = 'pending' OR
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('reviewer', 'admin'))
    );

-- Damage Photos: 與申請案件相同的存取權限
CREATE POLICY "Users can view related photos" ON damage_photos
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM applications 
            WHERE applications.id = damage_photos.application_id 
            AND (applications.applicant_id = auth.uid() OR 
                 EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('reviewer', 'admin')))
        )
    );

CREATE POLICY "Users can upload photos to own applications" ON damage_photos
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM applications 
            WHERE applications.id = damage_photos.application_id 
            AND applications.applicant_id = auth.uid()
        )
    );

-- Review Records: 只有審核員和管理員可以建立審核記錄
CREATE POLICY "Reviewers can create review records" ON review_records
    FOR INSERT WITH CHECK (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('reviewer', 'admin'))
    );

CREATE POLICY "Users can view review records" ON review_records
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM applications 
            WHERE applications.id = review_records.application_id 
            AND (applications.applicant_id = auth.uid() OR 
                 EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('reviewer', 'admin')))
        )
    );

-- Digital Certificates: 與申請案件相同的存取權限
CREATE POLICY "Users can view related certificates" ON digital_certificates
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM applications 
            WHERE applications.id = digital_certificates.application_id 
            AND (applications.applicant_id = auth.uid() OR 
                 EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND role IN ('reviewer', 'admin')))
        )
    );

-- ==========================================
-- 觸發器：自動更新 updated_at
-- ==========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- 函數：生成案件編號
-- ==========================================

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

-- ==========================================
-- Storage Buckets 設定說明
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

