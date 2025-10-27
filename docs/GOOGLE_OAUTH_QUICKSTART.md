# Google OAuth 登入 - 快速開始指南

## 🚀 5 分鐘快速設定

### 步驟 1: 安裝相依套件

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

### 步驟 2: Google Cloud Console 設定

1. 前往 https://console.cloud.google.com/
2. 建立新專案（或選擇現有專案）
3. 啟用 Google+ API：
   - API 和服務 → 程式庫 → 搜尋 "Google+ API" → 啟用
4. 建立 OAuth 憑證：
   - API 和服務 → 憑證 → 建立憑證 → OAuth 用戶端 ID
   - 應用程式類型：網頁應用程式
   - 已授權的重新導向 URI：
     ```
     http://localhost:8080/api/v1/auth/google/callback
     ```
5. 複製「用戶端 ID」和「用戶端密鑰」

### 步驟 3: 設定環境變數

編輯 `.env` 檔案：

```bash
# 貼上你的憑證
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8080/api/v1/auth/google/callback
```

### 步驟 4: 啟動伺服器

```bash
uvicorn main:app --reload
```

### 步驟 5: 測試

在瀏覽器中開啟：
```
http://localhost:8080/static/google_login_test.html
```

點擊「使用 Google 帳號登入」按鈕！

## ✅ 驗證設定

執行檢查腳本：

```bash
python3 tests/test_google_oauth.py
```

應該看到所有項目都是 ✅

## 📋 API 端點

### 登入
```
GET /api/v1/auth/google/login
```

### 回調（自動）
```
GET /api/v1/auth/google/callback
```

### Token 登入
```
POST /api/v1/auth/google/token
Body: {"id_token": "..."}
```

## 🔧 前端整合

### HTML 按鈕

```html
<a href="/api/v1/auth/google/login">
    <button>使用 Google 帳號登入</button>
</a>
```

### JavaScript 處理

```javascript
// 檢查登入後的 token
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('access_token');

if (token) {
    localStorage.setItem('access_token', token);
    // 取得使用者資訊
    fetch('/api/v1/users/me', {
        headers: {'Authorization': `Bearer ${token}`}
    });
}
```

## 🐛 常見問題

### redirect_uri_mismatch
→ 確認 Google Console 中的重定向 URI 與 .env 中的完全一致

### 未設定 GOOGLE_CLIENT_ID
→ 檢查 .env 檔案是否正確設定

### 無法取得使用者資訊
→ 確認已啟用 Google+ API

## 📚 完整文件

查看 `docs/GOOGLE_OAUTH_INTEGRATION.md` 了解更多詳情。

## 🎉 完成！

現在使用者可以使用 Gmail 帳號登入你的系統了！
