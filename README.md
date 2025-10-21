# 🌊 災民補助申請系統 (Mix_Curry) V2.0

## 颱風水災受災戶透過數位憑證領取補助

基於政府數位憑證沙盒的災民補助申請管理系統，使用 FastAPI + Supabase 開發。

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg)](https://www.python.org)
[![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E.svg)](https://supabase.com)

---

## 📋 專案簡介

本系統專注於**颱風水災受災戶的補助申請與發放**，旨在簡化災民補助申請流程，從傳統紙本申請（需時 30-60 分鐘）縮短至數位化申請（8-12 分鐘），並**整合政府數位憑證沙盒 API** 實現憑證驗證與發放功能。

### 🎯 V2.0 新功能

- ✅ **數位憑證登入** - 整合政府數位憑證，無密碼安全登入
- ✅ **完整身份驗證系統** - JWT Token + 角色權限管理
- ✅ **區域管理** - 里長只能查看和審核自己轄區的案件
- ✅ **通知系統** - 簡訊 + Email + App 推送通知
- ✅ **銀行 API 整合** - 帳戶驗證、重複申請檢查、交易記錄
- ✅ **補件流程** - 里長可要求災民補充資料或安排現場勘查
- ✅ **完整的前後台分離** - 災民端 + 里長端

### 主要功能

- **🙋 災民申請** - 線上填寫申請表單、上傳災損照片、銀行帳戶驗證
- **👨‍💼 審核管理** - 審核員審核、現場勘查、電子簽核、要求補件
- **📱 數位憑證** - QR Code 憑證生成、驗證、發放
- **📊 統計儀表板** - 即時統計申請案件與補助金額
- **🖼️ 照片管理** - Supabase Storage 整合，支援災損照片上傳
- **🔔 通知系統** - 申請提交、審核結果、補件要求等自動通知
- **🏛️ 區域管理** - 按照里/鄰區域分配審核權限

### 技術架構

- **後端框架**: FastAPI 0.109.0
- **資料庫**: Supabase (PostgreSQL) - 使用 Supabase Client 作為 ORM
- **檔案儲存**: Supabase Storage
- **身份驗證**: JWT Token + BCrypt 密碼加密
- **QR Code 生成**: qrcode + Pillow
- **API 文件**: Swagger UI / ReDoc
- **政府 API 整合**: 
  - 發行端: https://issuer-sandbox.wallet.gov.tw/swaggerui/
  - 驗證端: https://verifier-sandbox.wallet.gov.tw/swaggerui/
- **前端整合**: 支援 React, Vue, Next.js 等前端框架

---

## 📚 完整文件

- **[🌊 完整流程圖](./FLOW_DIAGRAM.md)** - 完整的系統流程圖和架構圖（⭐ 新增！）
- **[🏗️ 系統架構文件](./ARCHITECTURE.md)** - 完整的系統架構圖和資料庫 ER 圖
- **[🎨 前端整合完整指南](./FRONTEND_INTEGRATION_GUIDE.md)** - React/Vue 完整範例（⭐ 新增！）
- **[📘 前端整合指南](./FRONTEND_GUIDE.md)** - 簡化版 API 呼叫範例
- **[🏛️ 政府 API 整合](./GOV_API_INTEGRATION.md)** - 數位憑證沙盒 API 整合說明
- **[🗄️ Supabase 設定](./SUPABASE_SETUP.md)** - 資料庫和 Storage 設定清單
- **[🧪 HTTP 測試檔案](./https/test.http)** - 完整 API 測試集合
- **[🌐 網頁測試介面](http://localhost:8080/test)** - 瀏覽器中直接測試 API
- **[📖 API 文件 (Swagger)](http://localhost:8080/docs)** - 互動式 API 文件

---

## 🚀 快速開始

### 1. 環境需求

- Python 3.10+
- Supabase 帳號（[註冊](https://supabase.com)）

### 2. 安裝依賴

```bash
# 使用 uv（推薦）
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

# 或使用 pip
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. 設定環境變數

建立 `.env` 檔案：

```bash
# Supabase 設定
SUPABASE_URL=your-supabase-project-url
SUPABASE_SERVICE_ROLE=your-supabase-service-role-key
SUPABASE_ANON_KEY=your-supabase-anon-key

# FastAPI 設定
DEBUG=True
SECRET_KEY=your-secret-key-change-in-production

# 數位憑證 API 設定（開發時使用模擬）
TWFIDO_API_URL=https://twfido-sandbox.nat.gov.tw
DIGITAL_ID_API_URL=https://digital-id-sandbox.gov.tw
DIGITAL_ID_API_KEY=your-digital-id-api-key  # 生產環境需申請

# 銀行 API 設定（可選）
BANK_API_URL=https://bank-api.example.com
BANK_API_KEY=your-bank-api-key

# 簡訊/Email 服務設定（可選）
# SMS_API_KEY=your-sms-api-key
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
```

> 💡 在 Supabase Dashboard 的 Settings > API 可以找到您的專案 URL 和金鑰

### 4. 建立資料庫結構

在 Supabase Dashboard 的 SQL Editor 執行 `database_schema.sql`：

1. 登入 Supabase Dashboard
2. 選擇您的專案
3. 點擊左側 **SQL Editor**
4. 複製 `database_schema.sql` 的內容並執行
5. 確認所有資料表和索引建立成功

**新增的資料表：**
- ✅ `districts` - 區域管理（里/鄰）
- ✅ `notifications` - 通知系統
- ✅ `bank_verification_records` - 銀行驗證記錄

### 5. 建立 Storage Buckets

在 Supabase Dashboard 建立以下 Storage Buckets：

1. **damage-photos** (災損照片)
   - Public: `false`
   - File size limit: `10MB`
   - Allowed MIME types: `image/jpeg, image/png`

2. **qr-codes** (QR Code 圖片)
   - Public: `true`
   - File size limit: `1MB`
   - Allowed MIME types: `image/png`

3. **inspection-photos** (現場勘查照片)
   - Public: `false`
   - File size limit: `10MB`
   - Allowed MIME types: `image/jpeg, image/png`

### 6. 管理資料庫（可選）

使用 `command.py` 管理工具：

```bash
# 測試資料庫連線
python command.py test

# 建立測試資料
python command.py create-test-data

# 查看資料庫統計
python command.py stats

# 清除所有資料（小心使用！）
python command.py clear
```

### 7. 啟動服務

```bash
# 開發模式（自動重載）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

API 服務將在 http://localhost:8080 啟動

---

## 📚 API 文件與測試

啟動服務後，可以透過以下網址存取：

- **🌐 網頁測試介面**: http://localhost:8080/test（⭐ 推薦！最簡單的測試方式）
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

---

## 🔌 API 端點

### 身份驗證 (`/api/v1/auth`) - 🆕

- `POST /register` - 註冊新使用者
- `POST /login` - 使用者登入（支援密碼或數位憑證）
- `POST /refresh` - 刷新 Access Token
- `GET /me` - 取得當前使用者資訊
- `POST /verify-digital-id` - 驗證數位身份
- `POST /logout` - 登出

### 使用者管理 (`/api/v1/users`)

- `POST /` - 建立使用者
- `GET /{user_id}` - 取得使用者資料
- `GET /email/{email}` - 根據 Email 查詢使用者
- `GET /id-number/{id_number}` - 根據身分證字號查詢使用者

### 申請案件 (`/api/v1/applications`)

- `POST /` - 建立新申請案件（包含銀行帳戶驗證）
- `GET /{application_id}` - 取得申請案件詳情
- `GET /case-no/{case_no}` - 根據案件編號查詢
- `GET /applicant/{applicant_id}` - 查詢特定申請人的所有案件
- `GET /status/{status}` - 根據狀態查詢案件
- `PATCH /{application_id}` - 更新申請案件

### 審核管理 (`/api/v1/reviews`)

- `POST /` - 建立審核記錄
- `GET /application/{application_id}` - 取得審核記錄
- `POST /approve/{application_id}` - 核准申請（自動發送通知）
- `POST /reject/{application_id}` - 駁回申請（自動發送通知）

### 數位憑證 (`/api/v1/certificates`)

- `POST /` - 建立數位憑證（整合政府發行端 API）
- `GET /{certificate_no}` - 查詢憑證
- `GET /application/{application_id}` - 根據申請案件查詢憑證
- `POST /verify` - 驗證憑證（本地）
- `POST /disburse` - 發放補助
- `POST /scan/{certificate_no}` - 掃描 QR Code（本地）
- `POST /gov/verify-qr` - **使用政府驗證端 API 驗證 QR Code**
- `POST /gov/create-verification-request` - **建立驗證請求（發放窗口使用）**

### 照片管理 (`/api/v1/photos`)

- `POST /upload` - 上傳災損照片
- `POST /upload-multiple` - 批次上傳照片
- `GET /application/{application_id}` - 取得申請案件的所有照片
- `DELETE /{photo_id}` - 刪除照片
- `POST /inspection/upload` - 上傳現場勘查照片

### 區域管理 (`/api/v1/districts`) - 🆕

- `GET /` - 取得區域列表
- `GET /{district_id}` - 取得區域詳情
- `POST /` - 建立新區域（僅管理員）
- `PATCH /{district_id}` - 更新區域資訊（僅管理員）
- `DELETE /{district_id}` - 停用區域（僅管理員）
- `GET /{district_id}/applications` - 取得區域的申請案件
- `GET /{district_id}/stats` - 取得區域統計

### 通知系統 (`/api/v1/notifications`) - 🆕

- `GET /` - 取得通知列表
- `GET /unread-count` - 取得未讀通知數量
- `PATCH /{notification_id}/read` - 標記通知為已讀
- `POST /mark-all-read` - 標記所有通知為已讀
- `GET /types` - 取得支援的通知類型

### 統計資料

- `GET /api/v1/stats` - 取得系統統計資料

---

## 🗂️ 專案結構

```
Mix_Curry/
├── main.py                      # FastAPI 主程式
├── command.py                   # 資料庫管理工具
├── test_api.py                  # API 測試腳本
├── app/                         # 應用程式核心
│   ├── settings.py              # 設定檔
│   ├── models/                  # 資料模型
│   │   ├── database.py          # Supabase 資料庫服務（ORM）
│   │   └── models.py            # Pydantic 資料模型
│   ├── services/                # 服務層
│   │   ├── storage.py           # Supabase Storage 服務
│   │   ├── gov_wallet.py        # 政府數位憑證 API 整合
│   │   ├── auth.py              # 🆕 身份驗證服務
│   │   ├── notifications.py     # 🆕 通知系統服務
│   │   └── bank_api.py          # 🆕 銀行 API 整合服務
│   └── routers/                 # API 路由
│       ├── __init__.py
│       ├── applications.py      # 申請案件 API
│       ├── users.py             # 使用者 API
│       ├── reviews.py           # 審核 API
│       ├── certificates.py      # 憑證 API（整合政府沙盒）
│       ├── photos.py            # 照片上傳 API
│       ├── auth.py              # 🆕 身份驗證 API
│       ├── districts.py         # 🆕 區域管理 API
│       └── notifications.py     # 🆕 通知系統 API
├── database_schema.sql          # 資料庫結構 SQL (V2)
├── requirements.txt             # Python 依賴套件
├── pyproject.toml               # 專案配置檔
├── .env                         # 環境變數（需自行建立）
├── .gitignore
├── README.md                    # 專案說明
├── FLOW_DIAGRAM.md              # 🆕 完整流程圖
├── FRONTEND_INTEGRATION_GUIDE.md # 🆕 前端整合完整指南
├── FRONTEND_GUIDE.md            # 前端整合簡化指南
├── ARCHITECTURE.md              # 系統架構文件
├── SUPABASE_SETUP.md            # Supabase 設定清單
└── GOV_API_INTEGRATION.md       # 政府 API 整合說明
```

---

## 📊 資料庫結構

### 主要資料表

1. **districts** 🆕 - 區域管理（里/鄰）
2. **users** - 使用者（災民、審核員、管理員）
3. **applications** - 申請案件主表
4. **damage_photos** - 災損照片
5. **review_records** - 審核記錄
6. **digital_certificates** - 數位憑證
7. **subsidy_items** - 補助項目明細
8. **notifications** 🆕 - 通知系統
9. **bank_verification_records** 🆕 - 銀行驗證記錄
10. **system_settings** - 系統設定

詳細結構請參考 `database_schema.sql`

---

## 🔐 安全性考量

- ✅ JWT Token 身份驗證 + Refresh Token 機制
- ✅ BCrypt 密碼加密
- ✅ 角色權限管理（災民、里長、管理員）
- ✅ 區域權限隔離（里長只能看自己轄區）
- ✅ Row Level Security (RLS) 已在資料庫層級設定
- ✅ 照片儲存使用私有 Bucket 和簽名 URL
- ✅ API 支援 CORS，生產環境需限制來源網域
- ✅ 整合政府數位憑證 API，憑證驗證符合國家標準
- ✅ 銀行 API 整合，支援帳戶驗證和重複申請檢查
- ⚠️ 生產環境需使用 HTTPS
- ⚠️ 目前使用沙盒環境，正式環境需更換為生產 API

---

## 🏛️ 政府 API 整合

本系統整合了政府數位憑證沙盒 API：

### 發行端 API
- **URL**: https://issuer-sandbox.wallet.gov.tw/swaggerui/
- **功能**: 發行數位憑證、產生 QR Code
- **使用時機**: 災民申請獲得核准時

### 驗證端 API
- **URL**: https://verifier-sandbox.wallet.gov.tw/swaggerui/
- **功能**: 驗證憑證、掃描 QR Code
- **使用時機**: 發放補助窗口驗證災民身份時

詳細整合說明請參考 [GOV_API_INTEGRATION.md](GOV_API_INTEGRATION.md)

---

## 🎓 專題展示建議

1. **展示真實政府表單** - 說明我們完全基於台南市政府實務設計（颱風水災受災戶）
2. **Demo 災民填寫流程** - 展示從 8-12 分鐘完成（vs 紙本 30-60 分鐘）
3. **Demo 審核端介面** - 現場勘查 + 電子簽核流程 + 補件要求
4. **展示數位憑證整合** - **使用政府數位憑證沙盒 API**
   - 發行憑證 → 災民掃描 QR Code → 憑證加入皮夾
   - 發放窗口驗證 → 掃描災民憑證 → 驗證通過 → 發放補助
5. **展示通知系統** - 申請提交、審核結果、補件要求等自動通知
6. **展示區域管理** - 里長只能查看自己轄區的案件
7. **數據對比** - 展示效益評估表

### 🌟 展示亮點

- ✅ **完整整合政府數位憑證沙盒**（發行端 + 驗證端）
- ✅ **符合 W3C Verifiable Credentials 標準**
- ✅ **實現從申請到發放的完整流程**
- ✅ **支援 Fallback 機制**（政府 API 失敗時自動切換本地模式）
- ✅ **完整的身份驗證和權限管理**
- ✅ **區域管理和通知系統**
- ✅ **銀行 API 整合（帳戶驗證、重複申請檢查）**
- ✅ **前後台完全分離**

---

## 🛠️ 開發指南

### API 使用範例

詳細範例請參考：
- [DIGITAL_ID_GUIDE.md](./DIGITAL_ID_GUIDE.md) - **數位憑證登入完整指南** 🆕
- [FRONTEND_INTEGRATION_GUIDE.md](./FRONTEND_INTEGRATION_GUIDE.md) - 完整的 React/Vue 範例
- [FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md) - 簡化版 API 呼叫範例

### 數位憑證登入快速測試

**1. 產生測試用 QR Code：**
```bash
# 訪問以下網址
http://localhost:8080/api/v1/auth/digital-id/generate-test-qr?id_number=A123456789&full_name=測試用戶
```

**2. 使用數位憑證登入：**
- 災民前台：http://localhost:8080/applicant
- 里長後台：http://localhost:8080/admin
- 貼上步驟 1 產生的 QR Code 資料
- 首次使用補充手機號碼即可

**3. 或使用 Email 登入（備用）：**
```bash
# 先用測試頁面註冊帳號
http://localhost:8080/test
```

詳細說明請參考 [DIGITAL_ID_GUIDE.md](./DIGITAL_ID_GUIDE.md)

### 測試流程

```bash
# 1. 清空資料庫
python command.py clear --force

# 2. 建立測試資料
python command.py create-test-data

# 3. 執行測試
python test_api.py

# 4. 查看結果
python command.py stats
```

---

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

---

## 📄 授權

本專案基於台南市政府公開的災民補助申請表單設計，僅供學術研究與專題展示使用。

---

## 📞 聯絡資訊

如有任何問題，歡迎聯絡開發團隊。

---

**🚀 V2.0 已完成！可以直接用於專題報告或實際部署！**

### 版本歷史

- **V2.0** (2025-10) - 新增身份驗證、區域管理、通知系統、銀行 API 整合
- **V1.0** (2025-09) - 基本申請、審核、憑證功能
