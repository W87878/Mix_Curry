# 前端 Email 驗證登入整合指南

## 📋 完整流程

### 第一步：發送驗證碼

用戶點擊「註冊」或「登入」，輸入 Email 後：

```javascript
// 調用後端 API 發送驗證碼
async function sendVerificationCode(email) {
    try {
        const response = await fetch('/api/v1/auth/email/auth', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                is_verified: false
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 後端會回傳驗證碼
            const verificationCode = data.verification_code;
            console.log('收到驗證碼:', verificationCode);
            
            // 儲存驗證碼（用於比對）
            localStorage.setItem('verification_code', verificationCode);
            localStorage.setItem('verification_email', email);
            
            // 開始倒數計時（3分鐘）
            startCountdown(180); // 180 秒 = 3 分鐘
            
            // 顯示驗證碼輸入框
            showVerificationCodeInput();
            
            return { success: true, code: verificationCode };
        } else {
            throw new Error(data.message || '發送驗證碼失敗');
        }
    } catch (error) {
        console.error('發送驗證碼失敗:', error);
        alert('發送驗證碼失敗：' + error.message);
        return { success: false, error: error.message };
    }
}
```

### 第二步：前端倒數計時

```javascript
let countdownTimer = null;

function startCountdown(seconds) {
    // 清除之前的計時器
    if (countdownTimer) {
        clearInterval(countdownTimer);
    }
    
    let remaining = seconds;
    const countdownElement = document.getElementById('countdown');
    
    // 更新顯示
    function updateDisplay() {
        const minutes = Math.floor(remaining / 60);
        const secs = remaining % 60;
        countdownElement.textContent = `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
    
    updateDisplay();
    
    // 每秒更新
    countdownTimer = setInterval(() => {
        remaining--;
        updateDisplay();
        
        if (remaining <= 0) {
            clearInterval(countdownTimer);
            countdownElement.textContent = '驗證碼已過期';
            // 可以顯示「重新發送」按鈕
            showResendButton();
        }
    }, 1000);
}
```

### 第三步：前端驗證碼比對

```javascript
async function verifyAndLogin(userInputCode) {
    try {
        // 從 localStorage 取得後端回傳的驗證碼
        const correctCode = localStorage.getItem('verification_code');
        const email = localStorage.getItem('verification_email');
        
        if (!correctCode || !email) {
            throw new Error('請先發送驗證碼');
        }
        
        // 前端比對驗證碼
        const isCorrect = (userInputCode === correctCode);
        
        // 調用登入 API
        const response = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                login_type: 'password',
                verify: isCorrect  // true = 驗證成功, false = 驗證失敗
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.access_token) {
            // 登入成功
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            
            // 清除驗證碼
            localStorage.removeItem('verification_code');
            localStorage.removeItem('verification_email');
            
            // 跳轉到主頁面
            window.location.href = '/applicant';
            
            return { success: true, user: data.user };
        } else {
            // 驗證失敗
            throw new Error(data.detail?.message || '驗證碼錯誤');
        }
    } catch (error) {
        console.error('驗證失敗:', error);
        alert('驗證失敗：' + error.message);
        return { success: false, error: error.message };
    }
}
```

### 第四步：重新發送驗證碼

```javascript
async function resendVerificationCode() {
    const email = localStorage.getItem('verification_email');
    
    if (!email) {
        alert('請先輸入 Email');
        return;
    }
    
    try {
        const response = await fetch('/api/v1/auth/email/resend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // 儲存新的驗證碼
            localStorage.setItem('verification_code', data.verification_code);
            
            // 重新開始倒數
            startCountdown(180);
            
            alert('驗證碼已重新發送');
        } else {
            throw new Error(data.message || '重新發送失敗');
        }
    } catch (error) {
        console.error('重新發送失敗:', error);
        alert('重新發送失敗：' + error.message);
    }
}
```

## 🎨 完整 HTML 範例

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email 驗證登入</title>
    <style>
        .verification-step {
            max-width: 400px;
            margin: 50px auto;
            padding: 30px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .input-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        input {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
        }
        button:hover {
            background: #45a049;
        }
        button.secondary {
            background: #2196F3;
            margin-top: 10px;
        }
        button.secondary:hover {
            background: #0b7dda;
        }
        .countdown {
            text-align: center;
            font-size: 24px;
            color: #f44336;
            margin: 20px 0;
        }
        .hidden {
            display: none;
        }
    </style>
</head>
<body>
    <!-- 步驟 1：輸入 Email -->
    <div id="step1" class="verification-step">
        <h2>Email 驗證登入</h2>
        <div class="input-group">
            <label>Email 地址</label>
            <input type="email" id="emailInput" placeholder="請輸入您的 Email">
        </div>
        <button onclick="handleSendCode()">發送驗證碼</button>
    </div>

    <!-- 步驟 2：輸入驗證碼 -->
    <div id="step2" class="verification-step hidden">
        <h2>輸入驗證碼</h2>
        <p>驗證碼已發送到您的 Email</p>
        <div class="countdown" id="countdown">3:00</div>
        <div class="input-group">
            <label>驗證碼</label>
            <input type="text" id="codeInput" placeholder="請輸入 6 位數驗證碼" maxlength="6">
        </div>
        <button onclick="handleVerify()">驗證並登入</button>
        <button class="secondary" onclick="handleResend()">重新發送驗證碼</button>
    </div>

    <script>
        let countdownTimer = null;

        // 發送驗證碼
        async function handleSendCode() {
            const email = document.getElementById('emailInput').value;
            
            if (!email || !email.includes('@')) {
                alert('請輸入有效的 Email');
                return;
            }

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
                    // 儲存驗證碼和 Email
                    localStorage.setItem('verification_code', data.verification_code);
                    localStorage.setItem('verification_email', email);
                    
                    // 顯示第二步
                    document.getElementById('step1').classList.add('hidden');
                    document.getElementById('step2').classList.remove('hidden');
                    
                    // 開始倒數
                    startCountdown(180);
                    
                    alert('驗證碼已發送！');
                } else {
                    throw new Error(data.message || '發送失敗');
                }
            } catch (error) {
                console.error(error);
                alert('發送失敗：' + error.message);
            }
        }

        // 倒數計時
        function startCountdown(seconds) {
            if (countdownTimer) clearInterval(countdownTimer);
            
            let remaining = seconds;
            const display = document.getElementById('countdown');
            
            function update() {
                const min = Math.floor(remaining / 60);
                const sec = remaining % 60;
                display.textContent = `${min}:${sec.toString().padStart(2, '0')}`;
            }
            
            update();
            countdownTimer = setInterval(() => {
                remaining--;
                update();
                if (remaining <= 0) {
                    clearInterval(countdownTimer);
                    display.textContent = '驗證碼已過期';
                }
            }, 1000);
        }

        // 驗證並登入
        async function handleVerify() {
            const userCode = document.getElementById('codeInput').value;
            const correctCode = localStorage.getItem('verification_code');
            const email = localStorage.getItem('verification_email');

            if (!userCode) {
                alert('請輸入驗證碼');
                return;
            }

            // 前端比對
            const isCorrect = (userCode === correctCode);

            try {
                const response = await fetch('/api/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        email: email,
                        login_type: 'password',
                        verify: isCorrect
                    })
                });

                const data = await response.json();

                if (response.ok && data.access_token) {
                    // 成功
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('refresh_token', data.refresh_token);
                    alert('登入成功！');
                    window.location.href = '/applicant';
                } else {
                    alert('驗證碼錯誤，請重新輸入');
                }
            } catch (error) {
                console.error(error);
                alert('登入失敗：' + error.message);
            }
        }

        // 重新發送
        async function handleResend() {
            const email = localStorage.getItem('verification_email');

            try {
                const response = await fetch('/api/v1/auth/email/resend', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: email })
                });

                const data = await response.json();

                if (data.success) {
                    localStorage.setItem('verification_code', data.verification_code);
                    startCountdown(180);
                    alert('驗證碼已重新發送！');
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                alert('重新發送失敗：' + error.message);
            }
        }
    </script>
</body>
</html>
```

## 📊 流程圖

```
用戶輸入 Email
    ↓
[POST] /api/v1/auth/email/auth
    {
        "email": "user@example.com",
        "is_verified": false
    }
    ↓
後端發送郵件 + 回傳驗證碼
    {
        "success": true,
        "verification_code": "123456"
    }
    ↓
前端儲存驗證碼 + 開始倒數（3分鐘）
    ↓
用戶輸入驗證碼
    ↓
前端比對驗證碼
    ↓
[POST] /api/v1/auth/login
    {
        "email": "user@example.com",
        "verify": true/false  ← 比對結果
    }
    ↓
後端建立/登入帳號 + 回傳 Token
    {
        "access_token": "...",
        "refresh_token": "...",
        "user": { ... }
    }
```

## ✅ 重點提醒

1. **驗證碼比對在前端進行** - 後端只負責發送
2. **後端總是回傳驗證碼** - 讓前端能進行比對
3. **3 分鐘倒數計時** - 前端實作
4. **verify=true/false** - 告訴後端前端比對的結果
5. **自動建立帳號** - 如果用戶不存在，後端會自動建立

## 🔒 安全性考量

雖然驗證碼在前端比對，但：
- 每個驗證碼只能使用一次
- 驗證碼有效期限（由後端控制）
- 防暴力破解（最多嘗試 5 次）
- Token 認證仍在後端進行

## 📝 API 端點總結

| 端點 | 用途 | 說明 |
|------|------|------|
| `POST /api/v1/auth/email/auth` | 發送驗證碼 | 回傳驗證碼給前端 |
| `POST /api/v1/auth/login` | 登入 | 接收 `verify` 參數 |
| `POST /api/v1/auth/email/resend` | 重發驗證碼 | 重新發送新的驗證碼 |
