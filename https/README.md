# 📝 HTTP API 測試指南

本資料夾包含完整的 HTTP API 測試文件。

## 📂 檔案說明

- `test.http` - 完整的 API 測試請求集合
- `test_images/` - 測試用圖片資料夾
- `README.md` - 本說明文件

## 🚀 快速開始

### 方法 1：使用 VS Code REST Client（推薦）

1. **安裝擴充套件**
   - 在 VS Code 中搜尋並安裝 "REST Client" 擴充套件
   - 作者：Huachao Mao

2. **開啟測試檔案**
   ```bash
   code https/test.http
   ```

3. **執行測試**
   - 點擊每個請求上方的 `Send Request` 連結
   - 或使用快捷鍵 `Ctrl+Alt+R` (Windows/Linux) 或 `Cmd+Alt+R` (Mac)

4. **查看回應**
   - 回應會在右側新視窗中顯示
   - 可以複製回應中的 ID 用於後續請求

### 方法 2：使用 IntelliJ IDEA / WebStorm

1. **開啟測試檔案**
   - IntelliJ IDEA 和 WebStorm 內建支援 `.http` 檔案

2. **執行測試**
   - 點擊行號旁的綠色播放按鈕
   - 或按 `Ctrl+Enter` (Windows/Linux) 或 `Cmd+Return` (Mac)

### 方法 3：使用 Postman

1. **匯入集合**
   - 開啟 Postman
   - 點擊 Import
   - 選擇 `test.http` 檔案

2. **執行測試**
   - Postman 會自動轉換成集合
   - 依序執行每個請求

### 方法 4：使用 curl

參考 `test.http` 中的範例，使用 curl 命令：

```bash
# 健康檢查
curl http://localhost:8000/health

# 建立使用者
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "full_name": "測試用戶",
    "id_number": "A123456789",
    "phone": "0912345678",
    "role": "applicant"
  }'
```

## 📋 完整測試流程

### 流程 1：災民申請補助（8-12 分鐘）

```
1. 建立災民帳號
   → POST /api/v1/users/
   
2. 建立申請案件
   → POST /api/v1/applications/
   ✅ 記下 application_id 和 case_no
   
3. 上傳災損照片（至少 2 張）
   → POST /api/v1/photos/upload (災前照片)
   → POST /api/v1/photos/upload (災後照片)
   
4. 查看申請狀態
   → GET /api/v1/applications/{application_id}
```

### 流程 2：審核員審核（15-20 分鐘）

```
1. 建立審核員帳號
   → POST /api/v1/users/ (role: reviewer)
   
2. 查看待審核案件
   → GET /api/v1/applications/status/pending
   
3. 開始審核
   → POST /api/v1/reviews/
   
4. 上傳現場勘查照片
   → POST /api/v1/photos/inspection/upload
   
5. 核准案件
   → POST /api/v1/reviews/approve/{application_id}
   ✅ 設定 approved_amount
   
6. 發行數位憑證
   → POST /api/v1/certificates/
   ✅ 記下 certificate_no
```

### 流程 3：發放補助（5 分鐘）

```
1. 建立驗證請求（產生 QR Code）
   → POST /api/v1/certificates/gov/create-verification-request
   
2. 驗證憑證
   → POST /api/v1/certificates/verify
   
3. 掃描 QR Code
   → POST /api/v1/certificates/scan/{certificate_no}
   
4. 發放補助
   → POST /api/v1/certificates/disburse
   
5. 確認完成
   → GET /api/v1/applications/{application_id}
   ✅ status 應為 "completed"
```

## 🖼️ 圖片上傳測試

### 準備測試圖片

在 `test_images/` 資料夾中放入測試圖片：

```bash
https/test_images/
├── damage_before.jpg  # 災前照片
├── damage_after.jpg   # 災後照片
└── inspection.jpg     # 現場勘查照片
```

### 使用 curl 上傳圖片

```bash
# 上傳災前照片
curl -X POST "http://localhost:8000/api/v1/photos/upload" \
  -F "application_id=你的案件ID" \
  -F "photo_type=before_damage" \
  -F "description=一樓客廳淹水情形" \
  -F "uploaded_by=申請人ID" \
  -F "file=@./https/test_images/damage_before.jpg"

# 上傳災後照片
curl -X POST "http://localhost:8000/api/v1/photos/upload" \
  -F "application_id=你的案件ID" \
  -F "photo_type=after_damage" \
  -F "description=災後清理情形" \
  -F "uploaded_by=申請人ID" \
  -F "file=@./https/test_images/damage_after.jpg"

# 上傳現場勘查照片（審核員）
curl -X POST "http://localhost:8000/api/v1/photos/inspection/upload" \
  -F "application_id=你的案件ID" \
  -F "reviewer_id=審核員ID" \
  -F "description=現場勘查確認災損情形" \
  -F "file=@./https/test_images/inspection.jpg"
```

### 使用 Postman 上傳圖片

1. 選擇請求方法：`POST`
2. URL：`http://localhost:8000/api/v1/photos/upload`
3. Body 選擇：`form-data`
4. 添加欄位：
   - `application_id` (text): 你的案件 ID
   - `photo_type` (text): before_damage
   - `description` (text): 照片描述
   - `uploaded_by` (text): 上傳者 ID
   - `file` (file): 選擇圖片檔案
5. 點擊 Send

## 📊 測試資料範例

### 災害類型
- `typhoon` - 颱風
- `flood` - 水災
- `earthquake` - 地震
- `fire` - 火災

### 補助類型
- `housing` - 房屋補助
- `equipment` - 設備補助
- `living` - 生活補助
- `business` - 營業補助

### 案件狀態
- `pending` - 待審核
- `under_review` - 審核中
- `site_inspection` - 現場勘查中
- `approved` - 已核准
- `rejected` - 已駁回
- `completed` - 已完成

### 照片類型
- `before_damage` - 災前照片
- `after_damage` - 災後照片
- `site_inspection` - 現場勘查照片

## 🔧 變數替換

在使用 `test.http` 時，需要替換以下變數：

- `{application_id}` - 申請案件 ID
- `{user_id}` - 使用者 ID
- `{applicant_id}` - 申請人 ID
- `{reviewer_id}` - 審核員 ID
- `{case_no}` - 案件編號（例：CASE-2025-00001）
- `{certificate_no}` - 憑證編號（例：CERT-20251014120000-abc12345）
- `{photo_id}` - 照片 ID

💡 **提示**：從每個 API 回應的 `data.id` 欄位複製 ID。

## 🧪 測試檢查清單

### 基礎功能測試
- [ ] 健康檢查 API
- [ ] 建立災民使用者
- [ ] 建立審核員使用者
- [ ] 查詢使用者資料

### 申請流程測試
- [ ] 建立申請案件
- [ ] 查詢案件（by ID）
- [ ] 查詢案件（by 案件編號）
- [ ] 查詢案件（by 狀態）
- [ ] 更新案件資料

### 照片功能測試
- [ ] 上傳災前照片
- [ ] 上傳災後照片
- [ ] 上傳現場勘查照片
- [ ] 查詢案件所有照片
- [ ] 刪除照片

### 審核流程測試
- [ ] 建立審核記錄
- [ ] 查詢審核記錄
- [ ] 核准案件
- [ ] 駁回案件

### 憑證功能測試
- [ ] 建立憑證（政府 API 模式）
- [ ] 建立憑證（本地模式）
- [ ] 查詢憑證
- [ ] 驗證憑證
- [ ] 掃描 QR Code
- [ ] 發放補助

### 統計功能測試
- [ ] 查看系統統計

## ⚠️ 常見問題

### Q1: 無法連接到 API
**A**: 確認 FastAPI 服務正在運行
```bash
python main.py
```

### Q2: 上傳圖片失敗
**A**: 
1. 確認圖片檔案存在
2. 確認圖片大小 < 10MB
3. 確認格式為 jpg/jpeg/png

### Q3: 404 Not Found
**A**: 
1. 檢查 URL 是否正確
2. 確認 ID 是否存在
3. 檢查案件狀態是否符合操作要求

### Q4: 500 Internal Server Error
**A**: 
1. 查看服務端日誌
2. 確認 Supabase 連線正常
3. 檢查環境變數設定

## 📚 相關文件

- [README.md](../README.md) - 專案總覽
- [GOV_API_INTEGRATION.md](../GOV_API_INTEGRATION.md) - 政府 API 整合說明
- [command.py](../command.py) - 資料庫管理工具

## 🎯 進階測試

### 使用管理工具配合測試

```bash
# 1. 清空資料庫
python command.py clear --force

# 2. 建立測試資料
python command.py create-test-data

# 3. 使用 test.http 進行測試

# 4. 查看統計
python command.py stats
```

### 自動化測試腳本

也可以使用 Python 測試腳本：
```bash
python test_api.py
```

---

**最後更新**: 2025-10-14  
**作者**: Mix_Curry Team

