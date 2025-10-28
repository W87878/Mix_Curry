# 🎯 最終解決方案：里長地圖功能完整修復指南

## 📋 問題總結

從對話中發現的問題：

1. ✅ **伺服器運行正常** - API 端點都正常回應
2. ✅ **案件已創建** - CASE-2025-00003, CASE-2025-00002, CASE-2025-00001
3. ❌ **地圖功能無法顯示** - 彈出「沒有可顯示的案件位置」
4. ❌ **路線規劃失敗** - 422 錯誤，`destinations` 為空陣列

---

## 🔍 根本原因

問題出在：**前端取得的案件資料中，地址欄位 (`damage_location`, `address`) 是 `null` 或 `undefined`**

可能的原因：
1. 資料庫欄位名稱不一致
2. API 回傳的資料結構不完整
3. 前端讀取欄位名稱錯誤

---

## ✅ 立即解決方案

### 步驟 1: 檢查案件資料

在 Chrome DevTools Console 中執行：

```javascript
// 1. 檢查原始 API 回應
fetch('https://YOUR_NGROK_URL/api/v1/applications/district/YOUR_DISTRICT_ID', {
    headers: { 'Authorization': 'Bearer ' + accessToken }
})
.then(r => r.json())
.then(data => {
    console.log('📦 API 原始回應:', data);
    console.log('📦 案件數量:', data.data?.applications?.length);
    
    if (data.data?.applications?.length > 0) {
        console.log('📦 第一個案件的所有欄位:', Object.keys(data.data.applications[0]));
        console.log('📦 第一個案件完整資料:', data.data.applications[0]);
    }
});

// 2. 檢查已載入的案件
console.log('📦 allMapApplications:', allMapApplications);
if (allMapApplications.length > 0) {
    console.log('📦 第一個案件:', allMapApplications[0]);
}
```

---

### 步驟 2: 根據 Console 輸出判斷

#### 情況 A: 如果 Console 顯示案件有地址

```javascript
// 例如：
{
    case_no: "CASE-2025-00001",
    damage_location: "台南市中西區民權路一段100號",
    address: "台南市中西區民權路一段100號"
}
```

**解決方案**: 前端程式碼正確，繼續測試。

---

#### 情況 B: 如果 Console 顯示案件沒有地址

```javascript
// 例如：
{
    case_no: "CASE-2025-00001",
    damage_location: null,
    address: null
}
```

**解決方案**: 需要重新創建案件或更新現有案件。

---

### 步驟 3: 直接使用災民端提交新案件

最簡單的方法是：**直接從災民端提交一個新案件**（確保包含地址）

1. 訪問 http://localhost:8080/applicant
2. 使用 Email 驗證登入
3. 填寫申請表單，**確保填寫「災損地點」**：
   ```
   災損地點: 台南市中西區民權路一段100號
   聯絡地址: 台南市中西區民權路一段100號
   ```
4. 提交申請

---

### 步驟 4: 直接修改前端，使用測試地址

如果上述方法都不行，我們可以在前端直接使用測試地址：

在 `static/admin.html` 中，找到 `planRoutes()` 函數，添加以下測試代碼：

```javascript
// 🧪 測試：如果沒有地址，使用測試地址
const destinations = applications
    .map((app, index) => {
        let addr = app.damage_location || app.address || app.formatted_address;
        
        // 🧪 如果沒有地址，使用測試地址
        if (!addr || addr.trim().length === 0) {
            const testAddresses = [
                "台南市中西區民權路一段100號",
                "台南市東區裕農路200號",
                "台南市南區金華路三段300號"
            ];
            addr = testAddresses[index % testAddresses.length];
            console.warn(`⚠️ 案件 ${app.case_no} 沒有地址，使用測試地址: ${addr}`);
        }
        
        return addr;
    })
    .filter(addr => addr && addr.trim().length > 0);
```

---

## 🧪 完整測試腳本

我創建一個新的測試腳本，直接檢查並修復資料庫中的案件：

```bash
cd /Users/steve.wang/Mix_Curry
python tests/diagnose_and_fix_applications.py
```

這個腳本會：
1. ✅ 檢查所有案件的地址欄位
2. ✅ 顯示哪些案件缺少地址
3. ✅ 提供修復選項

---

## 📊 預期結果

### 成功的 Console 輸出

```javascript
🚀 開始規劃路線...
📊 當前狀態: {
    selectedApplications: ["uuid1", "uuid2", "uuid3"],
    selectedCount: 3,
    allMapApplications: [
        {
            case_no: "CASE-2025-00001",
            damage_location: "台南市中西區民權路一段100號",
            address: "台南市中西區民權路一段100號"
        },
        // ...
    ],
    allMapCount: 3
}

✅ 選中的案件: {
    total: 3,
    selectedIds: ["uuid1", "uuid2", "uuid3"],
    matchedApps: [...]
}

📌 案件 CASE-2025-00001: {
    damage_location: "台南市中西區民權路一段100號",
    address: "台南市中西區民權路一段100號",
    formatted_address: undefined,
    selected: "台南市中西區民權路一段100號"
}

📌 案件 CASE-2025-00002: {
    damage_location: "台南市東區裕農路200號",
    address: "台南市東區裕農路200號",
    formatted_address: undefined,
    selected: "台南市東區裕農路200號"
}

📍 路線規劃資料: {
    applications: 3,
    destinations: [
        "台南市中西區民權路一段100號",
        "台南市東區裕農路200號",
        "台南市南區金華路三段300號"
    ],
    selectedApplications: ["uuid1", "uuid2", "uuid3"]
}

✓ 使用區域辦公處作為起點: 中西區辦公處

🚗 發送路線規劃請求: {
    start_location: "中西區辦公處",
    destinations: [
        "台南市中西區民權路一段100號",
        "台南市東區裕農路200號",
        "台南市南區金華路三段300號"
    ],
    mode: "driving"
}

✅ 路線規劃成功: {
    routes: [...]
}
```

---

## 🎯 快速除錯檢查清單

- [ ] 1. 伺服器正在運行？(`python main.py`)
- [ ] 2. 已登入里長帳號？(有 `district_id`)
- [ ] 3. 點擊「載入案件列表」？
- [ ] 4. Console 顯示案件數量 > 0？
- [ ] 5. Console 顯示案件有地址？(`damage_location` 或 `address` 不是 null)
- [ ] 6. 勾選了 2 個以上的案件？
- [ ] 7. 點擊「規劃最佳路線」？
- [ ] 8. Console 沒有錯誤？

---

## 📞 如果還是不行

請提供以下資訊：

1. **Console 完整輸出** (從點擊「規劃最佳路線」開始)
2. **Network 標籤中 `applications-map-data` 的回應**
3. **執行以下命令的輸出**：

```javascript
// 在 Console 中執行
console.log('=== 診斷資訊 ===');
console.log('currentUser:', currentUser);
console.log('accessToken:', accessToken ? '✓ 有' : '✗ 無');
console.log('allMapApplications 數量:', allMapApplications.length);
console.log('selectedApplications:', selectedApplications);

if (allMapApplications.length > 0) {
    console.log('第一個案件完整資料:', allMapApplications[0]);
}
```

把輸出截圖或複製貼上給我！ 📸

---

**更新日期**: 2025-10-28  
**狀態**: 等待診斷結果
