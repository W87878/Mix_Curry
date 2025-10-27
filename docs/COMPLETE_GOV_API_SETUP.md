# 🏛️ 完整政府 API 整合指南

## 📋 更新內容

### 1. 數據庫欄位更新

執行以下 SQL 來添加政府 API 相關欄位：

```bash
# 在 Supabase SQL Editor 中執行
psql < add_gov_api_fields.sql

# 或者直接複製 add_gov_api_fields.sql 的內容到 Supabase Dashboard
```

**新增欄位：**
- `gov_qr_code_data` - 政府發行的 QR Code（Base64）
- `gov_transaction_id` - 政府的 transaction ID
- `gov_deep_link` - Deep link for APP
- `gov_vc_uid` - VC 憑證模板 ID
- `disbursed_at` - 補助發放時間
- `vp_transaction_id` - VP 驗證的 transaction ID

### 2. 後端 API 更新

✅ 已完成：
- `/api/v1/complete-flow/review-and-issue` - 審核+發行憑證
- `/api/v1/complete-flow/generate-vp-qrcode` - 產生 VP QR Code
- `/api/v1/complete-flow/verify-vp` - 驗證 VP

### 3. 前端更新

✅ Admin 界面（admin.html）
- 審核按鈕整合政府發行端 API
- 自動顯示 QR Code modal
- 災民操作步驟說明

🔄 Applicant 界面（applicant.html）
- 需要添加「查看我的數位憑證」功能
- 顯示 QR Code 供掃描

---

## 🚀 完整使用流程

### 災民端流程

#### 步驟 1：提交申請
```
災民登入 → http://localhost:8080/applicant
填寫表單 → 提交申請
```

#### 步驟 2：等待審核
```
狀態：pending → under_review → approved
```

#### 步驟 3：收到 QR Code
```
方式 1：里長發送 QR Code 截圖
方式 2：在「我的申請」頁面查看
```

#### 步驟 4：用 APP 掃描
```
打開「TW FidO 數位憑證皮夾」APP
→ 掃描 QR Code
→ 確認並儲存憑證
```

#### 步驟 5：到 7-11 領取
```
到 7-11 機台
→ 選擇「災害補助領取」
→ 機台產生 VP QR Code
→ 用 APP 掃描
→ 驗證成功後領取補助
```

---

### 里長端流程

#### 步驟 1：登入後台
```
訪問：http://localhost:8080/admin
```

#### 步驟 2：審核申請
```
點擊案件 → 查看詳情
→ 輸入核准金額
→ 點擊「✅ 核准」
```

#### 步驟 3：系統自動處理
```
✅ 審核通過
→ 🚀 呼叫政府發行端 API
→ 📱 產生數位憑證 QR Code
→ 💾 儲存到資料庫
→ 📤 彈出 QR Code modal
```

#### 步驟 4：轉發 QR Code
```
截圖 QR Code modal
→ 透過 Line/Email 發送給災民
或：災民自己在申請頁面查看
```

---

### 7-11 機台流程（未來實作）

```
災民到 7-11
→ 點擊「災害補助領取」
→ 機台呼叫：GET /api/oidvp/qrcode
→ 顯示 VP QR Code
→ 災民用 APP 掃描
→ APP 提交憑證
→ 機台呼叫：POST /api/oidvp/result
→ 驗證成功 → 發放現金
```

---

## 🔧 環境變數設定

確保 `.env` 包含：

```bash
# Supabase
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE=your-service-role-key

# 政府 API Token
ISSUER_API_KEY=bE3uHSqJzz5GSHVHh6PGpTXPyCIjEtHA
VERIFIER_API_KEY=BLrdNlMkYL2vsCvudEsbd7N5tRlX58HS

# VC/VP 設定
GOV_VC_UID=00000000_subsidy_666  # VC 憑證模板 ID
GOV_VP_REF=00000000_subsidy_667  # VP 驗證服務代碼
```

---

## 📊 API 端點說明

### 1. 審核並發行憑證

```http
POST /api/v1/complete-flow/review-and-issue

Body:
{
  "application_id": "uuid",
  "approved": true,
  "review_notes": "審核通過"
}

Response:
{
  "success": true,
  "application_id": "uuid",
  "transaction_id": "TXN_xxx",
  "qr_code": "base64_image",
  "deep_link": "twfido://...",
  "message": "憑證已發行"
}
```

### 2. 產生 VP QR Code（7-11 機台）

```http
POST /api/v1/complete-flow/generate-vp-qrcode

Body:
{
  "ref": "00000000_subsidy_667"
}

Response:
{
  "success": true,
  "qrcode_image": "base64_image",
  "auth_uri": "twfido://...",
  "transaction_id": "xxx"
}
```

### 3. 驗證 VP

```http
POST /api/v1/complete-flow/verify-vp

Body:
{
  "transaction_id": "xxx"
}

Response:
{
  "success": true,
  "verified": true,
  "credential_data": {...}
}
```

---

## ⚠️ 目前狀態

### ✅ 已完成

1. **後端整合**
   - ✅ 政府發行端 API 整合
   - ✅ 政府驗證端 API 整合
   - ✅ 完整流程 API
   - ✅ 自動創建用戶

2. **前端整合**
   - ✅ Admin 界面審核功能
   - ✅ QR Code 顯示 modal
   - ✅ 錯誤處理

3. **數據庫**
   - ✅ Schema 更新 SQL
   - ✅ 新增必要欄位

### ⏳ 待完成

1. **Applicant 界面**
   - 🔄 顯示 QR Code 給災民
   - 🔄 查看憑證狀態

2. **7-11 機台模擬**
   - 🔄 VP QR Code 產生界面
   - 🔄 驗證結果顯示

3. **政府 API**
   - ❌ 發行端 500 錯誤（需政府技術支援）
   - ⏳ vcUid 配置確認

---

## 🧪 測試步驟

### 1. 執行數據庫遷移

```bash
# 在 Supabase Dashboard → SQL Editor
# 複製並執行 add_gov_api_fields.sql
```

### 2. 啟動服務

```bash
uvicorn main:app --reload --port 8080
```

### 3. 測試流程

1. **災民提交申請**
   - 訪問：http://localhost:8080/applicant
   - 填寫並提交表單

2. **里長審核**
   - 訪問：http://localhost:8080/admin
   - 審核申請 → 點擊「核准」
   - 查看彈出的 QR Code modal

3. **檢查資料庫**
   ```sql
   SELECT 
     case_no,
     applicant_name,
     status,
     gov_transaction_id,
     gov_qr_code_data IS NOT NULL as has_qr_code
   FROM applications
   WHERE status = 'approved'
   ORDER BY approved_at DESC
   LIMIT 5;
   ```

---

## 📞 技術支援

### 政府 API 問題

目前發行端 API 返回 **500 錯誤**，需要：

1. 聯絡：**數位發展部**
2. 提供：
   - vcUid: `00000000_subsidy_666`
   - 錯誤碼: `59999`
   - 錯誤訊息: "內部系統發生錯誤"

### 模擬模式

在政府 API 可用前，系統使用**模擬模式**：
- ✅ 完整流程測試
- ✅ QR Code 產生（模擬）
- ✅ 前端整合驗證

---

## 🎉 完成後的效果

一旦政府 API 可用：

```
災民提交申請
    ↓
里長審核通過
    ↓
【真實政府 API】產生數位憑證 QR Code
    ↓
災民用真實 APP 掃描並儲存憑證
    ↓
到 7-11 機台驗證
    ↓
【真實政府 API】驗證憑證
    ↓
發放補助 ✅
```

**完全符合政府標準流程！** 🚀

---

**系統已準備就緒，只等政府 API 配置完成！** ✨

