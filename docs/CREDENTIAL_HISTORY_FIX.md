# 憑證歷史記錄修復

## 📋 問題描述

1. **資料來源錯誤**：前端從 `applications` table 讀取資料，而不是從 `credential_history` table
2. **UI 問題**：重新整理按鈕文字太長

## ✅ 修復內容

### 1. 後端 API 新增

**檔案**：`app/routers/complete_flow.py`

新增 API endpoint：
```python
@router.get("/credential-history-list")
async def get_credential_history_list(
    skip: int = 0,
    limit: int = 100,
    disaster_type: Optional[str] = None,
    status: Optional[str] = None
):
```

**功能**：
- 從 `credential_history` table 讀取真實的憑證使用記錄
- 支援分頁（skip, limit）
- 支援災害類型篩選（flood/typhoon/earthquake/fire）
- 支援狀態篩選（issued/verified）

### 2. 前端修改

**檔案**：`static/admin.html`

#### 2.1 修改 `loadHistory()` 函數

**變更前**：
```javascript
// 從 applications table 讀取資料
const historyResponse = await fetch(`${API_BASE}/applications/?limit=1000`, {...});

// 轉換 applications 為歷史記錄
allHistory = applications
  .filter(app => app.status === 'approved' || app.status === 'disbursed')
  .map(app => ({...}));
```

**變更後**：
```javascript
// 從 credential_history table 讀取真實資料
const historyResponse = await fetch(
  `${API_BASE}/complete-flow/credential-history-list?${params.toString()}`, 
  {...}
);

// 直接使用 credential_history 記錄
allHistory = records.map(record => ({
  id: record.id,
  applicant_name: record.applicant_name,
  subsidy_type: getDisasterTypeText(record.disaster_type) + '補助',
  disaster_region: extractRegion(record.disaster_address),
  result: record.status, // 'issued' or 'verified'
  issuer_organization: record.issuer_organization || 'N/A',
  verifier_organization: record.verifier_organization || 'N/A',
  action_time: record.action_time
}));
```

#### 2.2 優化篩選邏輯

**變更前**：
```javascript
// 在前端做所有篩選（補助類型、狀態、搜尋）
if (subsidyFilter) {
  filteredHistory = filteredHistory.filter(h => h.subsidy_type.includes(subsidyFilter));
}
if (resultFilter) {
  filteredHistory = filteredHistory.filter(h => h.result === resultFilter);
}
if (searchInput) {
  filteredHistory = filteredHistory.filter(h => ...);
}
```

**變更後**：
```javascript
// API 層面做篩選（補助類型、狀態）
params.append('disaster_type', typeMap[subsidyFilter]);
params.append('status', resultFilter);

// 前端只做搜尋框篩選
if (searchInput) {
  filteredHistory = filteredHistory.filter(h => 
    h.applicant_name && h.applicant_name.toLowerCase().includes(searchInput)
  );
}
```

#### 2.3 重新整理按鈕

**變更前**：
```html
<button class="btn btn-secondary" onclick="loadHistory()">
  🔄 重新整理
</button>
```

**變更後**：
```html
<button class="btn btn-secondary" onclick="loadHistory()" title="重新整理">
  🔄
</button>
```

## 🔄 資料流程

### 修復前
```
admin.html (loadHistory)
  ↓
GET /applications/?limit=1000
  ↓
從 applications table 讀取所有申請
  ↓
前端過濾 status = 'approved' 或 'disbursed'
  ↓
前端轉換為歷史記錄格式
  ↓
顯示（模擬的歷史記錄）
```

### 修復後
```
admin.html (loadHistory)
  ↓
GET /complete-flow/credential-history-list?disaster_type=flood&status=issued
  ↓
從 credential_history table 讀取真實記錄
  ↓
後端篩選（災害類型、狀態）
  ↓
前端篩選（搜尋姓名）
  ↓
顯示（真實的憑證使用記錄）
```

## 📊 資料結構

### credential_history table 欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| id | UUID | 記錄 ID |
| application_id | UUID | 申請案件 ID |
| user_id | UUID | 使用者 ID |
| applicant_name | TEXT | 申請人姓名 |
| disaster_type | TEXT | 災害類型 |
| disaster_address | TEXT | 受災地址 |
| action_type | TEXT | 動作類型 (credential_issued/verified) |
| status | TEXT | 狀態 (issued/verified) |
| issuer_organization | TEXT | 發行機構 |
| verifier_organization | TEXT | 驗證機構 |
| action_time | TIMESTAMP | 動作時間 |

## 🧪 測試步驟

### 1. 檢查資料庫

```sql
-- 查看 credential_history table 是否有資料
SELECT COUNT(*) FROM credential_history;

-- 查看記錄內容
SELECT 
  applicant_name,
  disaster_type,
  status,
  action_type,
  issuer_organization,
  verifier_organization,
  action_time
FROM credential_history
ORDER BY action_time DESC
LIMIT 10;
```

### 2. 測試 API

```bash
# 測試新的 API endpoint
curl -X GET "http://localhost:8000/api/v1/complete-flow/credential-history-list?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 測試篩選功能
curl -X GET "http://localhost:8000/api/v1/complete-flow/credential-history-list?disaster_type=flood&status=issued" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. 前端測試

1. 刷新管理員後台頁面
2. 點擊「憑證記錄」tab
3. 檢查是否顯示真實的 credential_history 資料
4. 測試篩選器（補助類型、結果）
5. 測試搜尋框（按姓名搜尋）
6. 檢查重新整理按鈕（只顯示 🔄 符號）

## 📝 注意事項

### 資料生成

`credential_history` 記錄由以下流程自動生成：

1. **憑證發行時**（補助核准後）
   - 調用 `record_credential_history()`
   - `action_type`: 'credential_issued'
   - `status`: 'issued'
   - `issuer_organization`: 發行機構名稱

2. **憑證驗證時**（在便利商店領取補助時）
   - 調用 `record_credential_history()`
   - `action_type`: 'credential_verified'
   - `status`: 'verified'
   - `verifier_organization`: 驗證機構名稱（如：7-11 中正門市）

### 如果資料庫沒有記錄

如果 `credential_history` table 是空的：
1. 這是正常的，因為記錄只在憑證發行/驗證時才會產生
2. 需要完整執行一次補助流程：申請 → 審核 → 核准 → 發行憑證 → 驗證憑證
3. 可以使用測試腳本 `tests/test_credential_history.py` 來生成測試資料

## 🎯 預期結果

修復後：
- ✅ 顯示真實的憑證使用記錄（來自 credential_history table）
- ✅ 篩選功能正常（補助類型、狀態、搜尋）
- ✅ 重新整理按鈕只顯示符號
- ✅ 如果沒有記錄，顯示「📭 目前沒有憑證記錄」
- ✅ 性能更好（API 層面篩選，減少前端處理）

修復前：
- ❌ 顯示從 applications table 模擬的記錄
- ❌ 即使 credential_history 是空的也會顯示資料
- ❌ 資料不準確（issuer/verifier 組織是假的）
