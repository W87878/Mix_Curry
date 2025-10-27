# 🗺️ Google Maps API 整合文件

## 📋 概述

這個模組整合了 Google Maps API，提供地址驗證、地理編碼、距離計算等功能，用於災害補助系統的地址驗證和災損地點定位。

## 🚀 快速開始

### 1. 設定 API Key

在 `.env` 檔案中加入：

```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### 2. 啟用 Google Cloud APIs

在 [Google Cloud Console](https://console.cloud.google.com/) 啟用以下 API：

- ✅ **Geocoding API** - 地理編碼
- ✅ **Places API** - 地點搜尋
- ✅ **Distance Matrix API** - 距離計算

### 3. 執行測試

```bash
python test_google_maps.py
```

## 📚 功能說明

### 1️⃣ 地理編碼 (Geocode)

**將地址轉換為經緯度**

```python
from app.services.google_maps import get_google_maps_service

maps_service = get_google_maps_service()
result = await maps_service.geocode_address("台南市中西區民權路一段100號")

# 回應
{
    "success": True,
    "formatted_address": "700台南市中西區民權路一段100號",
    "latitude": 22.9917,
    "longitude": 120.2009,
    "place_id": "ChIJ...",
    "address_components": [...]
}
```

**API 端點：**
```http
POST /api/v1/maps/geocode
Content-Type: application/json

{
    "address": "台南市中西區民權路一段100號"
}
```

---

### 2️⃣ 反向地理編碼 (Reverse Geocode)

**將經緯度轉換為地址**

```python
result = await maps_service.reverse_geocode(
    latitude=22.9917,
    longitude=120.2009
)

# 回應
{
    "success": True,
    "formatted_address": "700台南市中西區民權路一段100號",
    "address_components": [...]
}
```

**API 端點：**
```http
POST /api/v1/maps/reverse-geocode
Content-Type: application/json

{
    "latitude": 22.9917,
    "longitude": 120.2009
}
```

---

### 3️⃣ 地址驗證 (Address Validation)

**驗證地址是否有效且精確**

```python
result = await maps_service.validate_address("台南市中西區民權路一段100號")

# 回應
{
    "success": True,
    "valid": True,
    "is_precise": True,  # 是否精確到門牌號碼
    "formatted_address": "700台南市中西區民權路一段100號",
    "suggestion": "700台南市中西區民權路一段100號",
    "latitude": 22.9917,
    "longitude": 120.2009
}
```

**API 端點：**
```http
POST /api/v1/maps/validate-address
Content-Type: application/json

{
    "address": "台南市中西區民權路一段100號"
}
```

**使用場景：**
- ✅ 災民填寫申請表單時驗證災損地址
- ✅ 自動校正地址格式
- ✅ 確保地址可以定位

---

### 4️⃣ 距離計算 (Distance Matrix)

**計算兩地之間的距離和時間**

```python
result = await maps_service.calculate_distance(
    origin="台南市中西區民權路一段100號",
    destination="台南市政府",
    mode="driving"  # driving, walking, bicycling, transit
)

# 回應
{
    "success": True,
    "distance": {
        "text": "5.2 公里",
        "value": 5200  # 公尺
    },
    "duration": {
        "text": "15 分鐘",
        "value": 900  # 秒
    }
}
```

**API 端點：**
```http
POST /api/v1/maps/distance
Content-Type: application/json

{
    "origin": "台南市中西區民權路一段100號",
    "destination": "台南市政府",
    "mode": "driving"
}
```

**使用場景：**
- ✅ 計算災損地點與審核機關的距離
- ✅ 安排現場勘查路線
- ✅ 評估是否需要現場勘查

---

### 5️⃣ 附近地點搜尋 (Nearby Search)

**尋找附近的便利商店、政府機關等**

```python
result = await maps_service.find_nearby_places(
    latitude=22.9917,
    longitude=120.2009,
    place_type="convenience_store",  # 便利商店
    radius=1000  # 1公里內
)

# 回應
{
    "success": True,
    "places": [
        {
            "name": "7-ELEVEN 台南民權門市",
            "address": "台南市中西區民權路一段...",
            "location": {"lat": 22.9917, "lng": 120.2009},
            "rating": 4.2,
            "is_open": True
        }
    ],
    "count": 5
}
```

**API 端點：**
```http
POST /api/v1/maps/nearby-places
Content-Type: application/json

{
    "latitude": 22.9917,
    "longitude": 120.2009,
    "place_type": "convenience_store",
    "radius": 1000
}
```

**支援的地點類型：**
- `convenience_store` - 便利商店（7-11、全家等）
- `government` - 政府機關
- `hospital` - 醫院
- `police` - 警察局
- `fire_station` - 消防局
- `bank` - 銀行
- `post_office` - 郵局

**使用場景：**
- ✅ 災民查詢附近可領取補助的便利商店
- ✅ 顯示最近的政府機關位置
- ✅ 提供災民就近服務的地點資訊

---

### 6️⃣ 地點詳細資訊 (Place Details)

**取得特定地點的詳細資訊**

```python
result = await maps_service.get_place_details("ChIJ...")

# 回應
{
    "success": True,
    "name": "台南市政府",
    "address": "70801台南市安平區永華路二段6號",
    "phone": "06-299-1111",
    "website": "https://www.tainan.gov.tw",
    "rating": 4.0,
    "opening_hours": {...}
}
```

**API 端點：**
```http
GET /api/v1/maps/place-details/ChIJ...?language=zh-TW
```

---

### 7️⃣ 地址組成解析 (Parse Address Components)

**將地址拆解為城市、區域、街道等組成**

```python
geocode_result = await maps_service.geocode_address("台南市中西區民權路一段100號")
parsed = maps_service.parse_address_components(geocode_result["address_components"])

# 結果
{
    "country": "台灣",
    "city": "台南市",
    "district": "中西區",
    "street": "民權路一段",
    "postal_code": "700"
}
```

---

## 🎯 災害補助系統應用場景

### 場景 1：災民填寫申請表單

```javascript
// 前端 JavaScript
async function validateAddress() {
    const address = document.getElementById('damage_address').value;
    
    const response = await fetch('/api/v1/maps/validate-address', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({address: address})
    });
    
    const result = await response.json();
    
    if (result.valid) {
        if (result.is_precise) {
            alert('✅ 地址有效！');
        } else {
            alert('⚠️ 地址不夠精確，建議使用：' + result.formatted_address);
        }
    } else {
        alert('❌ 地址無效，請重新輸入');
    }
}
```

### 場景 2：審核員查看申請案件位置

```python
# 後端 Python
async def get_application_location(application_id: str):
    # 取得申請資料
    app = db.get_application(application_id)
    
    # 地址轉經緯度
    maps_service = get_google_maps_service()
    result = await maps_service.geocode_address(app.damage_location)
    
    if result["success"]:
        # 計算與區公所的距離
        distance_result = await maps_service.calculate_distance(
            origin="台南市中西區區公所",
            destination=app.damage_location
        )
        
        return {
            "location": {
                "lat": result["latitude"],
                "lng": result["longitude"]
            },
            "distance_from_office": distance_result["distance"]["text"]
        }
```

### 場景 3：災民查詢附近領取點

```python
# 災民查詢附近的 7-11
@router.get("/api/v1/applications/{application_id}/nearby-stores")
async def get_nearby_stores(application_id: str):
    app = db.get_application(application_id)
    
    # 先將地址轉成經緯度
    maps_service = get_google_maps_service()
    geocode_result = await maps_service.geocode_address(app.address)
    
    if not geocode_result["success"]:
        raise HTTPException(400, "無法定位地址")
    
    # 搜尋附近便利商店
    stores = await maps_service.find_nearby_places(
        latitude=geocode_result["latitude"],
        longitude=geocode_result["longitude"],
        place_type="convenience_store",
        radius=2000  # 2公里內
    )
    
    return {
        "stores": stores["places"][:5],  # 只回傳最近5間
        "applicant_location": {
            "lat": geocode_result["latitude"],
            "lng": geocode_result["longitude"]
        }
    }
```

---

## 🔧 進階設定

### API Key 安全設定

在 Google Cloud Console 設定 API 金鑰限制：

1. **應用程式限制**
   - HTTP 引用網址（網站）
   - 加入你的網域：`https://yourdomain.com/*`

2. **API 限制**
   - 限制金鑰只能存取：
     - Geocoding API
     - Places API
     - Distance Matrix API

3. **配額管理**
   - 設定每日請求限制
   - 啟用帳單提醒

### 快取策略

為了節省 API 配額和提升效能，建議快取常用查詢：

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
async def cached_geocode(address: str):
    maps_service = get_google_maps_service()
    return await maps_service.geocode_address(address)
```

### 錯誤處理

```python
try:
    result = await maps_service.geocode_address(address)
    if not result["success"]:
        logger.warning(f"地址解析失敗: {result['message']}")
        # 使用備用方案或提示使用者
except Exception as e:
    logger.error(f"Google Maps API 錯誤: {e}")
    # 系統降級處理
```

---

## 📊 費用說明

Google Maps API 收費標準（2025年）：

| API | 免費額度 | 超出收費 |
|-----|---------|---------|
| Geocoding | 40,000 次/月 | $5 / 1,000 次 |
| Places | 根據欄位計費 | $17 - $32 / 1,000 次 |
| Distance Matrix | 40,000 元素/月 | $5 / 1,000 元素 |

**建議：**
- 使用快取減少重複查詢
- 監控 API 使用量
- 設定每月預算上限

---

## 🧪 測試

### 執行單元測試

```bash
# 測試所有功能
python test_google_maps.py

# 測試 API 端點
curl -X POST http://localhost:8080/api/v1/maps/validate-address \
  -H "Content-Type: application/json" \
  -d '{"address": "台南市中西區民權路一段100號"}'
```

### 健康檢查

```bash
curl http://localhost:8080/api/v1/maps/health
```

回應：
```json
{
    "status": "ok",
    "service": "google-maps",
    "api_key_configured": true
}
```

---

## 📝 待辦事項

- [ ] 加入地址自動完成功能（Autocomplete）
- [ ] 整合地圖顯示（嵌入 Google Maps）
- [ ] 批次地理編碼功能
- [ ] 地址正規化（Standardization）
- [ ] 路線規劃（Directions）

---

## 🤝 支援

如有問題請聯繫開發團隊或查閱：
- [Google Maps API 文件](https://developers.google.com/maps/documentation)
- [Google Cloud Console](https://console.cloud.google.com/)

---

## 📄 授權

此模組為災害補助系統的一部分，僅供內部使用。
