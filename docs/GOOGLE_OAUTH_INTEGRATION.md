# Google OAuth 登入整合指南

## 📋 概述

本系統整合了 Google OAuth 2.0 登入功能，讓使用者可以使用 Gmail 帳號快速登入系統，無需另外註冊帳號。

## 🎯 功能特色

- ✅ 使用 Google 帳號一鍵登入
- ✅ 自動建立使用者帳號
- ✅ 同步 Google 使用者資訊（名稱、Email、頭像）
- ✅ 安全的 OAuth 2.0 授權流程
- ✅ JWT Token 認證
- ✅ 與現有系統無縫整合

## 🔧 設定步驟

### 1. Google Cloud Console 設定

#### 1.1 建立專案
1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 建立新專案或選擇現有專案
3. 記下專案 ID

#### 1.2 啟用 Google+ API
1. 在左側選單選擇「API 和服務」→「程式庫」
2. 搜尋 "Google+ API"
3. 點擊「啟用」

#### 1.3 建立 OAuth 2.0 憑證
1. 在左側選單選擇「API 和服務」→「憑證」
2. 點擊「建立憑證」→「OAuth 用戶端 ID」
3. 應用程式類型選擇「網頁應用程式」
4. 設定名稱（例如：災害補助系統）
5. 新增「已授權的 JavaScript 來源」：
   ```
   http://localhost:8080
   https://your-domain.com
   ```
6. 新增「已授權的重新導向 URI」：
   ```
   http://localhost:8080/api/v1/auth/google/callback
   https://your-domain.com/api/v1/auth/google/callback
   ```
7. 點擊「建立」
8. 複製「用戶端 ID」和「用戶端密鑰」

### 2. 環境變數設定

編輯 `.env` 檔案，加入以下設定：

```bash
# Google OAuth 設定
GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret_here
GOOGLE_REDIRECT_URI=http://localhost:8080/api/v1/auth/google/callback
```

**生產環境記得更新 REDIRECT_URI！**

### 3. 安裝相依套件

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

或使用 uv：

```bash
uv pip install google-auth google-auth-oauthlib google-auth-httplib2
```

## 🚀 使用方式

### 方法 1: OAuth 重定向流程（推薦）

這是標準的 OAuth 2.0 流程，適合大多數網頁應用程式。

#### 前端實作

```html
<!-- 登入按鈕 -->
<a href="/api/v1/auth/google/login">
    <button>使用 Google 帳號登入</button>
</a>
```

#### 流程說明

1. 使用者點擊登入按鈕
2. 重定向到 `/api/v1/auth/google/login`
3. 後端產生授權 URL，重定向到 Google
4. 使用者在 Google 頁面授權
5. Google 重定向回 `/api/v1/auth/google/callback?code=...`
6. 後端用 code 換取 access token
7. 取得使用者資訊並建立/更新帳號
8. 產生 JWT token
9. 重定向到前端頁面，並傳遞 token

#### 接收 Token

前端可以透過 URL 參數接收 token：

```javascript
// 在頁面載入時檢查 URL 參數
const urlParams = new URLSearchParams(window.location.search);
const accessToken = urlParams.get('access_token');
const refreshToken = urlParams.get('refresh_token');

if (accessToken) {
    // 儲存 token
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    
    // 清理 URL
    window.history.replaceState({}, document.title, window.location.pathname);
    
    // 取得使用者資訊
    getUserInfo(accessToken);
}
```

### 方法 2: ID Token 直接登入（進階）

適合已經使用 Google Sign-In JavaScript Library 的應用程式。

#### 前端實作

```html
<!-- 載入 Google Sign-In Library -->
<script src="https://accounts.google.com/gsi/client" async defer></script>

<div id="g_id_onload"
     data-client_id="YOUR_CLIENT_ID"
     data-callback="handleCredentialResponse">
</div>
<div class="g_id_signin" data-type="standard"></div>

<script>
async function handleCredentialResponse(response) {
    // response.credential 是 ID Token
    const result = await fetch('/api/v1/auth/google/token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            id_token: response.credential
        })
    });
    
    const data = await result.json();
    
    // 儲存 token
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    
    // 取得使用者資訊
    console.log('User:', data.user);
}
</script>
```

## 📡 API 端點

### GET /api/v1/auth/google/login

開始 Google OAuth 登入流程。

**回應：** 重定向到 Google 授權頁面

---

### GET /api/v1/auth/google/callback

Google OAuth 回調端點（由 Google 自動呼叫）。

**參數：**
- `code` (string): 授權碼
- `state` (string): CSRF 防護參數

**回應：** 重定向到前端頁面，並帶上 access_token 和 refresh_token

---

### POST /api/v1/auth/google/token

使用 Google ID Token 進行登入。

**請求：**
```json
{
    "id_token": "Google ID Token"
}
```

**回應：**
```json
{
    "access_token": "JWT access token",
    "refresh_token": "JWT refresh token",
    "token_type": "bearer",
    "user": {
        "id": "user-uuid",
        "email": "user@gmail.com",
        "full_name": "User Name",
        "role": "applicant",
        "is_verified": true
    },
    "expires_in": 86400
}
```

## 🔐 使用者資料處理

### 自動建立使用者

當使用者首次透過 Google 登入時，系統會自動建立帳號：

```python
{
    "email": "user@gmail.com",           # 從 Google 取得
    "full_name": "User Name",            # 從 Google 取得
    "role": "applicant",                 # 預設為申請人
    "is_active": True,
    "is_verified": False,                # 填寫申請表單後才會驗證
    "id_number": "GOOGLE_xxx",           # 臨時值，表單填寫時更新
    "phone": "",                         # 空字串，表單填寫時更新
    "digital_identity": {
        "provider": "google",
        "google_id": "...",
        "picture": "...",
        "verified_email": true
    }
}
```

### 更新現有使用者

如果使用者已存在（相同 email），系統會：
- 更新 `last_login_at`
- 如果 `full_name` 為空，則從 Google 更新

### 資料填寫流程

使用 Google 登入的使用者在填寫申請表單時：
1. 系統會自動帶入 Email 和姓名（從 Google 取得）
2. 使用者需要填寫：
   - 身分證字號（`id_number`）- 會更新到 users 表
   - 手機號碼（`phone`）- 會更新到 users 表
   - 地址（`address`）- 儲存在 applications 表
   - 其他申請資料
3. 提交表單後，系統會自動更新 users 表的 `id_number` 和 `phone`

## 🧪 測試

### 1. 使用測試頁面

開啟瀏覽器訪問：
```
http://localhost:8080/static/google_login_test.html
```

### 2. 手動測試流程

```bash
# 1. 啟動伺服器
uvicorn main:app --reload

# 2. 在瀏覽器中訪問
open http://localhost:8080/api/v1/auth/google/login

# 3. 授權後會重定向回應用程式
```

### 3. 使用 cURL 測試（ID Token 方式）

```bash
# 先從 Google 取得 ID Token（需使用前端 SDK）
# 然後用 ID Token 呼叫 API

curl -X POST http://localhost:8080/api/v1/auth/google/token \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "YOUR_GOOGLE_ID_TOKEN"
  }'
```

## 🔒 安全性考量

### 1. CSRF 防護

系統使用 `state` 參數防止 CSRF 攻擊：
```python
state = secrets.token_urlsafe(32)
```

### 2. Token 驗證

在生產環境中，應該驗證 Google ID Token 的簽章：

```python
from google.auth.transport import requests
from google.oauth2 import id_token

# 驗證 ID Token
idinfo = id_token.verify_oauth2_token(
    token, 
    requests.Request(), 
    GOOGLE_CLIENT_ID
)
```

### 3. HTTPS

生產環境**必須**使用 HTTPS：
- 保護 OAuth 流程
- 保護 token 傳輸
- Google 要求 OAuth redirect URI 使用 HTTPS

### 4. Token 儲存

前端應安全地儲存 token：
- 使用 `httpOnly` Cookie（最安全）
- 或使用 `localStorage`（較方便但需注意 XSS）
- 永遠不要將 token 暴露在 URL 中（除了內部重定向）

## 📊 資料庫結構

Google 登入的使用者在 `users` 表中的 `digital_identity` 欄位會包含：

```json
{
    "provider": "google",
    "google_id": "103547991597142817347",
    "picture": "https://lh3.googleusercontent.com/...",
    "verified_email": true
}
```

## 🐛 常見問題

### Q1: 出現 "redirect_uri_mismatch" 錯誤

**解決方案：**
1. 確認 Google Console 中的重定向 URI 與程式碼中的一致
2. 確認沒有多餘的斜線或空格
3. 確認協定（http/https）正確

### Q2: 無法取得使用者資訊

**解決方案：**
1. 確認已啟用 Google+ API
2. 確認 OAuth scope 包含 userinfo.email 和 userinfo.profile
3. 檢查 access token 是否有效

### Q3: 使用者 id_number 衝突

**原因：** 系統暫時使用 `GOOGLE_xxx` 作為 id_number

**解決方案：**
1. 要求使用者在第一次申請時提供真實身分證字號
2. 或修改資料庫架構，讓 id_number 可為空

### Q4: 登入後無法存取其他 API

**解決方案：**
1. 確認已將 JWT token 加入請求 header
2. 格式：`Authorization: Bearer {access_token}`
3. 確認 token 未過期

## 🔄 與其他登入方式整合

系統支援多種登入方式：

1. **密碼登入**：`POST /api/v1/auth/login`
2. **Google 登入**：`GET /api/v1/auth/google/login`
3. **數位憑證登入**：`POST /api/v1/auth/digital-id-v2/generate-qr`
4. **TW FidO 登入**：透過完整流程 API

所有登入方式最終都會產生相同格式的 JWT token，可互通使用。

## 📝 開發檢查清單

- [ ] 在 Google Cloud Console 建立 OAuth 憑證
- [ ] 設定環境變數（CLIENT_ID, CLIENT_SECRET）
- [ ] 安裝必要套件
- [ ] 測試登入流程
- [ ] 處理使用者資料補充邏輯
- [ ] 設定生產環境重定向 URI
- [ ] 啟用 HTTPS
- [ ] 實作 token 刷新機制
- [ ] 加入錯誤處理和日誌
- [ ] 撰寫使用者文件

## 🎨 UI/UX 建議

### 登入按鈕設計

遵循 [Google 品牌指南](https://developers.google.com/identity/branding-guidelines)：

```html
<button style="
    background: #4285f4;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
">
    <img src="google-icon.svg" alt="Google" style="width: 24px; vertical-align: middle;">
    使用 Google 帳號登入
</button>
```

### 載入狀態

顯示登入進行中：

```javascript
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}
```

### 錯誤訊息

清楚地顯示錯誤：

```javascript
function showError(message) {
    alert('登入失敗：' + message);
}
```

## 📚 相關資源

- [Google OAuth 2.0 文件](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Web](https://developers.google.com/identity/sign-in/web)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)

## 🎉 完成！

現在你的系統已經整合 Google OAuth 登入功能。使用者可以使用 Gmail 帳號快速登入，無需記住額外的密碼。
