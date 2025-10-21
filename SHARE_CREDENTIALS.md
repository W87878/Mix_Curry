# 🔐 團隊開發者設定指南

## 📋 前置需求

1. Python 3.12+
2. 專案 GitHub 權限
3. Supabase 憑證（向專案管理員索取）

## 🚀 快速開始

### 1. Clone 專案
```bash
git clone <your-repo-url>
cd Mix_Curry
```

### 2. 安裝依賴
```bash
pip install -r requirements.txt
# 或使用 uv
uv pip install -r requirements.txt
```

### 3. 設定環境變數

創建 `.env` 文件（向專案管理員索取以下憑證）：

```env
# Supabase 連接設定
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# JWT 設定
SECRET_KEY=your-secret-key-for-jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 政府 API（沙盒測試）
ISSUER_API_BASE=https://issuer-sandbox.wallet.gov.tw
ISSUER_API_KEY=your-issuer-api-key
VERIFIER_API_BASE=https://verifier-sandbox.wallet.gov.tw
VERIFIER_API_KEY=your-verifier-api-key

# 調試模式
DEBUG=true
```

### 4. 啟動服務器
```bash
uvicorn main:app --reload --port 8000
```

### 5. 訪問介面

- **API 文檔**: http://localhost:8000/docs
- **管理後台**: http://localhost:8000/admin.html
- **災民介面**: http://localhost:8000/applicant.html

## 🔑 如何取得 Supabase 憑證

### 方式 A：從專案管理員取得
專案管理員會提供 `.env` 文件或以下三個 key。

### 方式 B：自己從 Dashboard 複製（需要專案權限）

1. 前往 [Supabase Dashboard](https://supabase.com/dashboard)
2. 選擇專案
3. 點擊左側 **Settings** → **API**
4. 複製以下資訊：
   - **Project URL** → `SUPABASE_URL`
   - **anon public** → `SUPABASE_ANON_KEY`
   - **service_role** → `SUPABASE_SERVICE_ROLE`（⚠️ 保密！）

## ⚠️ 安全注意事項

1. **絕對不要** 把 `.env` 文件提交到 Git
2. **絕對不要** 在前端代碼中使用 `service_role` key
3. **絕對不要** 在公開的地方分享這些 key
4. 定期更換 `SECRET_KEY`

## 🗄️ 資料庫設定

### 初次設定（只需執行一次）

如果是全新的 Supabase 專案，需要執行資料庫遷移：

```bash
# 在 Supabase Dashboard 的 SQL Editor 中執行
# 檔案位置: ./migration/*.sql
```

執行順序：
1. `database_schema.sql` - 創建基本表結構
2. `add_gov_api_fields.sql` - 添加政府 API 欄位

## 📞 聯絡資訊

遇到問題？聯絡：
- 專案管理員: [email]
- GitHub Issues: [repo-url]/issues

## 📚 更多文檔

- [API 整合指南](./COMPLETE_GOV_API_SETUP.md)
- [README](./README.md)

