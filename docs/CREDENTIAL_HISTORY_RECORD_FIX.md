# 憑證歷史記錄重複問題修復

## 更新日期
2025-11-19

## 問題描述

### 原始問題
使用者在領取憑證時，系統記錄了 **3 筆歷史記錄**，但實際上只需要記錄 **2 筆**：
1. **憑證發行**（審核通過時）
2. **憑證驗證**（在 7-11 或其他地點驗證時）

### 錯誤的記錄流程
```
1. 審核通過 → 記錄「憑證發行」✅
2. 使用者掃描 QR Code → 記錄「憑證領取」❌ (重複)
3. 7-11 驗證 → 記錄「憑證驗證」✅
```

### 正確的記錄流程
```
1. 審核通過 → 記錄「憑證發行」✅
2. 使用者掃描 QR Code → 不記錄
3. 7-11 驗證 → 記錄「憑證驗證」✅
```

---

## 根本原因分析

### 1. 重複的 API Endpoint
在 `complete_flow.py` 中存在一個專門用於記錄憑證領取的 endpoint：

```python
@router.post("/record-credential-claimed")
async def record_credential_claimed_endpoint(
    application_id: str,
    transaction_id: str
):
    """
    📝 記錄憑證領取（當用戶掃描 QR Code 並儲存憑證到手機時調用）
    """
    # 記錄憑證領取歷史
    await record_credential_history(
        application_id=application_id,
        user_id=application.get("applicant_id"),
        action_type="credential_issued",  # ❌ 與審核通過時重複
        status="issued",
        transaction_id=transaction_id,
        issuer_organization="台南市政府災害救助中心",
        notes="使用者已掃描 QR Code 並將憑證儲存至數位皮夾"
    )
```

### 2. 前端調用該 API
在 `applicant.html` 中，當檢測到使用者掃描 QR Code 後會調用此 API：

```javascript
// 記錄憑證領取歷史
try {
  const historyResponse = await fetch(
    `${API_BASE}/complete-flow/record-credential-claimed?application_id=${applicationId}&transaction_id=${transactionId}`, 
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  if (historyResponse.ok) {
    console.log('✅ 憑證領取歷史已記錄');
  }
} catch (historyError) {
  console.error('記錄憑證領取歷史失敗:', historyError);
}
```

### 3. 問題總結
- **審核通過時**：`/review-and-issue` API 會記錄一次「憑證發行」
- **掃描 QR Code 時**：`/record-credential-claimed` API 又記錄一次「憑證發行」
- **結果**：同一個動作被記錄了兩次

---

## 修復方案

### 方案選擇
刪除 `/record-credential-claimed` endpoint 和前端調用，理由：
1. ✅ **憑證發行已在審核通過時記錄**
2. ✅ **使用者掃描 QR Code 只是領取憑證的動作，不需要額外記錄**
3. ✅ **保持記錄簡潔，只記錄關鍵動作**

### 修復步驟

#### 1. 刪除後端 API Endpoint
**檔案**: `/Users/steve.wang/Mix_Curry/app/routers/complete_flow.py`

```python
# 刪除整個 endpoint
@router.post("/record-credential-claimed")
async def record_credential_claimed_endpoint(...):
    ...
```

#### 2. 移除前端 API 調用
**檔案**: `/Users/steve.wang/Mix_Curry/static/applicant.html`

```javascript
// 修改前：調用 API 記錄
try {
  const historyResponse = await fetch(`${API_BASE}/complete-flow/record-credential-claimed...`);
  ...
} catch (historyError) {
  ...
}

// 修改後：只留下註解說明
// 憑證領取歷史已在審核通過時記錄，不需要重複記錄
```

---

## 額外優化

### 1. 新增統計卡片
在管理員後台的憑證記錄頁面新增 4 個統計卡片：

```html
<!-- 統計卡片 -->
<div class="stats-header" style="margin-bottom: 20px;">
  <div class="stat-card">
    <div class="stat-label">總記錄</div>
    <div class="stat-value" id="historyStatTotal">-</div>
    <div class="stat-unit">筆</div>
    <div class="stat-icon" style="background: #e0e7ff;">📊</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">已發行憑證</div>
    <div class="stat-value" id="historyStatIssued">-</div>
    <div class="stat-unit">張</div>
    <div class="stat-icon" style="background: #fef3c7;">📄</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">已驗證憑證</div>
    <div class="stat-value" id="historyStatVerified">-</div>
    <div class="stat-unit">張</div>
    <div class="stat-icon" style="background: #d1fae5;">✓</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">驗證率</div>
    <div class="stat-value" id="historyStatRate">-</div>
    <div class="stat-unit">%</div>
    <div class="stat-icon" style="background: #dbeafe;">📈</div>
  </div>
</div>
```

### 2. 統計卡片邏輯
在 `loadHistory()` 函數中計算統計數據：

```javascript
// 更新統計卡片
const totalRecords = allHistory.length;
const issuedCount = allHistory.filter(h => h.result === 'issued').length;
const verifiedCount = allHistory.filter(h => h.result === 'verified').length;
const verificationRate = issuedCount > 0 ? Math.round((verifiedCount / issuedCount) * 100) : 0;

document.getElementById('historyStatTotal').textContent = totalRecords || '0';
document.getElementById('historyStatIssued').textContent = issuedCount || '0';
document.getElementById('historyStatVerified').textContent = verifiedCount || '0';
document.getElementById('historyStatRate').textContent = verificationRate || '0';
```

### 3. 修復時區問題
Supabase 儲存的是 UTC 時間，需要轉換為台北時間（UTC+8）：

```javascript
// 修改前：沒有指定時區
return date.toLocaleString('zh-TW', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit'
});

// 修改後：指定台北時區
return date.toLocaleString('zh-TW', {
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  timeZone: 'Asia/Taipei'  // 指定台北時區
});
```

---

## 修改的檔案

### 1. **app/routers/complete_flow.py**
- ❌ 刪除 `/record-credential-claimed` endpoint
- ✅ 保留審核通過時的記錄邏輯
- ✅ 保留驗證時的記錄邏輯

### 2. **static/applicant.html**
- ❌ 移除對 `/record-credential-claimed` 的 API 調用
- ✅ 新增註解說明不需要重複記錄

### 3. **static/admin.html**
- ✅ 新增統計卡片 HTML 結構
- ✅ 在 `loadHistory()` 中新增統計卡片更新邏輯
- ✅ 修改 `formatDateTime()` 函數，新增台北時區轉換

---

## 測試建議

### 功能測試
- [ ] 審核通過後，檢查是否只記錄 1 筆「已發行」
- [ ] 使用者掃描 QR Code 後，檢查是否沒有新增記錄
- [ ] 在 7-11 驗證後，檢查是否只記錄 1 筆「已驗證」
- [ ] 總共應該只有 2 筆記錄（發行 + 驗證）

### 統計卡片測試
- [ ] 總記錄數是否正確
- [ ] 已發行憑證數是否正確
- [ ] 已驗證憑證數是否正確
- [ ] 驗證率計算是否正確（已驗證 / 已發行 × 100%）

### 時區測試
- [ ] 驗證時間是否顯示為台北時間
- [ ] 時間是否比 Supabase UTC 時間晚 8 小時
- [ ] 時間格式是否正確（YYYY/MM/DD HH:mm）

---

## 資料庫清理（可選）

如果需要清理現有的重複記錄，可以執行以下 SQL：

```sql
-- 查看重複記錄
SELECT 
  application_id,
  action_type,
  status,
  COUNT(*) as count
FROM credential_history
WHERE action_type = 'credential_issued'
  AND status = 'issued'
GROUP BY application_id, action_type, status
HAVING COUNT(*) > 1;

-- 刪除重複記錄（保留最早的一筆）
DELETE FROM credential_history
WHERE id NOT IN (
  SELECT MIN(id)
  FROM credential_history
  WHERE action_type = 'credential_issued'
    AND status = 'issued'
  GROUP BY application_id
);
```

**⚠️ 警告**：執行刪除操作前請先備份資料庫！

---

## 正確的記錄時機

### 1. 憑證發行（issued）
**時機**：管理員審核通過時  
**觸發點**：`POST /complete-flow/review-and-issue`  
**記錄內容**：
- action_type: `credential_issued`
- status: `issued`
- issuer_organization: 台南市政府災害救助中心
- notes: 憑證發行成功，核准金額: NT$ XX,XXX

### 2. 憑證驗證（verified）
**時機**：在 7-11 或其他地點驗證時  
**觸發點**：`POST /complete-flow/verify-vp`  
**記錄內容**：
- action_type: `credential_verified`
- status: `verified`
- verifier_organization: 7-11 便利商店
- verification_location: { type: "711_store", ... }
- notes: 在 7-11 機台驗證成功，補助已發放

---

## credential_history Table Schema

```sql
CREATE TABLE credential_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  application_id UUID REFERENCES applications(id),
  user_id UUID REFERENCES users(id),
  action_type TEXT NOT NULL,  -- 'credential_issued' or 'credential_verified'
  status TEXT NOT NULL,        -- 'issued' or 'verified'
  action_time TIMESTAMPTZ DEFAULT NOW(),
  transaction_id TEXT,
  issuer_organization TEXT,
  verifier_organization TEXT,
  verification_location JSONB,
  certificate_id TEXT,
  notes TEXT,
  
  -- 冗余字段用於快速查詢
  applicant_name TEXT,
  disaster_type TEXT,
  disaster_address TEXT,
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 結論

本次修復成功解決了憑證歷史記錄重複的問題，並新增了統計卡片和時區轉換功能。

**主要成果**：
- ✅ 移除重複的憑證領取記錄邏輯
- ✅ 確保每個申請只記錄 2 筆（發行 + 驗證）
- ✅ 新增 4 個統計卡片（總記錄、已發行、已驗證、驗證率）
- ✅ 修復時區問題（UTC → UTC+8 台北時間）
- ✅ 保持記錄簡潔明確

**資料流程圖**：
```
審核通過
  ↓
記錄「憑證發行」
  ↓
使用者掃描 QR Code
  ↓ (不記錄)
憑證存入手機
  ↓
前往 7-11 驗證
  ↓
記錄「憑證驗證」
  ↓
完成
```

**下一步建議**：
- 考慮新增更多統計維度（如：按災害類型統計）
- 考慮新增時間範圍篩選（如：本月、本季、本年）
- 考慮匯出功能（CSV/Excel）
