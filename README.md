# 🌊 災民補助申請系統 (Mix_Curry)

## 颱風水災受災戶透過數位憑證領取補助

基於政府數位憑證沙盒的災民補助申請管理系統，使用 FastAPI + Supabase 開發。

## 📋 專案簡介

本系統專注於**颱風水災受災戶的補助申請與發放**，旨在簡化災民補助申請流程，從傳統紙本申請（需時 30-60 分鐘）縮短至數位化申請（8-12 分鐘），並**整合政府數位憑證沙盒 API** 實現憑證驗證與發放功能。

### 主要功能

- **🙋 災民申請** - 線上填寫申請表單、上傳災損照片
- **👨‍💼 審核管理** - 審核員審核、現場勘查、電子簽核
- **📱 數位憑證** - QR Code 憑證生成、驗證、發放
- **📊 統計儀表板** - 即時統計申請案件與補助金額
- **🖼️ 照片管理** - Supabase Storage 整合，支援災損照片上傳

### 技術架構

- **後端框架**: FastAPI 0.109.0
- **資料庫**: Supabase (PostgreSQL) - 使用 Supabase Client 作為 ORM
- **檔案儲存**: Supabase Storage
- **QR Code 生成**: qrcode + Pillow
- **API 文件**: Swagger UI / ReDoc
- **政府 API 整合**: 
  - 發行端: https://issuer-sandbox.wallet.gov.tw/swaggerui/
  - 驗證端: https://verifier-sandbox.wallet.gov.tw/swaggerui/
- **前端整合**: 支援 React, Vue, Next.js 等前端框架（詳見 [前端整合指南](./FRONTEND_GUIDE.md)）

## 📚 完整文件

- **[🏗️ 系統架構文件](./ARCHITECTURE.md)** - 完整的系統架構圖和資料庫 ER 圖（⭐ 新增！）
- **[前端整合指南](./FRONTEND_GUIDE.md)** - React/Vue/Next.js 呼叫 API 的完整範例
- **[政府 API 整合](./GOV_API_INTEGRATION.md)** - 數位憑證沙盒 API 整合說明
- **[HTTP 測試檔案](./https/test.http)** - 完整 API 測試集合
- **[網頁測試介面](http://localhost:8000/test)** - 瀏覽器中直接測試 API（需先啟動服務）
- **[API 文件 (Swagger)](http://localhost:8000/docs)** - 互動式 API 文件

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
```

> 💡 在 Supabase Dashboard 的 Settings > API 可以找到您的專案 URL 和金鑰

### 4. 建立資料庫結構

在 Supabase Dashboard 的 SQL Editor 執行 `database_schema.sql`：

1. 登入 Supabase Dashboard
2. 選擇您的專案
3. 點擊左側 **SQL Editor**
4. 複製 `database_schema.sql` 的內容並執行
5. 確認所有資料表和索引建立成功

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

更多指令請參考下方「管理工具」章節。

### 7. 啟動服務

```bash
# 開發模式（自動重載）
python main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API 服務將在 http://localhost:8000 啟動

## 📚 API 文件與測試

啟動服務後，可以透過以下網址存取：

- **🌐 網頁測試介面**: http://localhost:8000/test（⭐ 推薦！最簡單的測試方式）
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 快速測試 API

使用內建的網頁測試介面是最簡單的方式：

1. 啟動服務：`python main.py`
2. 開啟瀏覽器：http://localhost:8000/test
3. 在網頁介面中依序測試：
   - ✅ 建立使用者
   - ✅ 建立申請案件
   - ✅ 上傳災損照片
   - ✅ 查詢案件資料
   - ✅ 查看系統統計

測試頁面會自動處理 ID 的傳遞，讓您輕鬆完成完整流程測試！

## 🗂️ 專案結構

```
Mix_Curry/
├── main.py                      # FastAPI 主程式
├── command.py                   # 🆕 資料庫管理工具
├── test_api.py                  # API 測試腳本
├── app/                         # 應用程式核心
│   ├── settings.py              # 設定檔
│   ├── models/                  # 資料模型
│   │   ├── database.py          # Supabase 資料庫服務（ORM）
│   │   └── models.py            # Pydantic 資料模型
│   ├── services/                # 服務層
│   │   ├── storage.py           # Supabase Storage 服務
│   │   └── gov_wallet.py        # 政府數位憑證 API 整合
│   └── routers/                 # API 路由
│       ├── __init__.py
│       ├── applications.py      # 申請案件 API
│       ├── users.py             # 使用者 API
│       ├── reviews.py           # 審核 API
│       ├── certificates.py      # 憑證 API（整合政府沙盒）
│       └── photos.py            # 照片上傳 API
├── database_schema.sql          # 資料庫結構 SQL
├── requirements.txt             # Python 依賴套件
├── pyproject.toml               # 專案配置檔
├── .env                         # 環境變數（需自行建立）
├── .gitignore
├── README.md                    # 專案說明
├── SETUP_GUIDE.md               # 詳細安裝指南
├── SUPABASE_SETUP.md            # Supabase 設定清單
└── GOV_API_INTEGRATION.md       # 政府 API 整合說明
```

## 📊 資料庫結構

### 主要資料表

1. **users** - 使用者（災民、審核員、管理員）
2. **applications** - 申請案件主表
3. **damage_photos** - 災損照片
4. **review_records** - 審核記錄
5. **digital_certificates** - 數位憑證
6. **subsidy_items** - 補助項目明細

詳細結構請參考 `database_schema.sql`

## 🔌 API 端點

### 使用者管理 (`/api/v1/users`)

- `POST /` - 建立使用者
- `GET /{user_id}` - 取得使用者資料
- `GET /email/{email}` - 根據 Email 查詢使用者
- `GET /id-number/{id_number}` - 根據身分證字號查詢使用者

### 申請案件 (`/api/v1/applications`)

- `POST /` - 建立新申請案件
- `GET /{application_id}` - 取得申請案件詳情
- `GET /case-no/{case_no}` - 根據案件編號查詢
- `GET /applicant/{applicant_id}` - 查詢特定申請人的所有案件
- `GET /status/{status}` - 根據狀態查詢案件
- `PATCH /{application_id}` - 更新申請案件

### 審核管理 (`/api/v1/reviews`)

- `POST /` - 建立審核記錄
- `GET /application/{application_id}` - 取得審核記錄
- `POST /approve/{application_id}` - 核准申請
- `POST /reject/{application_id}` - 駁回申請

### 數位憑證 (`/api/v1/certificates`) - 整合政府沙盒 API

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

### 統計資料

- `GET /api/v1/stats` - 取得系統統計資料

## 🛠️ 管理工具 (command.py)

專案提供完整的資料庫管理工具 `command.py`。

### 可用指令

#### 1. 測試資料庫連線
```bash
python command.py test
```
測試 Supabase 連線和 RPC 函數。

#### 2. 建立測試資料
```bash
python command.py create-test-data
```
自動建立：
- ✅ 1 位測試災民
- ✅ 1 位測試審核員  
- ✅ 1 個測試申請案件
- ✅ 1 筆審核記錄

#### 3. 查看統計資訊
```bash
python command.py stats
```
顯示所有資料表的筆數和案件狀態分佈。

#### 4. 清除資料表
```bash
# 清除所有資料表（會要求確認）
python command.py clear

# 強制清除（不要求確認）
python command.py clear --force

# 清除指定資料表
python command.py clear-table users
python command.py clear-table applications
```

### 快速開發流程

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

## 🧪 測試

### 方法 1：使用管理工具
```bash
# 建立測試資料
python command.py create-test-data

# 查看統計
python command.py stats
```

### 方法 2：使用測試腳本
```bash
python test_api.py
```

### 方法 3：使用 Swagger UI
訪問 http://localhost:8000/docs

### 方法 4：手動測試政府 API
- 發行端 Swagger: https://issuer-sandbox.wallet.gov.tw/swaggerui/
- 驗證端 Swagger: https://verifier-sandbox.wallet.gov.tw/swaggerui/

## 🎓 專題展示建議

1. **展示真實政府表單** - 說明我們完全基於台南市政府實務設計（颱風水災受災戶）
2. **Demo 災民填寫流程** - 展示從 8-12 分鐘完成（vs 紙本 30-60 分鐘）
3. **Demo 審核端介面** - 現場勘查 + 電子簽核流程
4. **展示數位憑證整合** - **使用政府數位憑證沙盒 API**
   - 發行憑證 → 災民掃描 QR Code → 憑證加入皮夾
   - 發放窗口驗證 → 掃描災民憑證 → 驗證通過 → 發放補助
5. **數據對比** - 展示效益評估表

### 🌟 展示亮點

- ✅ **完整整合政府數位憑證沙盒**（發行端 + 驗證端）
- ✅ **符合 W3C Verifiable Credentials 標準**
- ✅ **實現從申請到發放的完整流程**
- ✅ **支援 Fallback 機制**（政府 API 失敗時自動切換本地模式）

## 💡 使用範例

### 快速開始（使用管理工具）

```bash
# 1. 建立測試資料
python command.py create-test-data

# 2. 查看 API 文件
open http://localhost:8000/docs

# 3. 執行測試腳本
python test_api.py
```

### API 使用範例

#### 建立使用者

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "phone": "0912345678",
    "full_name": "王小明",
    "id_number": "A123456789",
    "role": "applicant"
  }'
```

### 建立申請案件

```bash
curl -X POST "http://localhost:8000/api/v1/applications/" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "user-uuid",
    "applicant_name": "王小明",
    "id_number": "A123456789",
    "phone": "0912345678",
    "address": "台南市中西區民權路100號",
    "disaster_date": "2025-10-10",
    "disaster_type": "flood",
    "damage_description": "一樓淹水約50公分，家具電器受損",
    "damage_location": "台南市中西區民權路100號1樓",
    "subsidy_type": "housing",
    "requested_amount": 50000
  }'
```

### 上傳災損照片

```bash
curl -X POST "http://localhost:8000/api/v1/photos/upload" \
  -F "application_id=application-uuid" \
  -F "photo_type=before_damage" \
  -F "description=一樓客廳淹水情形" \
  -F "file=@photo.jpg"
```

## 🔐 安全性考量

- ✅ Row Level Security (RLS) 已在資料庫層級設定
- ✅ 照片儲存使用私有 Bucket 和簽名 URL
- ✅ API 支援 CORS，生產環境需限制來源網域
- ✅ 整合政府數位憑證 API，憑證驗證符合國家標準
- ⚠️ 建議加入 JWT 身份驗證機制
- ⚠️ 生產環境需使用 HTTPS
- ⚠️ 目前使用沙盒環境，正式環境需更換為生產 API

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

## 🤝 貢獻

歡迎提交 Issue 或 Pull Request！

## 📄 授權

本專案基於台南市政府公開的災民補助申請表單設計，僅供學術研究與專題展示使用。

## 📞 聯絡資訊

如有任何問題，歡迎聯絡開發團隊。

---

**🚀 所有設計都已完成，可以直接進入開發或用於專題報告！**