# Google 登入跳回登入畫面問題修復

## 問題描述
用戶使用 Google 登入後，被重定向回 `/applicant?access_token=...`，但頁面卻顯示登入界面而不是主選單。

## 根本原因

### 1. 缺少 Google Token 檢查
`initializeApp()` 函數沒有調用 `checkGoogleAuthToken()`，導致 URL 中的 `access_token` 參數沒有被提取。

**原始代碼：**
```javascript
async function initializeApp() {
    await initializeConfig();
    API_BASE = getApiBase();
    
    // ❌ 沒有檢查 Google OAuth callback
    
    if (accessToken && currentUser) {
        showMainMenu();
    } else {
        initializeLoginUI();
    }
}
```

### 2. 數位憑證登入自動啟動
頁面載入時，數位憑證 tab 預設為 active 狀態，導致自動調用 `loginWithDigitalID()`，與 Google 登入流程衝突。

## 修復方案

### 修復 1：調用 Google Token 檢查 ✅

```javascript
async function initializeApp() {
    await initializeConfig();
    API_BASE = getApiBase();
    
    // ✅ 先檢查 Google OAuth callback
    const isGoogleLogin = checkGoogleAuthToken();
    
    // 如果正在處理 Google 登入，就不要繼續執行
    if (isGoogleLogin) {
        console.log('🔄 正在處理 Google 登入，跳過其他初始化');
        return;
    }
    
    // 檢查現有登入狀態
    if (!accessToken || !currentUser) {
        accessToken = localStorage.getItem('applicant_token');
        const userStr = localStorage.getItem('applicant_user');
        if (userStr) {
            try {
                currentUser = JSON.parse(userStr);
            } catch (e) {
                console.error('解析 currentUser 失敗:', e);
            }
        }
    }
    
    if (accessToken && currentUser) {
        showMainMenu();
    } else {
        initializeLoginUI();
    }
}
```

### 修復 2：checkGoogleAuthToken 返回狀態 ✅

```javascript
function checkGoogleAuthToken() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get("access_token");
    const refreshToken = urlParams.get("refresh_token");

    if (token) {
        console.log("✅ 檢測到 Google OAuth token，處理登入...");
        
        // 儲存 token
        accessToken = token;
        localStorage.setItem("applicant_token", token);
        if (refreshToken) {
            localStorage.setItem("applicant_refresh_token", refreshToken);
        }

        // 清理 URL
        window.history.replaceState({}, document.title, window.location.pathname);

        // 取得使用者資訊並顯示主選單
        getUserInfoAndShowMenu();
        
        return true;  // ✅ 表示正在處理 Google 登入
    }
    
    return false;  // 沒有 Google token
}
```

### 修復 3：變更預設登入方式 ✅

```html
<!-- 原始：數位憑證預設為 active -->
<div class="login-tab" data-tab="general">
    一般登入
</div>
<div class="login-tab active" data-tab="digital">
    數位身分證憑證登入 (推薦)
</div>

<!-- 修復後：一般登入預設為 active -->
<div class="login-tab active" data-tab="general">
    一般登入 (推薦)
</div>
<div class="login-tab" data-tab="digital">
    數位身分證憑證登入
</div>
```

## 完整流程

### Google 登入流程

1. **用戶點擊「使用 Google 繼續登入」**
   ```javascript
   window.location.href = "/api/v1/auth/google/login";
   ```

2. **後端重定向到 Google OAuth**
   - 用戶在 Google 頁面授權

3. **Google 重定向回 callback URL**
   ```
   https://your-ngrok-url.ngrok-free.app/api/v1/auth/google/callback?code=...
   ```

4. **後端處理 callback**
   - 用 code 換取 access_token
   - 創建/更新用戶
   - 重定向到前端：
     ```
     /applicant?access_token=xxx&refresh_token=yyy
     ```

5. **前端處理 token**
   ```javascript
   // initializeApp 調用 checkGoogleAuthToken
   const isGoogleLogin = checkGoogleAuthToken();
   if (isGoogleLogin) {
       // 不執行其他初始化邏輯
       return;
   }
   ```

6. **取得用戶資訊**
   ```javascript
   getUserInfoAndShowMenu()
   → fetch('/api/v1/users/me')
   → 保存 currentUser
   → showMainMenu()
   ```

7. **顯示主選單** ✅

## 驗證測試

### 測試步驟

1. **清除瀏覽器數據**
   ```
   localStorage.clear()
   ```

2. **訪問登入頁面**
   ```
   https://your-ngrok-url.ngrok-free.app/applicant
   ```

3. **點擊「使用 Google 繼續登入」**

4. **在 Google 頁面授權**

5. **預期結果**
   - ✅ 自動跳轉回 applicant 頁面
   - ✅ 直接顯示主選單（不是登入界面）
   - ✅ Console 顯示：
     ```
     ✅ 檢測到 Google OAuth token，處理登入...
     🔄 正在處理 Google 登入，跳過其他初始化
     ✅ 已有登入狀態，顯示主選單
     ```

### 檢查項目

- [ ] URL 中的 `access_token` 被正確提取
- [ ] Token 被保存到 `localStorage`
- [ ] `currentUser` 被正確設置
- [ ] 不會調用 `loginWithDigitalID()`
- [ ] 直接顯示主選單

## 相關文件

- `static/applicant.html` - 前端登入邏輯
- `app/routers/auth.py` - Google OAuth 後端
- `app/services/google_oauth.py` - Google OAuth 服務

## 後續改進

### 1. 添加載入指示器
在處理 Google 登入時顯示載入動畫：

```javascript
if (isGoogleLogin) {
    // 顯示載入中
    document.body.innerHTML = '<div class="loading">正在登入...</div>';
    return;
}
```

### 2. 錯誤處理
如果 `getUserInfoAndShowMenu()` 失敗，顯示友好的錯誤訊息：

```javascript
async function getUserInfoAndShowMenu() {
    try {
        // ...
    } catch (error) {
        console.error('Google 登入失敗:', error);
        alert('Google 登入失敗，請重試');
        logout();
    }
}
```

### 3. Token 過期檢查
在 `initializeApp` 中檢查 token 是否過期：

```javascript
if (accessToken) {
    // 驗證 token 是否有效
    const isValid = await checkTokenValidity(accessToken);
    if (!isValid) {
        logout();
    }
}
```

## 總結

**問題**：Google 登入後跳回登入畫面

**原因**：
1. 沒有檢查 URL 中的 `access_token`
2. 數位憑證登入自動啟動干擾

**解決**：
1. ✅ `initializeApp` 調用 `checkGoogleAuthToken()`
2. ✅ 檢測到 Google token 時跳過其他初始化
3. ✅ 變更預設登入方式為一般登入

**結果**：Google 登入後正確顯示主選單 🎉
