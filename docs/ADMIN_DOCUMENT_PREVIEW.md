# 文件預覽與下載功能說明

## 功能概述

已在 admin.html（里長後台）中添加證明文件的查看和下載功能，讓里長可以：
1. 查看災民上傳的所有證明文件
2. 預覽文件（支援 PDF、圖片、DOCX 轉 PDF）
3. 下載文件到本地進行比對

## 功能特點

### 1. 支援的文件格式
- **PDF** - 直接預覽
- **圖片** (JPG, PNG) - 直接預覽
- **DOCX** - 自動轉換為 PDF 預覽（需要安裝 python-docx 和 reportlab）
- **其他格式** - 僅提供下載

### 2. 預覽功能
- DOCX 文件會自動轉換為 PDF 進行預覽
- 在新視窗中開啟，方便比對
- 預覽視窗提供下載原檔按鈕

### 3. 下載功能
- 一鍵下載原始文件
- 檔名自動設定
- 支援所有文件格式

## API 端點

### 1. 取得案件的所有文件
```http
GET /api/v1/documents/application/{application_id}
Authorization: Bearer {token}
```

**回應範例：**
```json
{
  "success": true,
  "message": "找到 3 個文件",
  "data": {
    "documents": [
      {
        "id": "uuid",
        "application_id": "uuid",
        "file_name": "戶籍謄本.pdf",
        "file_size": 1024000,
        "mime_type": "application/pdf",
        "document_type": "household_registration",
        "description": "全戶戶籍謄本",
        "uploaded_at": "2025-01-15T10:30:00Z",
        "signed_url": "https://..."
      }
    ],
    "total": 3
  }
}
```

### 2. 預覽文件（支援 DOCX 轉 PDF）
```http
GET /api/v1/documents/{document_id}/preview
Authorization: Bearer {token}
```

**說明：**
- 對於 DOCX 文件，自動轉換為 PDF
- 對於 PDF 和圖片，直接返回
- Content-Type 會根據文件類型自動設定
- Content-Disposition 設為 `inline`，在瀏覽器中直接顯示

### 3. 下載文件
```http
GET /api/v1/documents/{document_id}/download
Authorization: Bearer {token}
```

**說明：**
- 返回原始文件
- Content-Disposition 設為 `attachment`，觸發下載
- 檔名自動設定為原始檔名

## 前端使用方式

### 在 admin.html 中的使用

當里長點擊「審核」按鈕查看案件詳情時：

```javascript
// 自動載入案件的證明文件
await loadApplicationDocuments(applicationId);
```

文件列表會顯示在「證明文件」區塊，包含：
- 文件圖示（根據文件類型）
- 檔名
- 文件大小
- 文件類型（戶籍謄本、收入證明等）
- 上傳時間
- 預覽按鈕（DOCX、PDF、圖片）
- 下載按鈕

### 預覽功能

```javascript
// 開啟預覽視窗
previewDocument(documentId, fileName);
```

**特點：**
- 在新視窗中開啟
- 視窗大小：900x700
- 顯示檔名和下載按鈕
- 自動處理 DOCX 轉 PDF

### 下載功能

```javascript
// 下載文件到本地
downloadDocument(documentId, fileName);
```

**特點：**
- 使用 Blob API 下載
- 自動設定檔名
- 支援所有文件格式

## 後端實現

### DOCX 轉 PDF 功能

在 `app/routers/documents.py` 中添加了 `/preview` 端點：

```python
@router.get("/{document_id}/preview")
async def preview_document(document_id: str):
    """
    預覽文件
    - 對於 DOCX 文件，會自動轉換為 PDF 進行預覽
    - 對於 PDF 和圖片文件，直接返回原檔案
    """
```

**轉換流程：**
1. 檢查 MIME type 是否為 DOCX
2. 使用 `python-docx` 讀取 DOCX 內容
3. 使用 `reportlab` 生成 PDF
4. 返回轉換後的 PDF

**所需套件：**
```bash
pip install python-docx reportlab
```

或添加到 `requirements.txt`：
```
python-docx>=1.1.0
reportlab>=4.0.0
```

### 錯誤處理

如果轉換失敗或套件未安裝：
- 返回 501 錯誤（Not Implemented）
- 提示用戶直接下載檔案查看

## 測試方式

### 1. 使用測試頁面

訪問：`http://localhost:8000/static/test_document_preview.html`

可以測試：
- 取得案件文件列表
- 預覽文件
- 下載文件
- DOCX 轉 PDF

### 2. 完整流程測試

1. **災民端上傳文件**
   - 登入 `applicant.html`
   - 填寫申請表單
   - 在步驟 4 上傳證明文件（可上傳 DOCX、PDF、圖片）
   - 提交申請

2. **里長端查看文件**
   - 登入 `admin.html`
   - 在「待審核案件」中點擊「審核」
   - 在「證明文件」區塊查看文件列表
   - 點擊「預覽」查看文件
   - 點擊「下載」下載文件

3. **驗證 DOCX 轉 PDF**
   - 上傳一個 DOCX 文件
   - 在里長端點擊「預覽」
   - 應該看到轉換後的 PDF

## 文件類型說明

| 類型代碼 | 說明 |
|---------|------|
| `household_registration` | 戶籍謄本 |
| `income_proof` | 收入證明 |
| `property_proof` | 財產證明 |
| `damage_assessment` | 災損鑑定 |
| `supporting_document` | 一般證明文件 |
| `other` | 其他文件 |

## UI 設計

### 文件列表卡片
```
┌────────────────────────────────────────────┐
│ 📄 戶籍謄本.pdf                            │
│ 2.5 MB · 戶籍謄本 · 2025-01-15 10:30      │
│ 📝 全戶戶籍謄本                            │
│                      [👁️ 預覽] [⬇️ 下載]   │
└────────────────────────────────────────────┘
```

### 預覽視窗
```
┌─────────────────────────────────────────┐
│ 📄 戶籍謄本.pdf          [⬇️ 下載原檔]  │
├─────────────────────────────────────────┤
│                                         │
│        [PDF 或圖片預覽內容]             │
│                                         │
└─────────────────────────────────────────┘
```

## 注意事項

1. **安全性**
   - 所有 API 都需要 Bearer Token 認證
   - 只有審核者（里長）可以查看文件
   - 文件 URL 使用簽名 URL，有時效性

2. **效能考量**
   - DOCX 轉 PDF 需要處理時間
   - 大文件可能需要較長時間
   - 建議限制文件大小（目前為 20MB）

3. **瀏覽器相容性**
   - 預覽功能需要瀏覽器支援彈出視窗
   - PDF 預覽需要瀏覽器內建 PDF 閱讀器
   - 下載功能使用 Blob API

4. **DOCX 轉 PDF 限制**
   - 複雜格式可能無法完美轉換
   - 表格、圖片可能需要額外處理
   - 建議災民上傳 PDF 格式以獲得最佳預覽效果

## 未來改進

1. **支援更多格式**
   - Excel (XLS/XLSX) 轉 PDF
   - DOC (舊版 Word) 轉 PDF
   - 圖片合併為 PDF

2. **增強預覽功能**
   - 縮放、旋轉
   - 頁面導航
   - 全螢幕模式

3. **批次操作**
   - 批次下載所有文件
   - 打包下載為 ZIP

4. **文件管理**
   - 添加備註
   - 標記重點
   - 審核標記

## 相關檔案

- **前端**：`static/admin.html` - 里長後台
- **後端**：`app/routers/documents.py` - 文件 API
- **測試**：`static/test_document_preview.html` - 測試頁面
- **說明**：`docs/ADMIN_DOCUMENT_PREVIEW.md` - 本文檔
