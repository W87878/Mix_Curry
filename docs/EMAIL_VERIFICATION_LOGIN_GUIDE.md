# Email 驗證登入完整指南

## ✅ 正確的註冊/登入流程

### 🎯 推薦方式：Email 驗證登入（`/api/v1/auth/email/auth`）

這是**最簡單且最安全**的方式，適合所有用戶。

#### 流程說明

```
用戶輸入 Email
    ↓
發送驗證碼到信箱
    ↓
用戶輸入驗證碼
    ↓
驗證成功 → 自動建立/登入帳號
```

#### 詳細步驟

**第一步：請求驗證碼**

```bash
curl -X POST "https://your-domain.com/api/v1/auth/email/auth" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "is_verified": false
  }'
```

**回應範例：**
```json
{
  "success": true,
  "message": "驗證碼已發送到您的 Email",
  "verification_code": "123456"  // 開發環境才會顯示
}
```

**第二步：輸入驗證碼完成驗證**

```bash
curl -X POST "https://your-domain.com/api/v1/auth/email/auth" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "is_verified": true,
    "verification_code": "123456"
  }'
```

**回應範例：**
```json
{
  "success": true,
  "message": "登入成功",
  "user": {
    "id": "uuid-here",
    "email": "user@example.com",
    "full_name": "user",
    "role": "applicant",
    "is_verified": true
  },
  "applications": [],
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

---

### 📋 傳統方式：密碼登入（`/api/v1/auth/login`）

⚠️ **注意**：這個端點**需要用戶已經註冊並設定密碼**。

如果用戶沒有密碼（例如透過 Google 登入或 Email 驗證登入），請使用 `/api/v1/auth/email/auth` 端點。

#### 使用場景

- 用戶已經透過 `/api/v1/auth/register` 註冊並設定密碼
- 用戶想要使用密碼登入

#### 請求範例

```bash
curl -X POST "https://your-domain.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "mypassword123",
    "login_type": "password"
  }'
```

---

### 🔑 Google OAuth 登入

最快速的登入方式，不需要密碼。

#### 流程

```
點擊「使用 Google 登入」
    ↓
重定向到 Google 登入頁面
    ↓
Google 驗證完成
    ↓
自動建立/登入帳號
    ↓
返回應用程式（已登入）
```

#### 使用方式

**前端按鈕：**
```html
<a href="/api/v1/auth/google/login" class="btn-google">
  使用 Google 登入
</a>
```

**或使用 JavaScript：**
```javascript
function loginWithGoogle() {
    window.location.href = '/api/v1/auth/google/login';
}
```

---

## 🚨 常見錯誤處理

### 錯誤 1: `/login` 返回 400 "請提供密碼"

**原因：** 用戶在使用 `/api/v1/auth/login` 端點時沒有提供密碼或提供空密碼。

**解決方案：** 
- 使用 `/api/v1/auth/email/auth` 端點（推薦）
- 或者確保提供有效的密碼

```javascript
// ❌ 錯誤：空密碼
{
  "email": "user@example.com",
  "password": "",
  "login_type": "password"
}

// ✅ 正確：使用 Email 驗證登入
// 步驟 1: 請求驗證碼
{
  "email": "user@example.com",
  "is_verified": false
}

// 步驟 2: 驗證
{
  "email": "user@example.com",
  "is_verified": true,
  "verification_code": "123456"
}
```

### 錯誤 2: "使用者不存在"

**原因：** 使用 `/login` 端點時，資料庫中沒有該用戶。

**解決方案：**
- 使用 `/api/v1/auth/email/auth` 端點（會自動建立帳號）
- 或先使用 `/api/v1/auth/register` 註冊

### 錯誤 3: "此帳號未設定密碼"

**原因：** 用戶透過 Google 或 Email 驗證登入建立的帳號，沒有設定密碼。

**解決方案：**
- 使用 `/api/v1/auth/email/auth` 端點
- 或使用 `/api/v1/auth/google/login`

---

## 📱 前端整合範例

### 完整的 Email 驗證登入流程

```javascript
// 狀態管理
let verificationStep = 1; // 1: 輸入email, 2: 輸入驗證碼
let currentEmail = '';

// 步驟 1: 請求驗證碼
async function requestVerificationCode() {
    const email = document.getElementById('email').value;
    
    if (!email) {
        alert('請輸入 Email');
        return;
    }
    
    currentEmail = email;
    
    try {
        const response = await fetch('/api/v1/auth/email/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                is_verified: false
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('驗證碼已發送到您的信箱！');
            
            // 開發環境顯示驗證碼（生產環境不會有）
            if (data.verification_code) {
                console.log('驗證碼:', data.verification_code);
            }
            
            // 切換到輸入驗證碼的畫面
            verificationStep = 2;
            showVerificationCodeInput();
        } else {
            alert('發送失敗：' + data.message);
        }
    } catch (error) {
        alert('網路錯誤：' + error.message);
    }
}

// 步驟 2: 驗證並登入
async function verifyAndLogin() {
    const code = document.getElementById('verificationCode').value;
    
    if (!code) {
        alert('請輸入驗證碼');
        return;
    }
    
    try {
        const response = await fetch('/api/v1/auth/email/auth', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: currentEmail,
                is_verified: true,
                verification_code: code
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 儲存 Token
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            alert('登入成功！');
            
            // 跳轉到主頁
            window.location.href = '/applicant';
        } else {
            alert('驗證失敗：' + data.message);
        }
    } catch (error) {
        alert('網路錯誤：' + error.message);
    }
}

// UI 切換函數
function showVerificationCodeInput() {
    document.getElementById('emailInput').style.display = 'none';
    document.getElementById('codeInput').style.display = 'block';
}
```

### HTML 範例

```html
<div id="emailInput">
    <h2>Email 登入</h2>
    <input type="email" id="email" placeholder="請輸入 Email">
    <button onclick="requestVerificationCode()">發送驗證碼</button>
</div>

<div id="codeInput" style="display: none;">
    <h2>輸入驗證碼</h2>
    <p>驗證碼已發送到 <span id="emailDisplay"></span></p>
    <input type="text" id="verificationCode" placeholder="請輸入 6 位數驗證碼" maxlength="6">
    <button onclick="verifyAndLogin()">驗證並登入</button>
    <button onclick="requestVerificationCode()">重新發送</button>
</div>
```

---

## 🎯 API 端點總結

| 端點 | 用途 | 需要驗證 | 自動建立帳號 |
|------|------|----------|--------------|
| `/api/v1/auth/email/auth` | **Email 驗證登入（推薦）** | ✅ Email 驗證碼 | ✅ 是 |
| `/api/v1/auth/google/login` | **Google OAuth 登入** | ✅ Google 帳號 | ✅ 是 |
| `/api/v1/auth/register` | 傳統註冊（需填完整資料） | ❌ 否 | ✅ 是 |
| `/api/v1/auth/login` | 傳統密碼登入 | ✅ 密碼 | ❌ 否 |

---

## 💡 建議

**對於大多數用戶：**
- 優先使用 **Email 驗證登入** (`/api/v1/auth/email/auth`)
- 或 **Google 登入** (`/api/v1/auth/google/login`)

**優點：**
- ✅ 不需要記住密碼
- ✅ 更安全（每次都需要驗證）
- ✅ 流程簡單
- ✅ 自動建立帳號

**傳統登入的使用場景：**
- 用戶已經註冊並設定密碼
- 不想每次都接收驗證碼

---

## 📞 技術支援

如有問題，請查看：
- API 文檔：`http://localhost:8080/docs`
- 測試頁面：`/static/email_auth_test.html`
- 完整範例：`/static/applicant.html`
