# ✅ 憑證歷史記錄功能 - 部署檢查清單

## 📋 部署前檢查

### 1. 資料庫 Migration
- [ ] 備份現有資料庫
- [ ] 執行 migration script
  ```bash
  # 選項 A: 完整 schema（新系統）
  psql -U postgres -d your_database -f migration/unified_schema.sql
  
  # 選項 B: 僅添加 history table（現有系統）
  psql -U postgres -d your_database -f migration/add_credential_history_table.sql
  ```
- [ ] 驗證 table 建立成功
  ```sql
  \d credential_history
  SELECT * FROM credential_history LIMIT 1;
  ```
- [ ] 驗證索引建立成功
  ```sql
  \di credential_history*
  ```
- [ ] 驗證 RLS 政策建立成功
  ```sql
  SELECT * FROM pg_policies WHERE tablename = 'credential_history';
  ```

### 2. 後端程式碼
- [x] `app/routers/complete_flow.py` 已更新
  - [x] `record_credential_history()` 函數已添加
  - [x] 憑證發行時自動記錄
  - [x] 憑證驗證時自動記錄
  - [x] API endpoints 已添加
- [ ] 重啟後端服務
  ```bash
  # 如果使用 systemd
  sudo systemctl restart your-app-service
  
  # 如果使用 docker
  docker-compose restart backend
  
  # 如果使用 uvicorn
  pkill -f uvicorn
  uvicorn main:app --reload
  ```
- [ ] 檢查服務是否正常運行
  ```bash
  curl http://localhost:8000/api/v1/complete-flow/health
  ```

### 3. 前端程式碼
- [x] `static/applicant.html` 已更新
  - [x] 憑證領取成功時調用記錄 API
- [ ] 清除瀏覽器快取
- [ ] 測試前端功能

### 4. 環境變數檢查
- [ ] `SUPABASE_URL` 已設定
- [ ] `SUPABASE_SERVICE_ROLE` 已設定（需要 service_role 權限才能插入記錄）
- [ ] `.env` 文件已更新

### 5. 權限檢查
- [ ] 確認 Supabase service role key 有足夠權限
- [ ] 確認 RLS 政策正確設定
- [ ] 測試不同角色的存取權限
  - [ ] 一般使用者只能查看自己的記錄
  - [ ] 管理員可以查看所有記錄

## 🧪 功能測試

### 測試 1: 憑證發行記錄
- [ ] 建立新的申請案件
- [ ] 里長審核通過
- [ ] 檢查是否自動建立 history 記錄
  ```sql
  SELECT * FROM credential_history 
  WHERE action_type = 'credential_issued' 
  ORDER BY created_at DESC LIMIT 1;
  ```
- [ ] 驗證記錄內容正確
  - [ ] `issuer_organization` 有值
  - [ ] `verifier_organization` 為 NULL
  - [ ] `status = 'issued'`

### 測試 2: 憑證領取記錄
- [ ] 使用者掃描 QR Code
- [ ] 前端偵測到領取成功
- [ ] 檢查是否調用記錄 API
- [ ] 檢查瀏覽器 console 是否有成功訊息
- [ ] 驗證資料庫記錄

### 測試 3: 憑證驗證記錄（711 機台）
- [ ] 模擬 711 機台驗證
- [ ] 驗證成功後檢查 history 記錄
  ```sql
  SELECT * FROM credential_history 
  WHERE action_type = 'credential_verified' 
  ORDER BY created_at DESC LIMIT 1;
  ```
- [ ] 驗證記錄內容正確
  - [ ] `issuer_organization` 為 NULL
  - [ ] `verifier_organization` 有值
  - [ ] `status = 'verified'`

### 測試 4: API 端點
- [ ] 測試查詢申請歷史
  ```bash
  curl http://localhost:8000/api/v1/complete-flow/credential-history/{application_id}
  ```
- [ ] 測試查詢使用者歷史
  ```bash
  curl http://localhost:8000/api/v1/complete-flow/credential-history-by-user/{user_id}
  ```
- [ ] 測試統計 API
  ```bash
  curl "http://localhost:8000/api/v1/complete-flow/credential-history-stats?start_date=2024-01-01&end_date=2024-12-31"
  ```

### 測試 5: 安全性測試
- [ ] 一般使用者嘗試查看其他人的記錄（應該失敗）
- [ ] 管理員查看所有記錄（應該成功）
- [ ] 未登入使用者嘗試查詢（應該失敗）

## 📊 監控和日誌

### 檢查項目
- [ ] 檢查後端日誌是否有記錄相關訊息
  ```bash
  # 查看最近的日誌
  tail -f /var/log/your-app/app.log | grep "credential_history"
  ```
- [ ] 檢查是否有錯誤訊息
- [ ] 監控 API 回應時間
- [ ] 監控資料庫查詢效能

## 📈 效能檢查

### 查詢效能
- [ ] 檢查索引是否被使用
  ```sql
  EXPLAIN ANALYZE 
  SELECT * FROM credential_history 
  WHERE application_id = 'xxx' 
  ORDER BY action_time DESC;
  ```
- [ ] 確認查詢時間在可接受範圍內（< 100ms）

### 資料量預估
- [ ] 預估每日新增記錄數量
- [ ] 評估是否需要資料清理政策
- [ ] 考慮是否需要分區表（partition）

## 🔍 驗證清單

### 資料完整性
- [ ] 檢查所有必填欄位都有值
- [ ] 檢查 `issuer_organization` 和 `verifier_organization` 互斥
- [ ] 檢查時間戳記正確
- [ ] 檢查關聯的 application_id 和 user_id 存在

### 統計數據
- [ ] 執行統計查詢，驗證數字合理
  ```sql
  SELECT 
    action_type,
    status,
    COUNT(*) as count
  FROM credential_history
  GROUP BY action_type, status;
  ```

## 📝 文件檢查

- [x] `CREDENTIAL_HISTORY_GUIDE.md` 已建立
- [x] `CREDENTIAL_HISTORY_IMPLEMENTATION.md` 已建立
- [x] API 文件已更新
- [ ] README.md 已更新（如需要）
- [ ] 團隊成員已通知

## 🚀 上線步驟

### 生產環境部署
1. [ ] 在測試環境完成所有測試
2. [ ] 在 staging 環境驗證
3. [ ] 備份生產環境資料庫
4. [ ] 停機維護通知（如需要）
5. [ ] 執行 migration
6. [ ] 部署新版本程式碼
7. [ ] 驗證功能正常
8. [ ] 監控系統運行狀況
9. [ ] 通知使用者功能上線

## ⚠️ 回滾計畫

如果部署失敗，執行以下步驟：

1. [ ] 回滾資料庫（如果已執行 migration）
   ```sql
   DROP TABLE IF EXISTS credential_history CASCADE;
   ```
2. [ ] 回滾程式碼版本
3. [ ] 重啟服務
4. [ ] 驗證系統恢復正常
5. [ ] 記錄問題並分析原因

## 📞 支援資訊

- 技術文件: `docs/CREDENTIAL_HISTORY_GUIDE.md`
- 實作說明: `docs/CREDENTIAL_HISTORY_IMPLEMENTATION.md`
- 測試腳本: `tests/test_credential_history.py`
- Migration 腳本: `migration/add_credential_history_table.sql`

## ✅ 最終檢查

- [ ] 所有測試通過
- [ ] 文件已更新
- [ ] 團隊成員已培訓
- [ ] 監控已設定
- [ ] 回滾計畫已準備
- [ ] 🎉 準備上線！

---

**檢查人員**: __________
**檢查日期**: __________
**部署日期**: __________
**備註**: __________
