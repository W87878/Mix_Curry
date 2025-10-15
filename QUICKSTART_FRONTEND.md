# 🚀 前端快速上手指南

5 分鐘學會如何在前端呼叫災民補助申請系統 API

## 🎯 三種測試方式

### 1. 網頁測試介面（最簡單）⭐

```bash
# 啟動後端
python main.py

# 開啟瀏覽器
open http://localhost:8000/test
```

**優點**：
- ✅ 零程式碼，直接在瀏覽器測試
- ✅ 美觀的 UI 介面
- ✅ 自動處理 ID 傳遞
- ✅ 即時查看回應結果

---

### 2. HTTP 測試檔案（VS Code）

```bash
# 安裝 VS Code REST Client 擴充套件
# 然後開啟
code https/test.http
```

**優點**：
- ✅ 完整的 API 測試集合
- ✅ 支援變數替換
- ✅ 可作為 API 文件

---

### 3. JavaScript 程式碼

最基本的 API 呼叫範例：

```javascript
// API Base URL
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 1. 建立使用者
async function createUser() {
  const response = await fetch(`${API_BASE_URL}/users/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: 'test@example.com',
      full_name: '王小明',
      id_number: 'A123456789',
      phone: '0912345678',
      role: 'applicant'
    })
  });
  
  const data = await response.json();
  console.log('使用者 ID:', data.data.id);
  return data.data.id;
}

// 2. 建立申請
async function createApplication(userId) {
  const response = await fetch(`${API_BASE_URL}/applications/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      applicant_id: userId,
      applicant_name: '王小明',
      id_number: 'A123456789',
      phone: '0912345678',
      address: '台南市中西區民權路100號',
      disaster_date: '2025-10-10',
      disaster_type: 'typhoon',
      damage_description: '颱風造成一樓淹水',
      damage_location: '台南市中西區民權路100號1樓',
      subsidy_type: 'housing',
      requested_amount: 50000
    })
  });
  
  const data = await response.json();
  console.log('案件編號:', data.data.case_no);
  return data.data.id;
}

// 3. 上傳照片
async function uploadPhoto(applicationId, userId, file) {
  const formData = new FormData();
  formData.append('application_id', applicationId);
  formData.append('photo_type', 'before_damage');
  formData.append('description', '災前照片');
  formData.append('uploaded_by', userId);
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/photos/upload`, {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  console.log('照片 URL:', data.data.photo_url);
  return data.data.id;
}

// 完整流程
async function submitApplication(photoFile) {
  try {
    // 建立使用者
    const userId = await createUser();
    
    // 建立申請
    const applicationId = await createApplication(userId);
    
    // 上傳照片
    await uploadPhoto(applicationId, userId, photoFile);
    
    console.log('✅ 申請完成！');
  } catch (error) {
    console.error('❌ 錯誤:', error);
  }
}
```

---

## 📦 前端框架整合

### React

```jsx
import { useState } from 'react';

function ApplicationForm() {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/applications/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          // ... 表單資料
        })
      });

      const data = await response.json();
      console.log('成功:', data);
    } catch (error) {
      console.error('錯誤:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* 表單內容 */}
      <button type="submit" disabled={loading}>
        {loading ? '提交中...' : '提交申請'}
      </button>
    </form>
  );
}
```

### Vue 3

```vue
<script setup>
import { ref } from 'vue';

const loading = ref(false);

async function handleSubmit() {
  loading.value = true;
  
  try {
    const response = await fetch('http://localhost:8000/api/v1/applications/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        // ... 表單資料
      })
    });
    
    const data = await response.json();
    console.log('成功:', data);
  } catch (error) {
    console.error('錯誤:', error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <!-- 表單內容 -->
    <button type="submit" :disabled="loading">
      {{ loading ? '提交中...' : '提交申請' }}
    </button>
  </form>
</template>
```

---

## 🔑 常用 API 端點

| 功能 | 方法 | 路徑 | 說明 |
|------|------|------|------|
| 建立使用者 | POST | `/api/v1/users/` | 註冊災民/審核員 |
| 建立申請 | POST | `/api/v1/applications/` | 提交補助申請 |
| 查詢申請 | GET | `/api/v1/applications/{id}` | 查看申請詳情 |
| 上傳照片 | POST | `/api/v1/photos/upload` | 上傳災損照片 |
| 核准申請 | POST | `/api/v1/reviews/approve/{id}` | 審核員核准 |
| 建立憑證 | POST | `/api/v1/certificates/` | 生成 QR Code |
| 掃描憑證 | POST | `/api/v1/certificates/scan/{no}` | 驗證憑證 |
| 系統統計 | GET | `/api/v1/stats` | 取得統計資料 |

---

## 📝 注意事項

### CORS 設定

後端已經啟用 CORS，允許所有來源（開發環境）：

```python
# main.py 已設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發環境
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

⚠️ **生產環境**請改為：
```python
allow_origins=["https://your-domain.com"]
```

### 上傳檔案

上傳照片時**不要**設定 `Content-Type`，讓瀏覽器自動處理：

```javascript
// ✅ 正確
const response = await fetch(url, {
  method: 'POST',
  body: formData  // 不設定 headers
});

// ❌ 錯誤
const response = await fetch(url, {
  method: 'POST',
  headers: { 'Content-Type': 'multipart/form-data' },  // 不要手動設定！
  body: formData
});
```

### 錯誤處理

API 錯誤格式：

```json
{
  "success": false,
  "message": "錯誤訊息",
  "detail": "詳細錯誤資訊"
}
```

建議處理方式：

```javascript
try {
  const response = await fetch(url, options);
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.detail || data.message || '請求失敗');
  }
  
  return data;
} catch (error) {
  console.error('API 錯誤:', error.message);
  alert('發生錯誤: ' + error.message);
}
```

---

## 🎓 完整範例

想看完整的範例程式碼？

- **HTML 範例**: `static/test_api.html`
- **詳細文件**: [FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md)
- **HTTP 測試**: `https/test.http`

---

## 📚 相關資源

- [前端整合完整指南](./FRONTEND_GUIDE.md)
- [API 文件 (Swagger)](http://localhost:8000/docs)
- [網頁測試介面](http://localhost:8000/test)
- [主要 README](./README.md)

---

**祝您開發順利！** 🚀

有問題？查看 [FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md) 獲取更詳細的說明。

