"""
Google Maps API 路由
提供地址驗證、地理編碼等 API 端點
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List

from app.services.google_maps import get_google_maps_service

router = APIRouter(prefix="/api/v1/maps", tags=["地圖服務"])


# ==========================================
# 請求/回應模型
# ==========================================

class GeocodeRequest(BaseModel):
    """地理編碼請求"""
    address: str
    language: Optional[str] = "zh-TW"


class ReverseGeocodeRequest(BaseModel):
    """反向地理編碼請求"""
    latitude: float
    longitude: float
    language: Optional[str] = "zh-TW"


class DistanceRequest(BaseModel):
    """距離計算請求"""
    origin: str
    destination: str
    mode: Optional[str] = "driving"  # driving, walking, bicycling, transit


class NearbyPlacesRequest(BaseModel):
    """附近地點搜尋請求"""
    latitude: float
    longitude: float
    place_type: Optional[str] = "convenience_store"
    radius: Optional[int] = 1000
    language: Optional[str] = "zh-TW"


# ==========================================
# API 端點
# ==========================================

@router.post("/geocode")
async def geocode_address(request: GeocodeRequest):
    """
    🗺️ 地理編碼：將地址轉換為經緯度
    
    Example:
    ```json
    {
        "address": "台南市中西區民權路一段100號"
    }
    ```
    
    Response:
    ```json
    {
        "success": true,
        "formatted_address": "700台南市中西區民權路一段100號",
        "latitude": 22.9917,
        "longitude": 120.2009,
        "place_id": "ChIJ...",
        "address_components": [...]
    }
    ```
    """
    try:
        maps_service = get_google_maps_service()
        result = await maps_service.geocode_address(
            address=request.address,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reverse-geocode")
async def reverse_geocode(request: ReverseGeocodeRequest):
    """
    🗺️ 反向地理編碼：將經緯度轉換為地址
    
    Example:
    ```json
    {
        "latitude": 22.9917,
        "longitude": 120.2009
    }
    ```
    """
    try:
        maps_service = get_google_maps_service()
        result = await maps_service.reverse_geocode(
            latitude=request.latitude,
            longitude=request.longitude,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-address")
async def validate_address(request: GeocodeRequest):
    """
    ✅ 驗證地址是否有效
    
    用於災害補助申請時驗證災損地址
    
    Example:
    ```json
    {
        "address": "台南市中西區民權路一段100號"
    }
    ```
    
    Response:
    ```json
    {
        "success": true,
        "valid": true,
        "is_precise": true,
        "formatted_address": "700台南市中西區民權路一段100號",
        "suggestion": "700台南市中西區民權路一段100號",
        "latitude": 22.9917,
        "longitude": 120.2009
    }
    ```
    """
    try:
        maps_service = get_google_maps_service()
        result = await maps_service.validate_address(request.address)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/distance")
async def calculate_distance(request: DistanceRequest):
    """
    📏 計算兩地之間的距離和時間
    
    用於計算災損地點與審核地點的距離
    
    Example:
    ```json
    {
        "origin": "台南市中西區民權路一段100號",
        "destination": "台南市政府",
        "mode": "driving"
    }
    ```
    
    Response:
    ```json
    {
        "success": true,
        "distance": {
            "text": "5.2 公里",
            "value": 5200
        },
        "duration": {
            "text": "15 分鐘",
            "value": 900
        }
    }
    ```
    """
    try:
        maps_service = get_google_maps_service()
        result = await maps_service.calculate_distance(
            origin=request.origin,
            destination=request.destination,
            mode=request.mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nearby-places")
async def find_nearby_places(request: NearbyPlacesRequest):
    """
    📍 尋找附近的地點
    
    用於尋找附近的便利商店（領取補助）、政府機關等
    
    Place Types:
    - convenience_store: 便利商店
    - government: 政府機關
    - hospital: 醫院
    - police: 警察局
    - fire_station: 消防局
    - bank: 銀行
    
    Example:
    ```json
    {
        "latitude": 22.9917,
        "longitude": 120.2009,
        "place_type": "convenience_store",
        "radius": 1000
    }
    ```
    
    Response:
    ```json
    {
        "success": true,
        "places": [
            {
                "name": "7-ELEVEN 台南民權門市",
                "address": "台南市中西區民權路一段...",
                "location": {"lat": 22.9917, "lng": 120.2009},
                "rating": 4.2,
                "is_open": true
            }
        ],
        "count": 5
    }
    ```
    """
    try:
        maps_service = get_google_maps_service()
        result = await maps_service.find_nearby_places(
            latitude=request.latitude,
            longitude=request.longitude,
            place_type=request.place_type,
            radius=request.radius,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/place-details/{place_id}")
async def get_place_details(
    place_id: str,
    language: Optional[str] = Query("zh-TW", description="語言")
):
    """
    🏢 取得地點詳細資訊
    
    Example:
    GET /api/v1/maps/place-details/ChIJ...?language=zh-TW
    
    Response:
    ```json
    {
        "success": true,
        "name": "台南市政府",
        "address": "70801台南市安平區永華路二段6號",
        "phone": "06-299-1111",
        "website": "https://www.tainan.gov.tw",
        "rating": 4.0,
        "opening_hours": {...}
    }
    ```
    """
    try:
        maps_service = get_google_maps_service()
        result = await maps_service.get_place_details(
            place_id=place_id,
            language=language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康檢查"""
    maps_service = get_google_maps_service()
    
    return {
        "status": "ok",
        "service": "google-maps",
        "api_key_configured": bool(maps_service.api_key)
    }


@router.get("/test-address-validation")
async def test_address_validation():
    """
    測試地址驗證功能（使用台南市政府地址）
    """
    try:
        maps_service = get_google_maps_service()
        
        test_addresses = [
            "台南市中西區民權路一段100號",
            "台南市政府",
            "台南市安平區永華路二段6號",
            "700台南市中西區",
            "無效地址123"
        ]
        
        results = []
        for address in test_addresses:
            result = await maps_service.validate_address(address)
            results.append({
                "address": address,
                "valid": result.get("valid", False),
                "formatted": result.get("formatted_address", ""),
                "is_precise": result.get("is_precise", False)
            })
        
        return {
            "success": True,
            "test_count": len(test_addresses),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
