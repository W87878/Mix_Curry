"""
Google Maps API 路由
提供地址驗證、地理編碼等 API 端點
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.services.google_maps import get_google_maps_service

logger = logging.getLogger(__name__)
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


class RouteRequest(BaseModel):
    """路線規劃請求"""
    origin: str
    destination: str
    waypoints: Optional[List[str]] = None
    mode: Optional[str] = "driving"
    optimize: Optional[bool] = True


class MultiDestinationRouteRequest(BaseModel):
    """多目的地路線規劃請求"""
    start_location: str
    destinations: List[str]
    mode: Optional[str] = "driving"


class ApplicationLocationsRequest(BaseModel):
    """案件地點列表請求（里長用）"""
    application_ids: List[str]  # 案件 ID 列表


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


@router.post("/route")
async def calculate_route(request: RouteRequest):
    """
    🗺️ 計算路線（含途經點）
    
    用於規劃訪問多個災損地點的路線
    
    Example:
    ```json
    {
        "origin": "台南市政府",
        "destination": "台南市中西區民權路一段100號",
        "waypoints": [
            "台南市安平區永華路二段6號",
            "台南市東區裕農路100號"
        ],
        "mode": "driving",
        "optimize": true
    }
    ```
    
    Response:
    ```json
    {
        "success": true,
        "routes": [
            {
                "summary": "國道1號",
                "distance": {"text": "15.2 公里", "value": 15200},
                "duration": {"text": "25 分鐘", "value": 1500},
                "legs": [...],
                "waypoint_order": [0, 1]
            }
        ],
        "count": 3
    }
    ```
    """
    try:
        maps_service = get_google_maps_service()
        result = await maps_service.calculate_route(
            origin=request.origin,
            destination=request.destination,
            waypoints=request.waypoints,
            mode=request.mode,
            optimize_waypoints=request.optimize
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimal-routes")
async def get_optimal_routes(request: MultiDestinationRouteRequest):
    """
    🎯 取得多目的地最佳路線（Top 3）
    
    **里長專用功能**：規劃訪問多個災損地點的最佳路線
    
    系統會自動優化訪問順序，並提供 Top 3 最佳路線方案
    
    Example:
    ```json
    {
        "start_location": "台南市東區裕農里辦公處",
        "destinations": [
            "台南市東區裕農路100號",
            "台南市東區裕農路200號",
            "台南市東區裕農路300號",
            "台南市東區裕農路400號"
        ],
        "mode": "driving"
    }
    ```
    
    Response:
    ```json
    {
        "success": true,
        "routes": [
            {
                "rank": 1,
                "total_distance": {"text": "8.5 公里", "value": 8500},
                "total_duration": {"text": "18 分鐘", "value": 1080},
                "waypoint_order": [0, 2, 1, 3],
                "ordered_addresses": [
                    "台南市東區裕農路100號",
                    "台南市東區裕農路300號",
                    "台南市東區裕農路200號",
                    "台南市東區裕農路400號"
                ],
                "legs": [...]
            },
            {
                "rank": 2,
                ...
            },
            {
                "rank": 3,
                ...
            }
        ],
        "count": 3,
        "message": "規劃完成，提供 3 條最佳路線"
    }
    ```
    """
    try:
        maps_service = get_google_maps_service()
        result = await maps_service.get_optimized_multi_destination_routes(
            start_location=request.start_location,
            destinations=request.destinations,
            mode=request.mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/applications-map-data")
async def get_applications_map_data(request: ApplicationLocationsRequest):
    """
    📍 取得案件地圖資料（里長用）
    
    取得所有選定案件的地理位置資訊，用於在地圖上標示
    
    Example:
    ```json
    {
        "application_ids": [
            "uuid-1",
            "uuid-2",
            "uuid-3"
        ]
    }
    ```
    
    Response:
    ```json
    {
        "success": true,
        "applications": [
            {
                "id": "uuid-1",
                "case_no": "CASE-20250101-001",
                "applicant_name": "王小明",
                "address": "台南市東區裕農路100號",
                "latitude": 22.9917,
                "longitude": 120.2009,
                "status": "pending",
                "requested_amount": 30000,
                "disaster_type": "flood"
            },
            ...
        ],
        "count": 3
    }
    ```
    """
    try:
        from app.models.database import db_service
        
        applications = []
        maps_service = get_google_maps_service()
        
        for app_id in request.application_ids:
            # 從資料庫取得案件資訊
            try:
                app_data = db_service.get_application_by_id(app_id)
                if not app_data:
                    logger.warning(f"Application not found: {app_id}")
                    continue
                
                # 優先使用 damage_location，其次使用 address
                address_to_geocode = app_data.get("damage_location") or app_data.get("address")
                
                if not address_to_geocode:
                    logger.warning(f"No address found for application {app_id}")
                    continue
                
                logger.info(f"Processing application {app_data.get('case_no')}: {address_to_geocode}")
                
                # 如果沒有經緯度，調用 Google Maps API 進行地理編碼
                latitude = app_data.get("latitude")
                longitude = app_data.get("longitude")
                formatted_address = app_data.get("formatted_address")
                
                if not latitude or not longitude:
                    logger.info(f"Geocoding address: {address_to_geocode}")
                    geocode_result = await maps_service.geocode_address(
                        address=address_to_geocode,
                        language="zh-TW"
                    )
                    
                    if geocode_result.get("success"):
                        latitude = geocode_result.get("latitude")
                        longitude = geocode_result.get("longitude")
                        formatted_address = geocode_result.get("formatted_address")
                        
                        logger.info(f"✓ Geocoded: {formatted_address} -> ({latitude}, {longitude})")
                        
                        # 可選：將經緯度存回資料庫（避免重複查詢）
                        try:
                            db_service.client.table("applications").update({
                                "latitude": latitude,
                                "longitude": longitude,
                                "formatted_address": formatted_address
                            }).eq("id", app_id).execute()
                        except Exception as update_error:
                            logger.warning(f"Failed to update geocode data: {update_error}")
                    else:
                        logger.error(f"✗ Geocoding failed for {address_to_geocode}")
                        continue
                
                applications.append({
                    "id": str(app_data.get("id")),
                    "case_no": app_data.get("case_no"),
                    "applicant_name": app_data.get("applicant_name"),
                    "address": app_data.get("address"),
                    "damage_location": app_data.get("damage_location"),
                    "formatted_address": formatted_address,
                    "latitude": latitude,
                    "longitude": longitude,
                    "status": app_data.get("status"),
                    "requested_amount": app_data.get("requested_amount"),
                    "disaster_type": app_data.get("disaster_type"),
                    "disaster_date": app_data.get("disaster_date")
                })
                
            except Exception as e:
                logger.error(f"Error processing application {app_id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return {
            "success": True,
            "applications": applications,
            "count": len(applications),
            "message": f"取得 {len(applications)} 個案件資料"
        }
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
