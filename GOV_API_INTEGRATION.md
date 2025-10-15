# 🏛️ 政府數位憑證沙盒 API 整合說明

本文件說明如何整合政府數位憑證沙盒 API 到災民補助申請系統。

## 📋 政府 API 端點

### 發行端服務 API (Issuer)
- **沙盒環境**: https://issuer-sandbox.wallet.gov.tw/swaggerui/
- **用途**: 發行數位憑證、產生 QR Code、加入憑證到皮夾

### 驗證端服務 API (Verifier)
- **沙盒環境**: https://verifier-sandbox.wallet.gov.tw/swaggerui/
- **用途**: 驗證憑證、掃描 QR Code、建立驗證請求

## 🔄 整合流程

### 1. 發行憑證流程（核准補助時）

```
災民申請 → 審核員核准 → 系統呼叫發行端 API → 產生數位憑證 → 災民掃描 QR Code → 憑證加入皮夾
```

**API 呼叫順序**：
1. `POST /api/v1/certificates/` - 建立憑證（自動呼叫政府 API）
2. 政府發行端 API 回傳憑證 ID 和資料
3. 系統生成 QR Code 供災民掃描
4. 災民使用政府數位憑證 App 掃描 QR Code
5. 憑證自動加入災民的數位皮夾

### 2. 驗證憑證流程（發放補助時）

```
發放窗口產生驗證請求 → 顯示 QR Code → 災民掃描 QR Code → 出示憑證 → 系統驗證 → 發放補助
```

**API 呼叫順序**：
1. `POST /api/v1/certificates/gov/create-verification-request` - 建立驗證請求
2. 系統產生驗證用 QR Code
3. 災民掃描 QR Code 並出示憑證
4. `POST /api/v1/certificates/gov/verify-qr` - 驗證憑證
5. 驗證成功後發放補助

## 📡 API 端點說明

### 發行憑證

**端點**: `POST /api/v1/certificates/`

**參數**:
- `application_id`: 申請案件 ID
- `issued_by`: 核發人 ID
- `expires_days`: 憑證有效天數（預設 365）
- `use_gov_api`: 是否使用政府 API（預設 true）

**回應**:
```json
{
  "success": true,
  "message": "數位憑證建立成功（已整合政府沙盒 API）",
  "data": {
    "certificate_no": "CERT-20251014120000-abc12345",
    "qr_code_url": "https://xxx.supabase.co/storage/v1/...",
    "gov_credential": {
      "credentialId": "gov-cert-id-123",
      "type": ["VerifiableCredential", "DisasterReliefCredential"],
      ...
    },
    "using_gov_api": true
  }
}
```

### 驗證 QR Code（使用政府 API）

**端點**: `POST /api/v1/certificates/gov/verify-qr`

**參數**:
- `qr_data`: QR Code 掃描後的資料（JSON 字串）

**回應**:
```json
{
  "success": true,
  "message": "憑證驗證成功（政府 API）",
  "data": {
    "verified": true,
    "verification_method": "gov_api",
    "case_number": "CASE-2025-00001",
    "applicant_name": "王小明",
    "id_number": "A123456789",
    "approved_amount": 45000,
    "disaster_type": "颱風",
    "expiration_date": "2026-10-14T12:00:00Z"
  }
}
```

### 建立驗證請求

**端點**: `POST /api/v1/certificates/gov/create-verification-request`

**用途**: 發放窗口使用，產生供災民掃描的 QR Code

**回應**:
```json
{
  "success": true,
  "message": "驗證請求建立成功",
  "data": {
    "verification_request": {...},
    "qr_code": "data:image/png;base64,...",
    "request_id": "vr-123456",
    "usage": "請災民掃描此 QR Code 並出示憑證"
  }
}
```

## 🔐 憑證資料格式

### 災民補助數位憑證結構

根據 W3C Verifiable Credentials 標準：

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://wallet.gov.tw/credentials/disaster-relief/v1"
  ],
  "type": ["VerifiableCredential", "DisasterReliefCredential"],
  "issuer": {
    "id": "did:tw:gov:disaster-relief",
    "name": "災害應變中心"
  },
  "issuanceDate": "2025-10-14T12:00:00Z",
  "expirationDate": "2026-10-14T12:00:00Z",
  "credentialSubject": {
    "id": "did:tw:citizen:A123456789",
    "caseNumber": "CASE-2025-00001",
    "applicantName": "王小明",
    "idNumber": "A123456789",
    "disasterType": "颱風",
    "disasterDate": "2025-10-10",
    "approvedAmount": 45000,
    "currency": "TWD",
    "address": "台南市中西區民權路100號",
    "damageDescription": "一樓淹水約50公分",
    "subsidyType": "房屋補助"
  }
}
```

## 💻 程式碼範例

### Python 範例：發行憑證

```python
import httpx

async def issue_disaster_relief_credential(application_data):
    """發行災民補助憑證"""
    
    credential_data = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://wallet.gov.tw/credentials/disaster-relief/v1"
        ],
        "type": ["VerifiableCredential", "DisasterReliefCredential"],
        "issuer": {
            "id": "did:tw:gov:disaster-relief",
            "name": "災害應變中心"
        },
        "credentialSubject": {
            "id": f"did:tw:citizen:{application_data['id_number']}",
            "caseNumber": application_data['case_no'],
            "applicantName": application_data['applicant_name'],
            "approvedAmount": application_data['approved_amount'],
            ...
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://issuer-sandbox.wallet.gov.tw/api/v1/credentials/issue",
            json=credential_data
        )
        return response.json()
```

### Python 範例：驗證憑證

```python
async def verify_credential(qr_data):
    """驗證憑證"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://verifier-sandbox.wallet.gov.tw/api/v1/verify",
            json={"credential": qr_data}
        )
        result = response.json()
        return result.get('verified') == True
```

## 🎯 使用場景

### 場景 1：災民申請並取得憑證

1. **災民線上申請**
   ```bash
   POST /api/v1/applications/
   ```

2. **審核員審核並核准**
   ```bash
   POST /api/v1/reviews/approve/{application_id}
   ```

3. **系統自動發行數位憑證**
   ```bash
   POST /api/v1/certificates/?use_gov_api=true
   ```

4. **災民掃描 QR Code**
   - 系統產生的 QR Code URL
   - 災民使用政府數位憑證 App 掃描
   - 憑證自動加入皮夾

### 場景 2：發放窗口驗證並發放補助

1. **發放窗口建立驗證請求**
   ```bash
   POST /api/v1/certificates/gov/create-verification-request
   ```

2. **顯示 QR Code 供災民掃描**
   - 系統顯示驗證用 QR Code
   - 災民使用政府數位憑證 App 掃描

3. **災民出示憑證**
   - App 自動提示出示憑證
   - 災民確認後出示

4. **系統驗證憑證**
   ```bash
   POST /api/v1/certificates/gov/verify-qr
   ```

5. **驗證成功後發放補助**
   ```bash
   POST /api/v1/certificates/disburse
   ```

## 🧪 測試流程

### 1. 測試發行憑證

```bash
# 1. 建立測試使用者
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "full_name": "測試災民",
    "id_number": "A123456789",
    "phone": "0912345678",
    "role": "applicant"
  }'

# 2. 建立申請案件
curl -X POST "http://localhost:8000/api/v1/applications/" \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "{user_id}",
    "applicant_name": "測試災民",
    "disaster_type": "typhoon",
    "disaster_date": "2025-10-10",
    ...
  }'

# 3. 核准案件
curl -X POST "http://localhost:8000/api/v1/reviews/approve/{application_id}" \
  -d "reviewer_id={reviewer_id}&approved_amount=45000"

# 4. 發行憑證（使用政府 API）
curl -X POST "http://localhost:8000/api/v1/certificates/" \
  -d "application_id={application_id}&issued_by={reviewer_id}&use_gov_api=true"
```

### 2. 測試驗證憑證

```bash
# 1. 建立驗證請求
curl -X POST "http://localhost:8000/api/v1/certificates/gov/create-verification-request"

# 2. 驗證 QR Code
curl -X POST "http://localhost:8000/api/v1/certificates/gov/verify-qr" \
  -H "Content-Type: application/json" \
  -d '{"qr_data": "{掃描後的資料}"}'
```

## ⚠️ 注意事項

### 1. 沙盒環境限制

- ✅ 可用於開發和測試
- ✅ 可用於專題展示
- ⚠️ 不可用於正式環境
- ⚠️ 資料可能會定期清空

### 2. API 回應格式

政府 API 的回應格式可能與文件略有不同，請參考最新的 Swagger 文件：
- 發行端: https://issuer-sandbox.wallet.gov.tw/swaggerui/
- 驗證端: https://verifier-sandbox.wallet.gov.tw/swaggerui/

### 3. 錯誤處理

系統已實作 Fallback 機制：
- 如果政府 API 呼叫失敗，會自動切換為本地模式
- 本地模式仍會產生 QR Code，但不會與政府皮夾整合
- 這確保系統在政府 API 無法使用時仍能正常運作

### 4. 災害類型對應

| 系統代碼 | 中文名稱 |
|---------|---------|
| typhoon | 颱風 |
| flood | 水災 |
| earthquake | 地震 |
| fire | 火災 |
| other | 其他 |

## 📊 系統架構圖

```
┌─────────────┐
│   災民申請   │
└──────┬──────┘
       │
       ↓
┌──────────────┐
│  審核員審核   │
└──────┬───────┘
       │
       ↓
┌──────────────────────────┐
│ 系統發行憑證（呼叫政府API）│
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│ 政府發行端 API            │
│ issuer-sandbox.wallet... │
└──────┬───────────────────┘
       │
       ↓
┌──────────────┐
│  產生 QR Code │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ 災民掃描並    │
│ 加入憑證到皮夾│
└──────┬───────┘
       │
       ↓
┌──────────────────────────┐
│ 發放窗口驗證（呼叫政府API）│
└──────┬───────────────────┘
       │
       ↓
┌──────────────────────────┐
│ 政府驗證端 API            │
│ verifier-sandbox.wallet..│
└──────┬───────────────────┘
       │
       ↓
┌──────────────┐
│  發放補助     │
└──────────────┘
```

## 🔗 相關資源

- [政府數位憑證沙盒文件](https://wallet.gov.tw/)
- [W3C Verifiable Credentials](https://www.w3.org/TR/vc-data-model/)
- [專案 README](README.md)
- [Supabase 設定指南](SUPABASE_SETUP.md)

## 📞 技術支援

如遇到政府 API 相關問題，請聯絡：
- **數位憑證皮夾沙盒客服團隊**
- 發行端 API: https://issuer-sandbox.wallet.gov.tw/swaggerui/
- 驗證端 API: https://verifier-sandbox.wallet.gov.tw/swaggerui/

---

**更新日期**: 2025-10-14  
**版本**: 1.0.0

