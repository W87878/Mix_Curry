# 📦 Supabase 設定清單

本文件列出需要在 Supabase 建立的所有資料表和 Storage Buckets。

## 📊 資料庫表單清單

執行 `database_schema.sql` 後，將會建立以下資料表：

### ✅ 1. users (使用者表)
儲存災民、審核員和管理員的帳號資料

**主要欄位**：
- `id` (UUID) - 使用者 ID
- `email` - 電子郵件（唯一）
- `full_name` - 姓名
- `id_number` - 身分證字號（唯一）
- `phone` - 電話
- `role` - 角色（applicant, reviewer, admin）

### ✅ 2. applications (申請案件表)
儲存災民的補助申請案件

**主要欄位**：
- `id` (UUID) - 案件 ID
- `case_no` - 案件編號（自動生成，格式：CASE-2025-00001）
- `applicant_id` - 申請人 ID（外鍵 → users）
- `applicant_name` - 申請人姓名
- `disaster_date` - 災害發生日期
- `disaster_type` - 災害類型（flood, typhoon, earthquake...）
- `damage_description` - 災損描述
- `subsidy_type` - 補助類型
- `status` - 案件狀態（pending, under_review, approved...）
- `requested_amount` - 申請金額
- `approved_amount` - 核准金額

### ✅ 3. damage_photos (災損照片表)
儲存災損照片的元資料

**主要欄位**：
- `id` (UUID) - 照片 ID
- `application_id` - 案件 ID（外鍵 → applications）
- `photo_type` - 照片類型（before_damage, after_damage, site_inspection）
- `storage_path` - Storage 路徑
- `file_name` - 檔案名稱
- `file_size` - 檔案大小
- `description` - 照片說明

### ✅ 4. review_records (審核記錄表)
儲存案件的審核歷程

**主要欄位**：
- `id` (UUID) - 記錄 ID
- `application_id` - 案件 ID（外鍵 → applications）
- `reviewer_id` - 審核員 ID（外鍵 → users）
- `reviewer_name` - 審核員姓名
- `action` - 動作類型
- `previous_status` - 前一狀態
- `new_status` - 新狀態
- `comments` - 審核意見
- `decision_reason` - 核准/駁回理由

### ✅ 5. digital_certificates (數位憑證表)
儲存核發的數位憑證和 QR Code

**主要欄位**：
- `id` (UUID) - 憑證 ID
- `application_id` - 案件 ID（外鍵 → applications）
- `certificate_no` - 憑證編號（唯一）
- `qr_code_data` - QR Code 資料（JSON）
- `qr_code_image_path` - QR Code 圖片路徑
- `issued_amount` - 核發金額
- `is_verified` - 是否已驗證
- `is_disbursed` - 是否已發放
- `disbursement_method` - 發放方式

### ✅ 6. subsidy_items (補助項目表)
儲存申請案件的補助項目明細

**主要欄位**：
- `id` (UUID) - 項目 ID
- `application_id` - 案件 ID（外鍵 → applications）
- `item_category` - 項目分類
- `item_name` - 項目名稱
- `quantity` - 數量
- `total_price` - 總金額
- `approved` - 是否核准
- `approved_amount` - 核准金額

### ✅ 7. system_settings (系統設定表)
儲存系統參數設定

**主要欄位**：
- `id` (UUID) - 設定 ID
- `setting_key` - 設定鍵（唯一）
- `setting_value` - 設定值
- `description` - 說明

## 📁 Storage Buckets 清單

需要建立以下 3 個 Storage Buckets：

### ✅ 1. damage-photos (災損照片)

**設定**：
```
名稱: damage-photos
存取權限: Private (私有)
檔案大小限制: 10 MB
允許的 MIME 類型: image/jpeg, image/png, image/jpg
```

**用途**：
- 儲存災民上傳的災損照片
- 災損前後對比照片

**存取方式**：
- 使用簽名 URL（有效期限）
- 需要透過 API 驗證身份後才能存取

### ✅ 2. qr-codes (QR Code 圖片)

**設定**：
```
名稱: qr-codes
存取權限: Public (公開)
檔案大小限制: 1 MB
允許的 MIME 類型: image/png
```

**用途**：
- 儲存系統生成的 QR Code 圖片
- 用於數位憑證驗證

**存取方式**：
- 公開 URL，可直接存取
- 用於掃描和驗證

### ✅ 3. inspection-photos (現場勘查照片)

**設定**：
```
名稱: inspection-photos
存取權限: Private (私有)
檔案大小限制: 10 MB
允許的 MIME 類型: image/jpeg, image/png, image/jpg
```

**用途**：
- 儲存審核員現場勘查時拍攝的照片
- 作為審核依據

**存取方式**：
- 使用簽名 URL（有效期限）
- 只有審核員和管理員可存取

## 🔒 Row Level Security (RLS) 政策

SQL 腳本已自動設定以下安全政策：

### Users 表
- ✅ 使用者只能查看自己的資料
- ✅ 使用者只能更新自己的資料

### Applications 表
- ✅ 申請人可查看自己的申請案件
- ✅ 審核員和管理員可查看所有案件
- ✅ 申請人只能在 pending 狀態時更新案件
- ✅ 審核員和管理員可更新任何案件

### Damage Photos 表
- ✅ 與申請案件相同的存取權限
- ✅ 申請人可上傳照片到自己的案件

### Review Records 表
- ✅ 只有審核員和管理員可建立審核記錄
- ✅ 與申請案件相同的查看權限

### Digital Certificates 表
- ✅ 與申請案件相同的存取權限
- ✅ 只有審核員和管理員可建立憑證

## 🔧 自訂函數

SQL 腳本已建立以下自訂函數：

### 1. update_updated_at_column()
**用途**：自動更新 `updated_at` 欄位

**觸發器**：
- users 表更新時
- applications 表更新時

### 2. generate_case_no()
**用途**：自動生成案件編號

**格式**：`CASE-{年份}-{序號}`
- 例如：`CASE-2025-00001`

**邏輯**：
- 按年度重新編號
- 序號自動遞增
- 補零至 5 位數

## 📝 建立步驟總結

1. **執行 SQL 腳本**
   ```sql
   -- 在 Supabase Dashboard 的 SQL Editor 執行
   -- 複製 database_schema.sql 的完整內容
   ```

2. **建立 Storage Buckets**
   ```
   1. 點擊 Storage 選單
   2. 建立 damage-photos (Private)
   3. 建立 qr-codes (Public)
   4. 建立 inspection-photos (Private)
   ```

3. **驗證設定**
   ```
   - 檢查 Table Editor 是否有 7 張資料表
   - 檢查 Storage 是否有 3 個 Buckets
   - 檢查 Database > Functions 是否有 2 個函數
   ```

## ✅ 檢查清單

建立完成後，請確認：

- [ ] 7 張資料表已建立
- [ ] 所有索引已建立
- [ ] RLS 政策已啟用
- [ ] 3 個 Storage Buckets 已建立
- [ ] damage-photos 為私有
- [ ] qr-codes 為公開
- [ ] inspection-photos 為私有
- [ ] 觸發器已建立
- [ ] 自訂函數已建立

## 🔍 測試驗證

建立完成後，可以執行以下測試：

```sql
-- 測試 generate_case_no() 函數
SELECT generate_case_no();

-- 查看所有資料表
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- 檢查 RLS 是否啟用
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

## 🆘 常見問題

### Q: 執行 SQL 出現權限錯誤？
A: 確保使用的是 `service_role` 金鑰，而非 `anon` 金鑰。

### Q: Storage Bucket 建立後無法上傳？
A: 檢查 MIME 類型設定是否正確，以及檔案大小是否超過限制。

### Q: RLS 政策導致無法存取資料？
A: 在開發階段，可以暫時關閉 RLS（不建議在生產環境）：
```sql
ALTER TABLE table_name DISABLE ROW LEVEL SECURITY;
```

---

**📚 相關文件**：
- [README.md](README.md) - 專案說明
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - 詳細安裝指南
- [database_schema.sql](database_schema.sql) - 完整 SQL 腳本

