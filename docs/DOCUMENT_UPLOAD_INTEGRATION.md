# 文件上傳功能整合指南

## 概述
此文檔說明如何在災民端和里長後台中整合文件上傳、預覽和下載功能。

## 已完成的工作

### 1. 後端 API (`app/routers/documents.py`)
✅ 已創建完整的文件管理 API：
- `POST /api/v1/documents/upload` - 上傳文件
- `GET /api/v1/documents/application/{application_id}` - 獲取案件的所有文件
- `GET /api/v1/documents/{document_id}` - 獲取單個文件資訊
- `GET /api/v1/documents/{document_id}/download` - 下載文件
- `DELETE /api/v1/documents/{document_id}` - 刪除文件

### 2. 資料庫表格 (`migration/create_application_documents_table.sql`)
✅ 已創建 `application_documents` 表格：
```sql
CREATE TABLE application_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    document_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100),
    description TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 3. Storage Service 擴展 (`app/services/storage.py`)
✅ 添加了文件上傳方法：
- `upload_document()` - 上傳文件到 Supabase Storage
- `get_document_url()` - 獲取文件的公開 URL
- `delete_document()` - 刪除文件

### 4. 災民端表單 (`static/applicant.html`)
✅ 已添加：
- 步驟4：上傳證明文件
- 文件選擇和預覽功能
- 自動上傳文件到伺服器

## 需要手動完成的工作

### 步驟 1: 創建資料庫表格
執行以下 SQL 腳本：
```bash
# 連接到 Supabase 並執行
cat migration/create_application_documents_table.sql | psql $DATABASE_URL
```

或在 Supabase Dashboard 的 SQL Editor 中執行 `migration/create_application_documents_table.sql`

### 步驟 2: 創建 Storage Bucket
在 Supabase Dashboard 中：
1. 前往 Storage
2. 創建新的 bucket：`application-documents`
3. 設定為 Public（或根據需求設為 Private）
4. 設定存取政策

### 步驟 3: 在 admin.html 中添加文件查看功能

在 `static/admin.html` 的案件詳情部分添加以下 JavaScript 函數：

```javascript
// 載入案件的證明文件
async function loadApplicationDocuments(applicationId) {
    try {
        const response = await fetch(`${API_BASE}/documents/application/${applicationId}`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        
        if (!response.ok) {
            throw new Error('無法載入文件列表');
        }
        
        const result = await response.json();
        const documents = result.data?.documents || [];
        
        displayDocuments(documents);
    } catch (error) {
        console.error('載入文件失敗:', error);
        document.getElementById('documentsInfo').innerHTML = `
            <p style="color: #ef4444; font-size: 14px;">載入文件失敗: ${error.message}</p>
        `;
    }
}

// 顯示文件列表
function displayDocuments(documents) {
    const container = document.getElementById('documentsInfo');
    
    if (documents.length === 0) {
        container.innerHTML = '<p style="color: #999; font-size: 14px;">此案件無上傳文件</p>';
        return;
    }
    
    const html = documents.map(doc => {
        const icon = getFileIcon(doc.file_name);
        const sizeInMB = (doc.file_size / (1024 * 1024)).toFixed(2);
        const uploadDate = new Date(doc.uploaded_at).toLocaleDateString('zh-TW');
        
        return `
            <div style="display: flex; align-items: center; padding: 12px; background: #f8f9fa; border-radius: 8px; margin-bottom: 10px;">
                <div style="font-size: 32px; margin-right: 12px;">${icon}</div>
                <div style="flex: 1;">
                    <div style="font-weight: 500; margin-bottom: 4px;">${doc.file_name}</div>
                    <div style="font-size: 12px; color: #666;">
                        ${sizeInMB} MB • ${uploadDate}
                        ${doc.description ? `<br>${doc.description}` : ''}
                    </div>
                </div>
                <button 
                    onclick="previewDocument('${doc.id}', '${doc.file_name}')" 
                    class="btn btn-secondary" 
                    style="margin-right: 8px; padding: 8px 16px;">
                    👁️ 預覽
                </button>
                <button 
                    onclick="downloadDocument('${doc.id}', '${doc.file_name}')" 
                    class="btn btn-primary" 
                    style="padding: 8px 16px;">
                    ⬇️ 下載
                </button>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// 獲取文件圖示
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📄',
        'doc': '📝',
        'docx': '📝',
        'xls': '📊',
        'xlsx': '📊',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️'
    };
    return icons[ext] || '📎';
}

// 預覽文件
async function previewDocument(documentId, fileName) {
    try {
        const response = await fetch(`${API_BASE}/documents/${documentId}/download`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        
        if (!response.ok) {
            throw new Error('無法載入文件');
        }
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // 判斷文件類型
        const ext = fileName.split('.').pop().toLowerCase();
        
        if (['jpg', 'jpeg', 'png', 'gif'].includes(ext)) {
            // 圖片：在新視窗中顯示
            const win = window.open('', '_blank');
            win.document.write(`
                <html>
                <head><title>${fileName}</title></head>
                <body style="margin:0;display:flex;justify-content:center;align-items:center;background:#000;">
                    <img src="${url}" style="max-width:100%;max-height:100vh;" />
                </body>
                </html>
            `);
        } else if (ext === 'pdf') {
            // PDF：在新分頁中顯示
            window.open(url, '_blank');
        } else {
            // 其他檔案：直接下載
            downloadDocument(documentId, fileName);
        }
    } catch (error) {
        console.error('預覽文件失敗:', error);
        alert(`預覽失敗: ${error.message}`);
    }
}

// 下載文件
async function downloadDocument(documentId, fileName) {
    try {
        const response = await fetch(`${API_BASE}/documents/${documentId}/download`, {
            headers: { 'Authorization': `Bearer ${accessToken}` }
        });
        
        if (!response.ok) {
            throw new Error('無法下載文件');
        }
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        
        // 創建隱藏的下載連結
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // 清理 URL
        setTimeout(() => URL.revokeObjectURL(url), 100);
        
        console.log(`✓ 文件下載成功: ${fileName}`);
    } catch (error) {
        console.error('下載文件失敗:', error);
        alert(`下載失敗: ${error.message}`);
    }
}
```

### 步驟 4: 在案件詳情頁面中調用文件載入函數

找到顯示案件詳情的函數（通常在點擊案件時觸發），添加：

```javascript
// 在顯示案件詳情時載入文件
async function showApplicationDetail(applicationId) {
    // ...existing code to show application details...
    
    // 載入證明文件
    await loadApplicationDocuments(applicationId);
}
```

## 使用流程

### 災民端
1. 災民填寫申請表單
2. 在步驟4選擇要上傳的證明文件（最多5個，每個最大10MB）
3. 系統顯示已選擇的文件預覽
4. 提交申請後，文件自動上傳到伺服器

### 里長後台
1. 里長點擊查看案件詳情
2. 在「證明文件」區域看到所有上傳的文件
3. 可以點擊「預覽」查看文件內容（圖片和PDF直接顯示）
4. 可以點擊「下載」將文件下載到本地

## 支援的文件格式
- **文檔**: PDF, DOC, DOCX
- **圖片**: JPG, JPEG, PNG, GIF
- **試算表**: XLS, XLSX（可擴展）

## 安全性考慮
1. 文件大小限制：10MB
2. 文件數量限制：每個案件最多5個文件
3. 文件類型驗證：只允許特定格式
4. 存取控制：需要 JWT Token 驗證
5. 文件與案件關聯：只能查看自己相關案件的文件

## 測試步驟

### 1. 測試文件上傳
```bash
curl -X POST http://localhost:8080/api/v1/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "application_id=APPLICATION_UUID" \
  -F "document_type=supporting_document" \
  -F "description=測試文件"
```

### 2. 測試文件列表
```bash
curl http://localhost:8080/api/v1/documents/application/APPLICATION_UUID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. 測試文件下載
```bash
curl http://localhost:8080/api/v1/documents/DOCUMENT_UUID/download \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o downloaded_file.pdf
```

## 故障排除

### 問題：文件上傳失敗
- 檢查 Storage bucket 是否已創建
- 檢查文件大小是否超過限制
- 檢查文件格式是否支援

### 問題：無法預覽文件
- 確認瀏覽器支援該文件格式
- 檢查文件是否已正確上傳到 Storage
- 檢查 CORS 設定

### 問題：下載文件時出錯
- 檢查文件路徑是否正確
- 確認 Storage bucket 的存取權限
- 檢查網路連線

## 未來改進建議

1. **批次下載**：允許下載所有文件為 ZIP
2. **文件預覽優化**：支援更多文件格式的線上預覽
3. **文件版本控制**：記錄文件的修改歷史
4. **OCR 識別**：自動識別文件中的文字資訊
5. **文件分類**：按類型自動分類文件
6. **縮圖生成**：為圖片文件生成縮圖
7. **病毒掃描**：上傳前進行安全檢查

---
**最後更新**: 2025-10-28
**作者**: AI Assistant
