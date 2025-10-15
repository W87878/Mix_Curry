# 🌐 前端整合指南

本文件說明如何在前端（React, Vue, Next.js 等）呼叫災民補助申請系統 API。

## 📋 目錄

1. [快速測試](#快速測試)
2. [API 基本資訊](#api-基本資訊)
3. [CORS 設定](#cors-設定)
4. [JavaScript 呼叫範例](#javascript-呼叫範例)
5. [React 整合範例](#react-整合範例)
6. [Vue 整合範例](#vue-整合範例)
7. [Next.js 整合範例](#nextjs-整合範例)
8. [完整流程範例](#完整流程範例)
9. [錯誤處理](#錯誤處理)

---

## 快速測試

### 🚀 使用內建測試頁面（最簡單）

我們提供了一個完整的 HTML 測試頁面，您可以直接在瀏覽器中測試所有 API：

```bash
# 1. 啟動後端服務
python main.py

# 2. 開啟瀏覽器
open http://localhost:8000/test
```

**測試頁面功能**：
- ✅ 建立使用者
- ✅ 建立申請案件
- ✅ 上傳災損照片
- ✅ 查詢案件資料
- ✅ 查看系統統計
- ✅ 即時 API 狀態檢查
- ✅ 美觀的 UI 介面

這個測試頁面完全使用 Vanilla JavaScript，是學習如何呼叫 API 的最佳範例！

**檔案位置**: `static/test_api.html`

---

## API 基本資訊

### API Base URL

```javascript
// 開發環境
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 生產環境
const API_BASE_URL = 'https://your-domain.com/api/v1';
```

### API 文件

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## CORS 設定

後端已經配置 CORS，允許所有來源（開發環境）：

```python
# main.py 中已設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境請改為特定網域
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

⚠️ **生產環境建議**：將 `allow_origins` 改為您的前端網域：
```python
allow_origins=["https://your-frontend-domain.com"]
```

---

## JavaScript 呼叫範例

### 1. 使用 Fetch API

```javascript
// api.js - API 工具模組
const API_BASE_URL = 'http://localhost:8000/api/v1';

// 通用 API 呼叫函數
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || '請求失敗');
    }

    return data;
  } catch (error) {
    console.error('API 錯誤:', error);
    throw error;
  }
}

// ========================================
// 使用者 API
// ========================================

// 建立使用者
export async function createUser(userData) {
  return apiCall('/users/', {
    method: 'POST',
    body: JSON.stringify(userData),
  });
}

// 查詢使用者
export async function getUserById(userId) {
  return apiCall(`/users/${userId}`);
}

// ========================================
// 申請案件 API
// ========================================

// 建立申請案件
export async function createApplication(applicationData) {
  return apiCall('/applications/', {
    method: 'POST',
    body: JSON.stringify(applicationData),
  });
}

// 查詢申請案件
export async function getApplication(applicationId) {
  return apiCall(`/applications/${applicationId}`);
}

// 查詢我的申請案件
export async function getMyApplications(applicantId) {
  return apiCall(`/applications/applicant/${applicantId}`);
}

// ========================================
// 照片上傳 API
// ========================================

// 上傳照片
export async function uploadPhoto(formData) {
  const url = `${API_BASE_URL}/photos/upload`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData, // 不要設定 Content-Type，讓瀏覽器自動設定
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || '上傳失敗');
    }
    
    return data;
  } catch (error) {
    console.error('上傳照片錯誤:', error);
    throw error;
  }
}

// 查詢案件照片
export async function getApplicationPhotos(applicationId) {
  return apiCall(`/photos/application/${applicationId}`);
}

// ========================================
// 審核 API
// ========================================

// 核准申請
export async function approveApplication(applicationId, reviewData) {
  const params = new URLSearchParams(reviewData);
  return apiCall(`/reviews/approve/${applicationId}?${params}`, {
    method: 'POST',
  });
}

// ========================================
// 數位憑證 API
// ========================================

// 建立憑證
export async function createCertificate(params) {
  const queryParams = new URLSearchParams(params);
  return apiCall(`/certificates/?${queryParams}`, {
    method: 'POST',
  });
}

// 查詢憑證
export async function getCertificate(certificateNo) {
  return apiCall(`/certificates/${certificateNo}`);
}

// 掃描 QR Code
export async function scanQRCode(certificateNo) {
  return apiCall(`/certificates/scan/${certificateNo}`, {
    method: 'POST',
  });
}

// ========================================
// 統計 API
// ========================================

// 取得統計資料
export async function getStats() {
  return apiCall('/stats');
}
```

### 2. 使用 Axios

```javascript
// api.js - 使用 Axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器（可加入 token）
api.interceptors.request.use(
  (config) => {
    // 如果有 token，可以在這裡加入
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => Promise.reject(error)
);

// 回應攔截器（統一錯誤處理）
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API 錯誤:', error.response?.data || error.message);
    return Promise.reject(error.response?.data || error);
  }
);

// API 函數
export const userAPI = {
  create: (data) => api.post('/users/', data),
  getById: (id) => api.get(`/users/${id}`),
  getByEmail: (email) => api.get(`/users/email/${email}`),
};

export const applicationAPI = {
  create: (data) => api.post('/applications/', data),
  getById: (id) => api.get(`/applications/${id}`),
  getByApplicant: (applicantId) => api.get(`/applications/applicant/${applicantId}`),
  update: (id, data) => api.patch(`/applications/${id}`, data),
};

export const photoAPI = {
  upload: (formData) => api.post('/photos/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getByApplication: (applicationId) => api.get(`/photos/application/${applicationId}`),
};

export default api;
```

---

## React 整合範例

### 1. 建立 API Service

```typescript
// src/services/api.ts
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || '請求失敗');
    }

    return data;
  }

  // 使用者 API
  async createUser(userData: any) {
    return this.request('/users/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // 申請案件 API
  async createApplication(applicationData: any) {
    return this.request('/applications/', {
      method: 'POST',
      body: JSON.stringify(applicationData),
    });
  }

  async getMyApplications(applicantId: string) {
    return this.request(`/applications/applicant/${applicantId}`);
  }

  // 照片上傳 API
  async uploadPhoto(formData: FormData) {
    const url = `${API_BASE_URL}/photos/upload`;
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  }
}

export const apiService = new ApiService();
```

### 2. React Hook 範例

```typescript
// src/hooks/useApplication.ts
import { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export function useApplication(applicationId: string) {
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchApplication() {
      try {
        const response = await apiService.getMyApplications(applicationId);
        setApplication(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    if (applicationId) {
      fetchApplication();
    }
  }, [applicationId]);

  return { application, loading, error };
}
```

### 3. React 組件範例

```tsx
// src/components/ApplicationForm.tsx
import React, { useState } from 'react';
import { apiService } from '../services/api';

export function ApplicationForm({ applicantId }) {
  const [formData, setFormData] = useState({
    applicant_name: '',
    id_number: '',
    phone: '',
    address: '',
    disaster_date: '',
    disaster_type: 'typhoon',
    damage_description: '',
    damage_location: '',
    subsidy_type: 'housing',
    requested_amount: 0,
  });
  
  const [loading, setLoading] = useState(false);
  const [photos, setPhotos] = useState([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      // 1. 建立申請案件
      const response = await apiService.createApplication({
        ...formData,
        applicant_id: applicantId,
      });

      const applicationId = response.data.id;
      console.log('申請案件建立成功:', response.data.case_no);

      // 2. 上傳照片
      for (const photo of photos) {
        const formData = new FormData();
        formData.append('application_id', applicationId);
        formData.append('photo_type', photo.type);
        formData.append('description', photo.description);
        formData.append('file', photo.file);
        formData.append('uploaded_by', applicantId);

        await apiService.uploadPhoto(formData);
      }

      alert('申請提交成功！案件編號：' + response.data.case_no);
      // 導向到查看頁面
      window.location.href = `/applications/${applicationId}`;
      
    } catch (error) {
      console.error('提交失敗:', error);
      alert('提交失敗: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePhotoChange = (e) => {
    const files = Array.from(e.target.files);
    setPhotos(files.map(file => ({
      file,
      type: 'before_damage',
      description: '',
    })));
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>災民補助申請表單</h2>
      
      {/* 基本資料 */}
      <div>
        <label>姓名：</label>
        <input
          type="text"
          value={formData.applicant_name}
          onChange={(e) => setFormData({...formData, applicant_name: e.target.value})}
          required
        />
      </div>

      <div>
        <label>身分證字號：</label>
        <input
          type="text"
          value={formData.id_number}
          onChange={(e) => setFormData({...formData, id_number: e.target.value})}
          required
        />
      </div>

      {/* 災害資料 */}
      <div>
        <label>災害類型：</label>
        <select
          value={formData.disaster_type}
          onChange={(e) => setFormData({...formData, disaster_type: e.target.value})}
        >
          <option value="typhoon">颱風</option>
          <option value="flood">水災</option>
          <option value="earthquake">地震</option>
          <option value="fire">火災</option>
        </select>
      </div>

      <div>
        <label>災損描述：</label>
        <textarea
          value={formData.damage_description}
          onChange={(e) => setFormData({...formData, damage_description: e.target.value})}
          rows={4}
          required
        />
      </div>

      {/* 上傳照片 */}
      <div>
        <label>災損照片：</label>
        <input
          type="file"
          multiple
          accept="image/*"
          onChange={handlePhotoChange}
        />
        <small>請上傳災前災後對比照片</small>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? '提交中...' : '提交申請'}
      </button>
    </form>
  );
}
```

---

## Vue 整合範例

### 1. API Service (Composition API)

```typescript
// src/composables/useApi.ts
import { ref } from 'vue';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export function useApi() {
  const loading = ref(false);
  const error = ref(null);

  async function request(endpoint: string, options: RequestInit = {}) {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || '請求失敗');
      }

      return data;
    } catch (err) {
      error.value = err.message;
      throw err;
    } finally {
      loading.value = false;
    }
  }

  return {
    loading,
    error,
    createApplication: (data) => request('/applications/', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
    getMyApplications: (applicantId) => request(`/applications/applicant/${applicantId}`),
    uploadPhoto: async (formData) => {
      loading.value = true;
      try {
        const response = await fetch(`${API_BASE_URL}/photos/upload`, {
          method: 'POST',
          body: formData,
        });
        return response.json();
      } finally {
        loading.value = false;
      }
    },
  };
}
```

### 2. Vue 組件範例

```vue
<!-- src/components/ApplicationForm.vue -->
<template>
  <form @submit.prevent="handleSubmit">
    <h2>災民補助申請表單</h2>
    
    <div>
      <label>姓名：</label>
      <input v-model="formData.applicant_name" required />
    </div>

    <div>
      <label>災害類型：</label>
      <select v-model="formData.disaster_type">
        <option value="typhoon">颱風</option>
        <option value="flood">水災</option>
        <option value="earthquake">地震</option>
      </select>
    </div>

    <div>
      <label>災損照片：</label>
      <input type="file" multiple @change="handlePhotoChange" accept="image/*" />
    </div>

    <button type="submit" :disabled="loading">
      {{ loading ? '提交中...' : '提交申請' }}
    </button>

    <div v-if="error" class="error">{{ error }}</div>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useApi } from '../composables/useApi';

const props = defineProps<{ applicantId: string }>();
const { loading, error, createApplication, uploadPhoto } = useApi();

const formData = ref({
  applicant_name: '',
  id_number: '',
  phone: '',
  address: '',
  disaster_date: '',
  disaster_type: 'typhoon',
  damage_description: '',
  damage_location: '',
  subsidy_type: 'housing',
  requested_amount: 0,
});

const photos = ref([]);

const handlePhotoChange = (event) => {
  photos.value = Array.from(event.target.files);
};

const handleSubmit = async () => {
  try {
    // 建立申請
    const response = await createApplication({
      ...formData.value,
      applicant_id: props.applicantId,
    });

    const applicationId = response.data.id;

    // 上傳照片
    for (const photo of photos.value) {
      const formData = new FormData();
      formData.append('application_id', applicationId);
      formData.append('photo_type', 'before_damage');
      formData.append('file', photo);
      formData.append('uploaded_by', props.applicantId);

      await uploadPhoto(formData);
    }

    alert('申請提交成功！');
  } catch (err) {
    console.error('提交失敗:', err);
  }
};
</script>
```

---

## Next.js 整合範例

### 1. API Routes (Server-side)

```typescript
// app/api/applications/route.ts
import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`${API_BASE_URL}/applications/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error.message },
      { status: 500 }
    );
  }
}
```

### 2. Client Component

```typescript
// app/components/ApplicationForm.tsx
'use client';

import { useState } from 'react';

export default function ApplicationForm({ applicantId }: { applicantId: string }) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/applications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          applicant_id: applicantId,
          // ... 其他資料
        }),
      });

      const data = await response.json();
      console.log('申請成功:', data);
    } catch (error) {
      console.error('提交失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* 表單內容 */}
    </form>
  );
}
```

---

## 完整流程範例

### 災民申請完整流程

```javascript
// 完整的申請流程
async function submitDisasterApplication(userData, applicationData, photos) {
  try {
    // 步驟 1: 建立使用者（如果還沒有）
    const userResponse = await createUser(userData);
    const userId = userResponse.data.id;
    console.log('✅ 使用者建立成功:', userId);

    // 步驟 2: 建立申請案件
    const appResponse = await createApplication({
      ...applicationData,
      applicant_id: userId,
    });
    const applicationId = appResponse.data.id;
    const caseNo = appResponse.data.case_no;
    console.log('✅ 申請案件建立成功:', caseNo);

    // 步驟 3: 上傳所有照片
    const photoPromises = photos.map(async (photo) => {
      const formData = new FormData();
      formData.append('application_id', applicationId);
      formData.append('photo_type', photo.type);
      formData.append('description', photo.description);
      formData.append('file', photo.file);
      formData.append('uploaded_by', userId);

      return uploadPhoto(formData);
    });

    await Promise.all(photoPromises);
    console.log('✅ 照片上傳成功');

    // 步驟 4: 查詢完整的申請資料
    const fullApplication = await getApplication(applicationId);
    console.log('✅ 申請完成:', fullApplication);

    return {
      success: true,
      userId,
      applicationId,
      caseNo,
      data: fullApplication,
    };

  } catch (error) {
    console.error('❌ 申請流程失敗:', error);
    throw error;
  }
}

// 使用範例
const result = await submitDisasterApplication(
  // 使用者資料
  {
    email: 'victim@example.com',
    full_name: '王小明',
    id_number: 'A123456789',
    phone: '0912345678',
    role: 'applicant',
  },
  // 申請資料
  {
    applicant_name: '王小明',
    id_number: 'A123456789',
    phone: '0912345678',
    address: '台南市中西區民權路100號',
    disaster_date: '2025-10-10',
    disaster_type: 'typhoon',
    damage_description: '颱風造成一樓淹水',
    damage_location: '台南市中西區民權路100號1樓',
    subsidy_type: 'housing',
    requested_amount: 50000,
  },
  // 照片
  [
    { type: 'before_damage', description: '災前照片', file: file1 },
    { type: 'after_damage', description: '災後照片', file: file2 },
  ]
);
```

---

## 錯誤處理

### 統一錯誤處理

```javascript
// errorHandler.js
export function handleApiError(error) {
  if (error.response) {
    // 伺服器回應錯誤
    const status = error.response.status;
    const message = error.response.data?.detail || '請求失敗';

    switch (status) {
      case 400:
        return '請求參數錯誤: ' + message;
      case 404:
        return '資源不存在: ' + message;
      case 500:
        return '伺服器錯誤: ' + message;
      default:
        return '發生錯誤: ' + message;
    }
  } else if (error.request) {
    // 請求已發送但沒有收到回應
    return '無法連接到伺服器，請檢查網路連線';
  } else {
    // 其他錯誤
    return '發生未知錯誤: ' + error.message;
  }
}

// 使用範例
try {
  const response = await createApplication(data);
} catch (error) {
  const errorMessage = handleApiError(error);
  alert(errorMessage);
}
```

---

## 環境變數設定

### React (.env)

```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
```

### Vue (.env)

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

### Next.js (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## 📚 相關資源

- [API 文件 (Swagger)](http://localhost:8000/docs)
- [HTTP 測試檔案](./https/test.http)
- [完整 README](./README.md)

---

**最後更新**: 2025-10-14  
**版本**: 1.0.0

