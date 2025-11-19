-- ==========================================
-- 災民補助申請系統 - 刪除所有資料表
-- ⚠️ 危險操作！請謹慎使用！
-- 生成時間: 2025-10-27 11:09:58
-- ==========================================

-- 停用觸發器
DROP TRIGGER IF EXISTS update_districts_updated_at ON districts;
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
DROP TRIGGER IF EXISTS trigger_auto_assign_reviewer ON applications;

-- 刪除函數
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP FUNCTION IF EXISTS generate_case_no();
DROP FUNCTION IF EXISTS auto_assign_reviewer();

-- 刪除資料表（按照依賴順序）
DROP TABLE IF EXISTS subsidy_items CASCADE;
DROP TABLE IF EXISTS bank_verification_records CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS digital_certificates CASCADE;
DROP TABLE IF EXISTS review_records CASCADE;
DROP TABLE IF EXISTS damage_photos CASCADE;
DROP TABLE IF EXISTS applications CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS districts CASCADE;
DROP TABLE IF EXISTS system_settings CASCADE;
DROP TABLE IF EXISTS credential_history CASCADE;

-- ==========================================
-- 完成
-- ==========================================
