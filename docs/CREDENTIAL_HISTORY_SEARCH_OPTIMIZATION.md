# 憑證歷史記錄搜尋與排序優化

## 更新日期
2025-01-XX

## 概述
優化管理員後台的憑證歷史記錄頁面，將多個篩選器整合為統一的搜尋框，並新增驗證時間排序功能。

---

## 優化內容

### 1. 統一搜尋框 (Unified Search Box)

#### 修改前
- **3 個獨立篩選器**：
  - 補助類型下拉選單（水災/颱風/地震/火災）
  - 結果下拉選單（已發行/已驗證）
  - 姓名搜尋框（只能搜尋姓名）

#### 修改後
- **1 個統一搜尋框** + **2 個下拉選單**：
  - 統一搜尋框：支援多欄位搜尋
  - 排序下拉選單：驗證時間排序
  - 結果下拉選單：已發行/已驗證

#### 搜尋支援的欄位
統一搜尋框現在支援以下欄位：

| 欄位 | 說明 | 範例 |
|------|------|------|
| 姓名 | 申請人姓名 | "王小明" |
| 補助類型 | 災害類型 | "水災補助", "颱風", "地震" |
| 發行機構 | 憑證發行單位 | "花蓮縣政府", "社會局" |
| 驗證機構 | 憑證驗證單位 | "超商", "銀行" |

#### 搜尋邏輯
```javascript
if (searchInput) {
  filteredHistory = filteredHistory.filter(h => {
    // 搜尋姓名
    if (h.applicant_name && h.applicant_name.toLowerCase().includes(searchInput)) {
      return true;
    }
    // 搜尋補助類型
    if (h.subsidy_type && h.subsidy_type.toLowerCase().includes(searchInput)) {
      return true;
    }
    // 搜尋發行機構
    if (h.issuer_organization && h.issuer_organization.toLowerCase().includes(searchInput)) {
      return true;
    }
    // 搜尋驗證機構
    if (h.verifier_organization && h.verifier_organization.toLowerCase().includes(searchInput)) {
      return true;
    }
    return false;
  });
}
```

---

### 2. 驗證時間排序 (Verification Time Sorting)

#### 新增功能
- **排序下拉選單**：
  - 驗證時間（新到舊）- 預設選項
  - 驗證時間（舊到新）

#### 排序實現
```javascript
// 取得排序條件
const sortBy = document.getElementById('historySortBy')?.value || 'time_desc';

// 排序
if (sortBy === 'time_desc') {
  // 驗證時間（新到舊）
  filteredHistory.sort((a, b) => new Date(b.verification_time) - new Date(a.verification_time));
} else if (sortBy === 'time_asc') {
  // 驗證時間（舊到新）
  filteredHistory.sort((a, b) => new Date(a.verification_time) - new Date(b.verification_time));
}
```

---

## UI 結構變化

### 修改前
```html
<select id="historySubsidyFilter">...</select>
<select id="historyResultFilter">...</select>
<input id="historySearchInput" placeholder="🔍 搜尋申請人姓名..." />
<button>🔄</button>
```

### 修改後
```html
<input id="historySearchInput" 
       placeholder="🔍 搜尋姓名、補助類型、發行/驗證機構..." 
       style="width: 400px;" />
<select id="historySortBy">
  <option value="time_desc">驗證時間（新到舊）</option>
  <option value="time_asc">驗證時間（舊到新）</option>
</select>
<select id="historyResultFilter">...</select>
<button>🔄</button>
```

---

## 功能流程

### 篩選和排序流程
```
使用者輸入/選擇
  ↓
1. 從 API 獲取資料（後端篩選：status）
  ↓
2. 前端統一搜尋框過濾（姓名、補助類型、機構）
  ↓
3. 前端排序（驗證時間）
  ↓
4. 渲染表格
```

### 資料流向
```
credential_history table
  ↓
GET /api/v1/complete-flow/credential-history-list?status=xxx
  ↓ (後端篩選)
前端統一搜尋框
  ↓ (多欄位 OR 搜尋)
前端排序
  ↓ (按驗證時間)
表格顯示
```

---

## 程式碼變更

### 1. HTML 結構修改

**檔案**: `/Users/steve.wang/Mix_Curry/static/admin.html`

```html
<!-- 修改前：3 個篩選器 -->
<select id="historySubsidyFilter" onchange="loadHistory()">
  <option value="">所有補助類型</option>
  <option value="水災">水災補助</option>
  ...
</select>
<select id="historyResultFilter" onchange="loadHistory()">
  <option value="">所有結果</option>
  <option value="issued">已發行</option>
  <option value="verified">已驗證</option>
</select>
<input id="historySearchInput" placeholder="🔍 搜尋申請人姓名..." />

<!-- 修改後：1 個搜尋框 + 2 個下拉選單 -->
<input 
  id="historySearchInput" 
  placeholder="🔍 搜尋姓名、補助類型、發行/驗證機構..." 
  style="width: 400px;"
  onkeyup="loadHistory()"
/>
<select id="historySortBy" onchange="loadHistory()">
  <option value="time_desc">驗證時間（新到舊）</option>
  <option value="time_asc">驗證時間（舊到新）</option>
</select>
<select id="historyResultFilter" onchange="loadHistory()">
  <option value="">所有結果</option>
  <option value="issued">已發行</option>
  <option value="verified">已驗證</option>
</select>
```

### 2. JavaScript 邏輯修改

**檔案**: `/Users/steve.wang/Mix_Curry/static/admin.html`

```javascript
// 修改前：只能搜尋姓名
if (searchInput) {
  filteredHistory = filteredHistory.filter(h => 
    h.applicant_name && h.applicant_name.toLowerCase().includes(searchInput)
  );
}

// 修改後：多欄位 OR 搜尋
if (searchInput) {
  filteredHistory = filteredHistory.filter(h => {
    return (
      (h.applicant_name && h.applicant_name.toLowerCase().includes(searchInput)) ||
      (h.subsidy_type && h.subsidy_type.toLowerCase().includes(searchInput)) ||
      (h.issuer_organization && h.issuer_organization.toLowerCase().includes(searchInput)) ||
      (h.verifier_organization && h.verifier_organization.toLowerCase().includes(searchInput))
    );
  });
}

// 新增：排序功能
const sortBy = document.getElementById('historySortBy')?.value || 'time_desc';
if (sortBy === 'time_desc') {
  filteredHistory.sort((a, b) => new Date(b.verification_time) - new Date(a.verification_time));
} else if (sortBy === 'time_asc') {
  filteredHistory.sort((a, b) => new Date(a.verification_time) - new Date(b.verification_time));
}
```

---

## 使用範例

### 範例 1：搜尋特定姓名
- **輸入**：`王小明`
- **結果**：顯示所有姓名包含"王小明"的記錄

### 範例 2：搜尋特定補助類型
- **輸入**：`水災`
- **結果**：顯示所有"水災補助"類型的記錄

### 範例 3：搜尋特定機構
- **輸入**：`花蓮縣政府`
- **結果**：顯示所有由"花蓮縣政府"發行或驗證的記錄

### 範例 4：組合篩選
- **搜尋框**：`超商`
- **結果篩選**：`已驗證`
- **排序**：`驗證時間（新到舊）`
- **結果**：顯示所有在超商驗證的已驗證記錄，按時間新到舊排序

---

## 優勢與效益

### 1. 使用者體驗提升
- ✅ **更簡潔的介面**：從 3 個篩選器減少到 1 個搜尋框
- ✅ **更快速的搜尋**：一個搜尋框涵蓋多個欄位
- ✅ **更直覺的操作**：不需要記住哪個欄位在哪個篩選器

### 2. 功能增強
- ✅ **多欄位搜尋**：支援姓名、補助類型、機構名稱
- ✅ **OR 邏輯**：只要任一欄位符合即顯示
- ✅ **時間排序**：快速查看最新/最舊的記錄

### 3. 維護性提升
- ✅ **程式碼更簡潔**：移除不需要的補助類型篩選器
- ✅ **邏輯更清晰**：統一的搜尋函數
- ✅ **易於擴充**：未來可輕鬆新增更多搜尋欄位

---

## 測試建議

### 功能測試
- [ ] 搜尋姓名是否正確
- [ ] 搜尋補助類型是否正確（包含"水災"、"颱風"、"地震"等）
- [ ] 搜尋發行機構是否正確
- [ ] 搜尋驗證機構是否正確
- [ ] 時間排序（新到舊）是否正確
- [ ] 時間排序（舊到新）是否正確
- [ ] 結果篩選（已發行/已驗證）是否正確
- [ ] 組合搜尋（搜尋框 + 結果篩選 + 排序）是否正確

### 邊界測試
- [ ] 空搜尋框（應顯示所有記錄）
- [ ] 搜尋不存在的內容（應顯示"目前沒有憑證記錄"）
- [ ] 特殊字元搜尋（如 `/`, `\`, `'`, `"`）
- [ ] 超長搜尋字串
- [ ] 大小寫混合搜尋（應不區分大小寫）

### 效能測試
- [ ] 1000 筆記錄的搜尋速度
- [ ] 排序 1000 筆記錄的速度
- [ ] 連續快速輸入搜尋關鍵字的反應

---

## 已知問題與限制

### 1. 搜尋延遲
- **問題**：每次按鍵都觸發搜尋，可能造成卡頓
- **建議**：考慮加入 debounce（300ms）

### 2. 無進階搜尋
- **限制**：無法使用 AND 邏輯（例如："姓名 AND 機構"）
- **建議**：未來可考慮加入進階搜尋模式

### 3. 無搜尋高亮
- **限制**：搜尋結果未高亮顯示匹配文字
- **建議**：未來可考慮在表格中高亮匹配的關鍵字

---

## 未來擴充方向

### 1. 加入 Debounce
```javascript
let searchTimeout;
document.getElementById('historySearchInput').addEventListener('keyup', () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    loadHistory();
  }, 300);
});
```

### 2. 加入進階搜尋模式
- 支援 AND/OR 運算子
- 支援欄位指定（如：`name:王小明 org:花蓮`）

### 3. 加入匹配高亮
```javascript
function highlightMatch(text, searchInput) {
  if (!searchInput) return text;
  const regex = new RegExp(`(${searchInput})`, 'gi');
  return text.replace(regex, '<mark>$1</mark>');
}
```

### 4. 加入搜尋歷史
- 記住使用者最近的搜尋關鍵字
- 提供快速選擇

---

## 結論

本次優化成功整合了多個篩選器為一個統一的搜尋框，並新增了時間排序功能。這些改進顯著提升了使用者體驗，使憑證歷史記錄的查詢更加直覺和高效。

**主要成果**：
- ✅ 統一搜尋框（支援 4 個欄位）
- ✅ 時間排序（新到舊/舊到新）
- ✅ UI 簡化（從 3 個篩選器減少到 1 個搜尋框）
- ✅ 邏輯優化（多欄位 OR 搜尋）

**下一步**：
- 加入 debounce 優化效能
- 考慮進階搜尋功能
- 考慮搜尋結果高亮顯示
