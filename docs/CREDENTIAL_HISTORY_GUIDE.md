# 📝 憑證使用歷史記錄功能

## 概述

此功能用於記錄災害補助憑證的完整使用歷史，包括：
1. **憑證發行/領取**：當使用者掃描 QR Code 並將憑證儲存到手機時
2. **憑證驗證**：當使用者在 711 機台出示憑證進行驗證時

## 📊 資料表結構

### credential_history 表

| 欄位名稱 | 類型 | 說明 |
|---------|------|------|
| id | UUID | 主鍵 |
| application_id | UUID | 關聯申請案件 |
| user_id | UUID | 關聯使用者 |
| certificate_id | UUID | 關聯憑證（可選） |
| action_type | VARCHAR(50) | 動作類型：`credential_issued` 或 `credential_verified` |
| action_time | TIMESTAMP | 動作發生時間 |
| applicant_name | VARCHAR(100) | 申請人姓名 |
| id_number | VARCHAR(20) | 身分證字號 |
| disaster_type | VARCHAR(50) | 災害類型（flood, typhoon, earthquake 等） |
| disaster_address | TEXT | 受災地址 |
| approved_amount | DECIMAL(12,2) | 核准金額 |
| issuer_organization | VARCHAR(200) | 發行機構（領取時記錄） |
| verifier_organization | VARCHAR(200) | 驗證機構（驗證時記錄，如：7-11 中正門市） |
| status | VARCHAR(20) | 狀態：`issued` 或 `verified` |
| transaction_id | VARCHAR(255) | 政府 API 的 transaction ID |
| verification_location | JSONB | 驗證地點詳細資訊 |
| device_info | JSONB | 裝置資訊（可選） |
| notes | TEXT | 備註 |
| created_at | TIMESTAMP | 記錄建立時間 |

## 🔄 使用流程

### 1. 憑證發行/領取記錄

當使用者掃描 QR Code 並儲存憑證時，系統會自動記錄：

```javascript
// 前端偵測到憑證領取成功
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
```

**記錄內容：**
- action_type: `credential_issued`
- status: `issued`
- issuer_organization: `台南市政府災害救助中心`
- verifier_organization: `null`

### 2. 憑證驗證記錄

當使用者在 711 機台驗證憑證時，系統會自動記錄：

```python
# 後端在 VP 驗證成功後記錄
await record_credential_history(
    application_id=application_id,
    user_id=application.get("applicant_id"),
    action_type="credential_verified",
    status="verified",
    transaction_id=request.transaction_id,
    verifier_organization="7-11 便利商店",
    verification_location={
        "type": "711_store",
        "verified_at": datetime.now().isoformat()
    },
    notes=f"在 7-11 機台驗證成功，補助已發放。案件編號: {case_no}"
)
```

**記錄內容：**
- action_type: `credential_verified`
- status: `verified`
- issuer_organization: `null`
- verifier_organization: `7-11 便利商店`

## 📡 API 端點

### 1. 記錄憑證領取
```http
POST /api/v1/complete-flow/record-credential-claimed
Query Parameters:
  - application_id: 申請案件 ID
  - transaction_id: 政府 API transaction ID
```

### 2. 查詢申請案件的歷史記錄
```http
GET /api/v1/complete-flow/credential-history/{application_id}

Response:
{
  "success": true,
  "data": [
    {
      "id": "...",
      "action_type": "credential_issued",
      "action_time": "2024-01-15T10:30:00Z",
      "applicant_name": "王小明",
      "disaster_type": "flood",
      "issuer_organization": "台南市政府災害救助中心",
      "status": "issued"
    },
    {
      "id": "...",
      "action_type": "credential_verified",
      "action_time": "2024-01-16T14:20:00Z",
      "applicant_name": "王小明",
      "verifier_organization": "7-11 中正門市",
      "status": "verified"
    }
  ],
  "total": 2
}
```

### 3. 查詢使用者的所有歷史記錄
```http
GET /api/v1/complete-flow/credential-history-by-user/{user_id}
```

### 4. 查詢統計數據
```http
GET /api/v1/complete-flow/credential-history-stats
Query Parameters:
  - start_date: 開始日期 (YYYY-MM-DD)
  - end_date: 結束日期 (YYYY-MM-DD)
  - disaster_type: 災害類型篩選

Response:
{
  "success": true,
  "stats": {
    "total_records": 100,
    "issued_count": 60,
    "verified_count": 40,
    "disaster_stats": {
      "flood": {"issued": 30, "verified": 20},
      "typhoon": {"issued": 20, "verified": 15},
      "earthquake": {"issued": 10, "verified": 5}
    },
    "issuer_stats": {
      "台南市政府災害救助中心": 60
    },
    "verifier_stats": {
      "7-11 便利商店": 40
    }
  }
}
```

## 🗄️ 資料庫遷移

### 選項 1：使用完整 schema
```sql
-- 執行 unified_schema.sql（已包含 credential_history 表）
\i migration/unified_schema.sql
```

### 選項 2：單獨添加 credential_history 表
```sql
-- 如果已有其他表，只需添加 credential_history
\i migration/add_credential_history_table.sql
```

## 🔒 安全性

系統已啟用 Row Level Security (RLS)：

1. **使用者**：只能查看自己的歷史記錄
2. **管理員**：可以查看所有歷史記錄
3. **系統**：使用 service_role 可以插入記錄

## 📈 使用案例

### 1. 管理員查看特定申請的完整歷史
```javascript
const response = await fetch(`/api/v1/complete-flow/credential-history/${applicationId}`);
const history = await response.json();

// 顯示時間軸
history.data.forEach(record => {
  console.log(`${record.action_time}: ${record.action_type} - ${record.status}`);
  if (record.issuer_organization) {
    console.log(`  發行機構: ${record.issuer_organization}`);
  }
  if (record.verifier_organization) {
    console.log(`  驗證機構: ${record.verifier_organization}`);
  }
});
```

### 2. 統計報表
```javascript
// 查詢本月的憑證使用統計
const startDate = '2024-01-01';
const endDate = '2024-01-31';

const response = await fetch(
  `/api/v1/complete-flow/credential-history-stats?start_date=${startDate}&end_date=${endDate}`
);
const stats = await response.json();

console.log(`本月發行: ${stats.stats.issued_count} 張憑證`);
console.log(`本月驗證: ${stats.stats.verified_count} 張憑證`);
```

### 3. 使用者查看自己的憑證使用記錄
```javascript
const response = await fetch(`/api/v1/complete-flow/credential-history-by-user/${userId}`);
const history = await response.json();

// 顯示使用者的憑證使用歷史
history.data.forEach(record => {
  console.log(`${record.action_time}: ${record.disaster_type} - ${record.status}`);
});
```

## 🎯 欄位說明

### issuer_organization vs verifier_organization

這兩個欄位設計為互斥（其中一個為 NULL）：

- **憑證發行時**：
  - `issuer_organization` = "台南市政府災害救助中心"
  - `verifier_organization` = `null`

- **憑證驗證時**：
  - `issuer_organization` = `null`
  - `verifier_organization` = "7-11 中正門市"

這樣可以清楚區分憑證的發行和驗證記錄。

## 🔍 查詢範例

### 查詢所有水災補助的憑證發行記錄
```sql
SELECT 
    applicant_name,
    disaster_address,
    approved_amount,
    issuer_organization,
    action_time
FROM credential_history
WHERE disaster_type = 'flood'
    AND action_type = 'credential_issued'
ORDER BY action_time DESC;
```

### 查詢特定 711 門市的驗證記錄
```sql
SELECT 
    applicant_name,
    id_number,
    disaster_type,
    approved_amount,
    action_time
FROM credential_history
WHERE verifier_organization LIKE '%7-11%'
    AND status = 'verified'
ORDER BY action_time DESC;
```

### 統計每日憑證發行數量
```sql
SELECT 
    DATE(action_time) as date,
    COUNT(*) as issued_count
FROM credential_history
WHERE action_type = 'credential_issued'
GROUP BY DATE(action_time)
ORDER BY date DESC;
```

## 📝 注意事項

1. **自動記錄**：系統會在憑證發行和驗證時自動記錄，無需手動操作
2. **資料快照**：history 記錄保存了申請人資料的快照，即使原申請資料被修改，歷史記錄也不會改變
3. **效能優化**：已建立必要的索引，確保查詢效能
4. **隱私保護**：啟用 RLS，確保使用者隱私

## 🚀 未來擴展

可以考慮添加的功能：

1. **地理位置記錄**：記錄驗證時的 GPS 座標
2. **裝置資訊**：記錄使用者的裝置類型（iOS/Android）
3. **驗證失敗記錄**：記錄驗證失敗的原因
4. **匯出報表**：支援 Excel/PDF 格式匯出
5. **即時通知**：當有新的憑證驗證時，通知相關人員
