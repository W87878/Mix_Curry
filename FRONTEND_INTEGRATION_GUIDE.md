# 🎨 前端整合完整指南

## 目錄

- [系統架構](#系統架構)
- [身份驗證流程](#身份驗證流程)
- [React 完整範例](#react-完整範例)
- [Vue 完整範例](#vue-完整範例)
- [API 呼叫範例](#api-呼叫範例)
- [檔案上傳處理](#檔案上傳處理)
- [錯誤處理](#錯誤處理)
- [狀態管理](#狀態管理)

---

## 系統架構

```
前端應用
├── /applicant          # 災民前台
│   ├── /login          # 登入頁
│   ├── /register       # 註冊頁
│   ├── /dashboard      # 個人儀表板
│   ├── /apply          # 申請表單
│   ├── /applications   # 我的申請
│   └── /certificate    # 我的憑證（QR Code）
│
└── /admin              # 里長後台
    ├── /login          # 後台登入
    ├── /dashboard      # 管理儀表板
    ├── /applications   # 案件管理
    ├── /review/[id]    # 審核介面
    └── /inspection     # 現場勘查管理
```

---

## 身份驗證流程

### 1. JWT Token 管理

```javascript
// utils/auth.js
export const authService = {
  // 儲存 Token
  saveToken(accessToken, refreshToken) {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  },

  // 取得 Token
  getAccessToken() {
    return localStorage.getItem('access_token');
  },

  getRefreshToken() {
    return localStorage.getItem('refresh_token');
  },

  // 清除 Token
  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  // 儲存使用者資訊
  saveUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
  },

  // 取得使用者資訊
  getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  // 檢查是否已登入
  isAuthenticated() {
    return !!this.getAccessToken();
  },

  // 檢查角色
  hasRole(role) {
    const user = this.getUser();
    return user && user.role === role;
  }
};
```

### 2. Axios 攔截器設定

```javascript
// utils/axios.js
import axios from 'axios';
import { authService } from './auth';

const API_BASE_URL = 'http://localhost:8000';

// 建立 axios 實例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器：自動加入 Token
api.interceptors.request.use(
  (config) => {
    const token = authService.getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 回應攔截器：處理 Token 過期
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Token 過期，嘗試刷新
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = authService.getRefreshToken();
        const response = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const { access_token } = response.data;
        authService.saveToken(access_token, refreshToken);

        // 重試原請求
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // 刷新失敗，導向登入頁
        authService.clearTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

---

## React 完整範例

### 1. 登入頁面

```jsx
// pages/Login.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/axios';
import { authService } from '../utils/auth';

function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    loginType: 'password', // 或 'digital_id'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await api.post('/api/v1/auth/login', {
        email: formData.email,
        password: formData.password,
        login_type: formData.loginType,
      });

      const { access_token, refresh_token, user } = response.data;

      // 儲存 Token 和使用者資訊
      authService.saveToken(access_token, refresh_token);
      authService.saveUser(user);

      // 根據角色導向不同頁面
      if (user.role === 'applicant') {
        navigate('/applicant/dashboard');
      } else if (user.role === 'reviewer') {
        navigate('/admin/dashboard');
      } else {
        navigate('/admin/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || '登入失敗');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h2 className="text-2xl font-bold text-center mb-6">災民補助申請系統</h2>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              電子郵件
            </label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              密碼
            </label>
            <input
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? '登入中...' : '登入'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <a href="/register" className="text-blue-500 hover:underline">
            還沒有帳號？立即註冊
          </a>
        </div>
      </div>
    </div>
  );
}

export default Login;
```

### 2. 申請表單頁面

```jsx
// pages/ApplyForm.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../utils/axios';
import { authService } from '../utils/auth';

function ApplyForm() {
  const navigate = useNavigate();
  const user = authService.getUser();
  
  const [formData, setFormData] = useState({
    applicant_name: user?.full_name || '',
    id_number: user?.id_number || '',
    phone: user?.phone || '',
    address: '',
    bank_code: '',
    bank_name: '',
    bank_account: '',
    account_holder_name: user?.full_name || '',
    disaster_date: '',
    disaster_type: 'flood',
    damage_description: '',
    damage_location: '',
    estimated_loss: '',
    subsidy_type: 'housing',
    requested_amount: '',
  });
  
  const [photos, setPhotos] = useState({
    before_damage: [],
    after_damage: [],
  });
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePhotoUpload = (e, photoType) => {
    const files = Array.from(e.target.files);
    setPhotos(prev => ({
      ...prev,
      [photoType]: [...prev[photoType], ...files]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // 1. 建立申請案件
      const applicationResponse = await api.post('/api/v1/applications/', {
        ...formData,
        applicant_id: user.id,
        estimated_loss: parseFloat(formData.estimated_loss),
        requested_amount: parseFloat(formData.requested_amount),
      });

      const application = applicationResponse.data;
      console.log('申請案件建立成功:', application);

      // 2. 上傳照片
      const uploadPromises = [];
      
      for (const photoType of ['before_damage', 'after_damage']) {
        for (const file of photos[photoType]) {
          const photoFormData = new FormData();
          photoFormData.append('file', file);
          photoFormData.append('application_id', application.id);
          photoFormData.append('photo_type', photoType);
          photoFormData.append('description', `${photoType === 'before_damage' ? '災前' : '災後'}照片`);

          uploadPromises.push(
            api.post('/api/v1/photos/upload', photoFormData, {
              headers: { 'Content-Type': 'multipart/form-data' },
            })
          );
        }
      }

      await Promise.all(uploadPromises);
      console.log('照片上傳完成');

      // 3. 導向申請完成頁面
      alert(`申請提交成功！案件編號：${application.case_no}`);
      navigate(`/applicant/applications/${application.id}`);
      
    } catch (err) {
      console.error('申請失敗:', err);
      setError(err.response?.data?.detail || '申請失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">災民補助申請表單</h1>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 基本資料 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">基本資料</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 font-bold mb-2">姓名 *</label>
              <input
                type="text"
                value={formData.applicant_name}
                onChange={(e) => setFormData({ ...formData, applicant_name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">身分證字號 *</label>
              <input
                type="text"
                value={formData.id_number}
                onChange={(e) => setFormData({ ...formData, id_number: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">手機號碼 *</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">聯絡地址 *</label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>
          </div>
        </div>

        {/* 銀行資料 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">銀行帳戶資料</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 font-bold mb-2">銀行代碼 *</label>
              <input
                type="text"
                value={formData.bank_code}
                onChange={(e) => setFormData({ ...formData, bank_code: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="例如：004"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">銀行名稱 *</label>
              <input
                type="text"
                value={formData.bank_name}
                onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                placeholder="例如：台灣銀行"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">銀行帳號 *</label>
              <input
                type="text"
                value={formData.bank_account}
                onChange={(e) => setFormData({ ...formData, bank_account: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">戶名 *</label>
              <input
                type="text"
                value={formData.account_holder_name}
                onChange={(e) => setFormData({ ...formData, account_holder_name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>
          </div>
        </div>

        {/* 災損資料 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">災損資料</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-gray-700 font-bold mb-2">災害日期 *</label>
              <input
                type="date"
                value={formData.disaster_date}
                onChange={(e) => setFormData({ ...formData, disaster_date: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">災害類型 *</label>
              <select
                value={formData.disaster_type}
                onChange={(e) => setFormData({ ...formData, disaster_type: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              >
                <option value="flood">水災</option>
                <option value="typhoon">颱風</option>
                <option value="earthquake">地震</option>
                <option value="other">其他</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-gray-700 font-bold mb-2">災損地點 *</label>
              <input
                type="text"
                value={formData.damage_location}
                onChange={(e) => setFormData({ ...formData, damage_location: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-gray-700 font-bold mb-2">災損描述 *</label>
              <textarea
                value={formData.damage_description}
                onChange={(e) => setFormData({ ...formData, damage_description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                rows="4"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">預估損失金額 *</label>
              <input
                type="number"
                value={formData.estimated_loss}
                onChange={(e) => setFormData({ ...formData, estimated_loss: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">申請金額 *</label>
              <input
                type="number"
                value={formData.requested_amount}
                onChange={(e) => setFormData({ ...formData, requested_amount: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
            </div>
          </div>
        </div>

        {/* 上傳照片 */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4">災損照片</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-gray-700 font-bold mb-2">災前照片</label>
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => handlePhotoUpload(e, 'before_damage')}
                className="w-full px-3 py-2 border rounded-lg"
              />
              <p className="text-sm text-gray-600 mt-1">
                已選擇 {photos.before_damage.length} 張照片
              </p>
            </div>

            <div>
              <label className="block text-gray-700 font-bold mb-2">災後照片 *</label>
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => handlePhotoUpload(e, 'after_damage')}
                className="w-full px-3 py-2 border rounded-lg"
                required
              />
              <p className="text-sm text-gray-600 mt-1">
                已選擇 {photos.after_damage.length} 張照片
              </p>
            </div>
          </div>
        </div>

        {/* 提交按鈕 */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={() => navigate('/applicant/dashboard')}
            className="px-6 py-2 border rounded-lg hover:bg-gray-100"
          >
            取消
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
          >
            {loading ? '提交中...' : '提交申請'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default ApplyForm;
```

### 3. 里長審核頁面

```jsx
// pages/ReviewApplication.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../utils/axios';

function ReviewApplication() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [application, setApplication] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const [reviewData, setReviewData] = useState({
    action: '',
    comments: '',
    approved_amount: '',
    supplement_request: '',
    rejection_reason: '',
  });

  useEffect(() => {
    fetchApplication();
  }, [id]);

  const fetchApplication = async () => {
    try {
      // 取得申請案件
      const appResponse = await api.get(`/api/v1/applications/${id}`);
      setApplication(appResponse.data);

      // 取得照片
      const photosResponse = await api.get(`/api/v1/photos/application/${id}`);
      setPhotos(photosResponse.data);

      setLoading(false);
    } catch (error) {
      console.error('取得申請案件失敗:', error);
      alert('取得申請案件失敗');
      navigate('/admin/dashboard');
    }
  };

  const handleApprove = async () => {
    if (!reviewData.approved_amount) {
      alert('請輸入核准金額');
      return;
    }

    setActionLoading(true);
    try {
      await api.post(`/api/v1/reviews/approve/${id}`, {
        approved_amount: parseFloat(reviewData.approved_amount),
        comments: reviewData.comments,
      });

      alert('核准成功！');
      navigate('/admin/dashboard');
    } catch (error) {
      alert(error.response?.data?.detail || '核准失敗');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!reviewData.rejection_reason) {
      alert('請輸入駁回原因');
      return;
    }

    setActionLoading(true);
    try {
      await api.post(`/api/v1/reviews/reject/${id}`, {
        rejection_reason: reviewData.rejection_reason,
        comments: reviewData.comments,
      });

      alert('駁回成功');
      navigate('/admin/dashboard');
    } catch (error) {
      alert(error.response?.data?.detail || '駁回失敗');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">載入中...</div>;
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">審核申請案件</h1>

      {/* 案件資訊 */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-xl font-bold mb-4">案件資訊</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="font-bold">案件編號：</span>
            {application.case_no}
          </div>
          <div>
            <span className="font-bold">申請人：</span>
            {application.applicant_name}
          </div>
          <div>
            <span className="font-bold">身分證字號：</span>
            {application.id_number}
          </div>
          <div>
            <span className="font-bold">聯絡電話：</span>
            {application.phone}
          </div>
          <div className="col-span-2">
            <span className="font-bold">聯絡地址：</span>
            {application.address}
          </div>
          <div>
            <span className="font-bold">災害日期：</span>
            {application.disaster_date}
          </div>
          <div>
            <span className="font-bold">災害類型：</span>
            {application.disaster_type}
          </div>
          <div className="col-span-2">
            <span className="font-bold">災損描述：</span>
            {application.damage_description}
          </div>
          <div>
            <span className="font-bold">申請金額：</span>
            ${application.requested_amount?.toLocaleString()}
          </div>
        </div>
      </div>

      {/* 災損照片 */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-xl font-bold mb-4">災損照片</h2>
        <div className="grid grid-cols-3 gap-4">
          {photos.map((photo) => (
            <div key={photo.id}>
              <img
                src={photo.file_url}
                alt={photo.description}
                className="w-full h-48 object-cover rounded-lg"
              />
              <p className="text-sm text-gray-600 mt-2">{photo.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 審核動作 */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold mb-4">審核動作</h2>

        <div className="space-y-4">
          <div>
            <label className="block font-bold mb-2">審核意見</label>
            <textarea
              value={reviewData.comments}
              onChange={(e) => setReviewData({ ...reviewData, comments: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              rows="3"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-bold mb-2">核准金額</label>
              <input
                type="number"
                value={reviewData.approved_amount}
                onChange={(e) => setReviewData({ ...reviewData, approved_amount: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
          </div>

          <div>
            <label className="block font-bold mb-2">駁回原因</label>
            <textarea
              value={reviewData.rejection_reason}
              onChange={(e) => setReviewData({ ...reviewData, rejection_reason: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
              rows="2"
            />
          </div>

          <div className="flex justify-end space-x-4">
            <button
              onClick={handleReject}
              disabled={actionLoading}
              className="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:bg-gray-400"
            >
              駁回申請
            </button>
            <button
              onClick={handleApprove}
              disabled={actionLoading}
              className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-400"
            >
              核准申請
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReviewApplication;
```

---

## Vue 完整範例

### Vue 3 + Composition API

```vue
<!-- pages/Login.vue -->
<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
      <h2 class="text-2xl font-bold text-center mb-6">災民補助申請系統</h2>

      <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
        {{ error }}
      </div>

      <form @submit.prevent="handleLogin">
        <div class="mb-4">
          <label class="block text-gray-700 text-sm font-bold mb-2">電子郵件</label>
          <input
            v-model="formData.email"
            type="email"
            class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div class="mb-6">
          <label class="block text-gray-700 text-sm font-bold mb-2">密碼</label>
          <input
            v-model="formData.password"
            type="password"
            class="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 disabled:bg-gray-400"
        >
          {{ loading ? '登入中...' : '登入' }}
        </button>
      </form>

      <div class="mt-4 text-center">
        <router-link to="/register" class="text-blue-500 hover:underline">
          還沒有帳號？立即註冊
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../utils/axios';
import { authService } from '../utils/auth';

const router = useRouter();

const formData = ref({
  email: '',
  password: '',
  loginType: 'password',
});

const loading = ref(false);
const error = ref('');

const handleLogin = async () => {
  loading.value = true;
  error.value = '';

  try {
    const response = await api.post('/api/v1/auth/login', {
      email: formData.value.email,
      password: formData.value.password,
      login_type: formData.value.loginType,
    });

    const { access_token, refresh_token, user } = response.data;

    authService.saveToken(access_token, refresh_token);
    authService.saveUser(user);

    if (user.role === 'applicant') {
      router.push('/applicant/dashboard');
    } else if (user.role === 'reviewer') {
      router.push('/admin/dashboard');
    } else {
      router.push('/admin/dashboard');
    }
  } catch (err) {
    error.value = err.response?.data?.detail || '登入失敗';
  } finally {
    loading.value = false;
  }
};
</script>
```

---

## API 呼叫範例彙整

```javascript
// api/services.js
import api from '../utils/axios';

export const authAPI = {
  login: (email, password, loginType = 'password') =>
    api.post('/api/v1/auth/login', { email, password, login_type: loginType }),
  
  register: (userData) =>
    api.post('/api/v1/auth/register', userData),
  
  refreshToken: (refreshToken) =>
    api.post('/api/v1/auth/refresh', { refresh_token: refreshToken }),
  
  getMe: () =>
    api.get('/api/v1/auth/me'),
  
  logout: () =>
    api.post('/api/v1/auth/logout'),
};

export const applicationAPI = {
  create: (data) =>
    api.post('/api/v1/applications/', data),
  
  getById: (id) =>
    api.get(`/api/v1/applications/${id}`),
  
  getByApplicant: (applicantId) =>
    api.get(`/api/v1/applications/applicant/${applicantId}`),
  
  update: (id, data) =>
    api.patch(`/api/v1/applications/${id}`, data),
};

export const photoAPI = {
  upload: (formData) =>
    api.post('/api/v1/photos/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  getByApplication: (applicationId) =>
    api.get(`/api/v1/photos/application/${applicationId}`),
  
  delete: (photoId) =>
    api.delete(`/api/v1/photos/${photoId}`),
};

export const reviewAPI = {
  approve: (applicationId, data) =>
    api.post(`/api/v1/reviews/approve/${applicationId}`, data),
  
  reject: (applicationId, data) =>
    api.post(`/api/v1/reviews/reject/${applicationId}`, data),
  
  getHistory: (applicationId) =>
    api.get(`/api/v1/reviews/application/${applicationId}`),
};

export const notificationAPI = {
  getAll: (unreadOnly = false, limit = 50) =>
    api.get('/api/v1/notifications/', { params: { unread_only: unreadOnly, limit } }),
  
  getUnreadCount: () =>
    api.get('/api/v1/notifications/unread-count'),
  
  markAsRead: (notificationId) =>
    api.patch(`/api/v1/notifications/${notificationId}/read`),
  
  markAllAsRead: () =>
    api.post('/api/v1/notifications/mark-all-read'),
};

export const districtAPI = {
  getAll: (params = {}) =>
    api.get('/api/v1/districts/', { params }),
  
  getById: (id) =>
    api.get(`/api/v1/districts/${id}`),
  
  getApplications: (districtId, statusFilter, limit = 50) =>
    api.get(`/api/v1/districts/${districtId}/applications`, {
      params: { status_filter: statusFilter, limit },
    }),
  
  getStats: (districtId) =>
    api.get(`/api/v1/districts/${districtId}/stats`),
};
```

---

## 完整的 React Router 設定

```jsx
// App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { authService } from './utils/auth';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import ApplicantDashboard from './pages/ApplicantDashboard';
import ApplyForm from './pages/ApplyForm';
import AdminDashboard from './pages/AdminDashboard';
import ReviewApplication from './pages/ReviewApplication';

// Protected Route Component
function ProtectedRoute({ children, allowedRoles }) {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" />;
  }

  const user = authService.getUser();
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" />;
  }

  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* 災民路由 */}
        <Route
          path="/applicant/dashboard"
          element={
            <ProtectedRoute allowedRoles={['applicant']}>
              <ApplicantDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/applicant/apply"
          element={
            <ProtectedRoute allowedRoles={['applicant']}>
              <ApplyForm />
            </ProtectedRoute>
          }
        />

        {/* 里長路由 */}
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={['reviewer', 'admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/review/:id"
          element={
            <ProtectedRoute allowedRoles={['reviewer', 'admin']}>
              <ReviewApplication />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

---

## 錯誤處理最佳實踐

```javascript
// utils/errorHandler.js
export const handleAPIError = (error, customMessage = '') => {
  if (error.response) {
    // 伺服器回應錯誤
    const status = error.response.status;
    const detail = error.response.data?.detail || '發生錯誤';

    switch (status) {
      case 400:
        return customMessage || `請求錯誤：${detail}`;
      case 401:
        return '您尚未登入或登入已過期';
      case 403:
        return '您沒有權限執行此操作';
      case 404:
        return '找不到資源';
      case 500:
        return '伺服器發生錯誤，請稍後再試';
      default:
        return detail;
    }
  } else if (error.request) {
    // 請求已發送但沒有收到回應
    return '網路連線失敗，請檢查您的網路連線';
  } else {
    // 其他錯誤
    return error.message || '發生未知錯誤';
  }
};
```

---

## 通知系統整合

```jsx
// components/NotificationBell.jsx
import React, { useState, useEffect } from 'react';
import { notificationAPI } from '../api/services';

function NotificationBell() {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    fetchUnreadCount();
    // 每 30 秒更新一次
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchUnreadCount = async () => {
    try {
      const response = await notificationAPI.getUnreadCount();
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('取得未讀數量失敗:', error);
    }
  };

  const fetchNotifications = async () => {
    try {
      const response = await notificationAPI.getAll(false, 10);
      setNotifications(response.data);
    } catch (error) {
      console.error('取得通知失敗:', error);
    }
  };

  const handleBellClick = () => {
    if (!showDropdown) {
      fetchNotifications();
    }
    setShowDropdown(!showDropdown);
  };

  const handleMarkAsRead = async (notificationId) => {
    try {
      await notificationAPI.markAsRead(notificationId);
      fetchUnreadCount();
      fetchNotifications();
    } catch (error) {
      console.error('標記通知失敗:', error);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={handleBellClick}
        className="relative p-2 rounded-full hover:bg-gray-200"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {unreadCount}
          </span>
        )}
      </button>

      {showDropdown && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg z-50">
          <div className="p-4 border-b">
            <h3 className="text-lg font-bold">通知</h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">沒有通知</div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b hover:bg-gray-50 cursor-pointer ${
                    !notification.is_read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => handleMarkAsRead(notification.id)}
                >
                  <div className="font-bold">{notification.title}</div>
                  <div className="text-sm text-gray-600">{notification.content}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {new Date(notification.created_at).toLocaleString()}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default NotificationBell;
```

---

**🎉 這樣就完成了完整的前端整合指南！**

包含：
- ✅ React 完整範例（登入、申請、審核）
- ✅ Vue 3 範例
- ✅ API 呼叫封裝
- ✅ 身份驗證流程
- ✅ 路由保護
- ✅ 錯誤處理
- ✅ 通知系統整合

