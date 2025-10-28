# 里長後台地圖功能修復完整記錄

## 📋 問題描述

### 錯誤訊息
```
Request URL: https://xxx.ngrok-free.app/api/v1/applications/district/undefined
Status Code: 404 Not Found
```

### 根本原因
1. ❌ **Login API 未返回 `district_id`** - 里長登入後 `currentUser.district_id` 為 `undefined`
2. ❌ **缺少 API 端點** - `/api/v1/applications/district/{district_id}` 不存在
3. ❌ **申請案件未設定 `district_id`** - 災民提交申請時沒有自動匹配區域

---

## ✅ 修復內容

### 1. 修復 Login API 返回 `district_id`

**檔案**: `app/routers/auth.py`

**修改前**:
```python
user={
    "id": str(user["id"]),
    "email": user["email"],
    "full_name": user.get("full_name", ""),
    "role": user["role"],
    "is_verified": user.get("is_verified", False)
}
```

**修改後**:
```python
user={
    "id": str(user["id"]),
    "email": user["email"],
    "full_name": user.get("full_name", ""),
    "role": user["role"],
    "is_verified": user.get("is_verified", False),
    "district_id": user.get("district_id")  # 新增
}
```

---

### 2. 新增 API 端點：按區域查詢申請案件

**檔案**: `app/routers/applications.py`

**新增端點**:
```python
@router.get("/district/{district_id}", response_model=APIResponse)
async def get_applications_by_district(
    district_id: str,
    status: Optional[str] = None,
    limit: int = 100
):
    """
    根據區域 ID 取得申請案件列表（里長專用）
    
    暫時方案: 返回所有案件（未來會根據地址自動匹配區域）
    """
```

**特色**:
- ✅ 支援狀態篩選 (`status` 參數)
- ✅ 支援數量限制 (`limit` 參數)
- ✅ 驗證區域是否存在
- ⚠️ **暫時方案**: 返回所有案件（因為災民申請時未設定 `district_id`）

---

### 3. 前端地圖功能防禦性檢查

**檔案**: `static/admin.html`

**修改 `loadMapApplications()` 函數**:
```javascript
async function loadMapApplications() {
    try {
        // 檢查 currentUser 是否存在
        if (!currentUser) {
            alert('請先登入');
            return;
        }
        
        // 檢查 district_id 是否存在
        if (!currentUser.district_id) {
            alert('您的帳號尚未設定管轄區域，請聯絡管理員');
            console.error('currentUser.district_id is undefined:', currentUser);
            return;
        }
        
        const response = await fetch(
            `${API_BASE}/applications/district/${currentUser.district_id}`,
            { headers: { 'Authorization': `Bearer ${accessToken}` } }
        );
        
        // ...
    } catch (error) {
        console.error('Error loading map applications:', error);
        alert('載入失敗：' + error.message);
    }
}
```

---

## 🔧 修復里長帳號 `district_id`

如果現有里長帳號沒有 `district_id`，使用以下腳本修復：

### 方法 1: 使用 `fix_reviewer_district_db.py` 腳本

```bash
cd /Users/steve.wang/Mix_Curry
python tests/fix_reviewer_district_db.py
```

**執行步驟**:
1. 輸入里長的 Email
2. 選擇管轄區域
3. 確認更新

### 方法 2: 重新創建里長帳號

```bash
python tests/create_reviewer.py
```

---

## 📊 資料庫結構

### `users` 表
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'applicant',
    district_id UUID REFERENCES districts(id), -- 里長管轄區域
    ...
);
```

### `applications` 表
```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY,
    case_no VARCHAR(50) UNIQUE NOT NULL,
    applicant_id UUID NOT NULL REFERENCES users(id),
    district_id UUID REFERENCES districts(id), -- 案件所屬區域
    ...
);
```

### `districts` 表
```sql
CREATE TABLE districts (
    id UUID PRIMARY KEY,
    district_code VARCHAR(20) UNIQUE NOT NULL,
    district_name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    ...
);
```

---

## 🧪 測試步驟

### 1. 確認里長帳號有 `district_id`

```bash
# 執行修復腳本
python tests/fix_reviewer_district_db.py

# 輸入里長 Email
請輸入里長的 Email: wangyouzhi248@gmail.com

# 選擇區域
請選擇區域編號: 1

# 確認更新
確定要更新嗎？ (y/N): y
```

### 2. 重新登入里長後台

```bash
# 1. 訪問 admin.html
open http://localhost:8080/admin

# 2. 使用 Email 驗證登入
- 輸入: wangyouzhi248@gmail.com
- 發送驗證碼
- 輸入驗證碼
- 登入成功
```

### 3. 測試地圖功能

```javascript
// 在 Chrome DevTools Console 中檢查
console.log('currentUser:', currentUser);
// 應該顯示: { ..., district_id: "ce97b599-..." }

console.log('accessToken:', accessToken ? '✓ 存在' : '✗ 不存在');
// 應該顯示: ✓ 存在
```

### 4. 載入地圖頁面

1. 點擊「📍 地圖」按鈕
2. 檢查是否成功載入 Google Maps
3. 檢查案件列表是否顯示
4. 檢查是否可以勾選案件

### 5. 測試路線規劃

1. 勾選 2-3 個案件
2. 點擊「📍 在地圖上顯示選取的案件」
3. 確認標記顯示在地圖上
4. 點擊「🚗 規劃最佳路線」
5. 確認顯示 Top 3 路線

---

## 🔄 未來改進計劃

### 自動設定 `district_id`

當災民提交申請時，根據地址自動匹配區域：

```python
# app/routers/applications.py

async def create_application(application: ApplicationCreate):
    # 根據地址解析區域
    district_id = await match_district_by_address(application.address)
    application_data = application.model_dump()
    application_data['district_id'] = district_id
    
    result = db_service.create_application(application_data)
    # ...
```

**地址解析策略**:
1. 使用 Google Maps Geocoding API 取得經緯度
2. 使用 Reverse Geocoding 取得完整地址
3. 解析「區」和「里」資訊
4. 匹配 `districts` 表中的區域

---

## 📝 修改檔案清單

```
修改的檔案:
├── app/routers/auth.py                    ✅ 修復 login API 返回 district_id
├── app/routers/applications.py            ✅ 新增 /district/{district_id} 端點
├── static/admin.html                      ✅ 新增防禦性檢查
└── tests/fix_reviewer_district_db.py      ✅ 新建修復腳本

文檔:
└── docs/ADMIN_MAP_FEATURE_FIX.md         ✅ 本文檔
```

---

## ⚠️ 已知限制

### 暫時方案說明

由於目前災民提交申請時**未自動設定 `district_id`**，`/api/v1/applications/district/{district_id}` 端點：

- ✅ **目前**: 返回所有申請案件（不限區域）
- 🔄 **未來**: 僅返回該區域的案件

**原因**: 如果只返回 `district_id` 匹配的案件，里長會看不到任何案件（因為所有案件的 `district_id` 都是 `null`）。

---

## ✅ 驗證結果

### API 測試

```bash
# 1. 測試登入 API
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "wangyouzhi248@gmail.com",
    "login_type": "password",
    "verify": true
  }'

# 回應應包含:
{
  "access_token": "...",
  "user": {
    "district_id": "ce97b599-cf02-4a09-8918-1438f7747de7"  # ✓ 存在
  }
}

# 2. 測試案件查詢 API
curl -X GET "http://localhost:8080/api/v1/applications/district/ce97b599-cf02-4a09-8918-1438f7747de7" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 回應應包含:
{
  "success": true,
  "data": {
    "applications": [...],  # ✓ 案件列表
    "total": 5,
    "note": "⚠️ 暫時顯示所有案件..."
  }
}
```

---

## 📞 問題排查

### 如果還是看不到地圖

1. **檢查 Console 錯誤**
   ```javascript
   // Chrome DevTools > Console
   console.log('currentUser:', currentUser);
   console.log('district_id:', currentUser?.district_id);
   ```

2. **檢查 Network 請求**
   ```
   Chrome DevTools > Network > Filter: district
   - 確認 URL 不是 /district/undefined
   - 確認回應是 200，不是 404
   ```

3. **重新執行修復腳本**
   ```bash
   python tests/fix_reviewer_district_db.py
   ```

4. **清除瀏覽器快取並重新登入**
   ```javascript
   localStorage.clear();
   location.reload();
   ```

---

## 🎉 完成檢查清單

- [x] Login API 返回 `district_id`
- [x] 新增 `/applications/district/{district_id}` API 端點
- [x] 前端地圖功能加入防禦性檢查
- [x] 創建修復腳本 `fix_reviewer_district_db.py`
- [x] 撰寫完整測試指南
- [x] 測試 API 端點正常運作
- [ ] 實作自動地址解析 `district_id`（未來計劃）

---

**更新日期**: 2025-10-28  
**狀態**: ✅ 基本功能完成，可以測試
