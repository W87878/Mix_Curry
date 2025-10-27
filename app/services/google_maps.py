"""
Google Maps API 服務
提供地址驗證、地理編碼、距離計算等功能
用於災害補助系統的地址驗證和災損地點定位
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
import httpx

load_dotenv()

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Google Maps API 服務類別"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 Google Maps 服務
        
        Args:
            api_key: Google Maps API Key，若未提供則從環境變數讀取
        """
        self.api_key = api_key or os.environ.get("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            logger.warning("未設定 GOOGLE_MAPS_API_KEY，某些功能將無法使用")
        
        self.base_url = "https://maps.googleapis.com/maps/api"
        self.timeout = 10.0
    
    async def geocode_address(self, address: str, language: str = "zh-TW") -> Dict:
        """
        地理編碼：將地址轉換為經緯度
        
        Args:
            address: 地址字串，例如：「台南市中西區民權路一段100號」
            language: 回應語言，預設為繁體中文
            
        Returns:
            {
                "success": bool,
                "formatted_address": str,  # 格式化後的完整地址
                "latitude": float,
                "longitude": float,
                "place_id": str,
                "address_components": list,  # 地址組成元件
                "message": str
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "message": "未設定 Google Maps API Key"
            }
        
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                "address": address,
                "key": self.api_key,
                "language": language
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            if data["status"] == "OK" and data["results"]:
                result = data["results"][0]
                location = result["geometry"]["location"]
                
                return {
                    "success": True,
                    "formatted_address": result["formatted_address"],
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                    "place_id": result["place_id"],
                    "address_components": result["address_components"],
                    "location_type": result["geometry"]["location_type"],
                    "message": "地址解析成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"地址解析失敗: {data.get('status', 'UNKNOWN_ERROR')}"
                }
                
        except Exception as e:
            logger.error(f"地理編碼錯誤: {e}")
            return {
                "success": False,
                "message": f"地理編碼錯誤: {str(e)}"
            }
    
    async def reverse_geocode(self, latitude: float, longitude: float, language: str = "zh-TW") -> Dict:
        """
        反向地理編碼：將經緯度轉換為地址
        
        Args:
            latitude: 緯度
            longitude: 經度
            language: 回應語言
            
        Returns:
            {
                "success": bool,
                "formatted_address": str,
                "address_components": list,
                "message": str
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "message": "未設定 Google Maps API Key"
            }
        
        try:
            url = f"{self.base_url}/geocode/json"
            params = {
                "latlng": f"{latitude},{longitude}",
                "key": self.api_key,
                "language": language
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            if data["status"] == "OK" and data["results"]:
                result = data["results"][0]
                
                return {
                    "success": True,
                    "formatted_address": result["formatted_address"],
                    "address_components": result["address_components"],
                    "place_id": result["place_id"],
                    "message": "地址查詢成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"地址查詢失敗: {data.get('status', 'UNKNOWN_ERROR')}"
                }
                
        except Exception as e:
            logger.error(f"反向地理編碼錯誤: {e}")
            return {
                "success": False,
                "message": f"反向地理編碼錯誤: {str(e)}"
            }
    
    async def validate_address(self, address: str) -> Dict:
        """
        驗證地址是否有效（簡化版）
        
        Args:
            address: 要驗證的地址
            
        Returns:
            {
                "success": bool,
                "valid": bool,
                "formatted_address": str,
                "suggestion": str,  # 建議地址
                "message": str
            }
        """
        result = await self.geocode_address(address)
        
        if result["success"]:
            # 檢查地址的精確度
            location_type = result.get("location_type", "")
            is_precise = location_type in ["ROOFTOP", "RANGE_INTERPOLATED"]
            
            return {
                "success": True,
                "valid": True,
                "is_precise": is_precise,
                "formatted_address": result["formatted_address"],
                "suggestion": result["formatted_address"] if result["formatted_address"] != address else None,
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "message": "地址有效" if is_precise else "地址有效但不夠精確"
            }
        else:
            return {
                "success": True,
                "valid": False,
                "message": "地址無效或無法解析"
            }
    
    async def calculate_distance(
        self, 
        origin: str, 
        destination: str,
        mode: str = "driving"
    ) -> Dict:
        """
        計算兩地之間的距離和時間
        
        Args:
            origin: 起點地址
            destination: 終點地址
            mode: 交通方式 (driving, walking, bicycling, transit)
            
        Returns:
            {
                "success": bool,
                "distance": {
                    "text": str,  # 例如：「5.2 公里」
                    "value": int  # 公尺
                },
                "duration": {
                    "text": str,  # 例如：「15 分鐘」
                    "value": int  # 秒
                },
                "message": str
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "message": "未設定 Google Maps API Key"
            }
        
        try:
            url = f"{self.base_url}/distancematrix/json"
            params = {
                "origins": origin,
                "destinations": destination,
                "mode": mode,
                "key": self.api_key,
                "language": "zh-TW"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            if data["status"] == "OK":
                element = data["rows"][0]["elements"][0]
                
                if element["status"] == "OK":
                    return {
                        "success": True,
                        "distance": element["distance"],
                        "duration": element["duration"],
                        "origin": data["origin_addresses"][0],
                        "destination": data["destination_addresses"][0],
                        "message": "距離計算成功"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"無法計算距離: {element['status']}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"API 錯誤: {data.get('status', 'UNKNOWN_ERROR')}"
                }
                
        except Exception as e:
            logger.error(f"距離計算錯誤: {e}")
            return {
                "success": False,
                "message": f"距離計算錯誤: {str(e)}"
            }
    
    async def find_nearby_places(
        self,
        latitude: float,
        longitude: float,
        place_type: str = "convenience_store",
        radius: int = 1000,
        language: str = "zh-TW"
    ) -> Dict:
        """
        尋找附近的地點（例如：便利商店、政府機關）
        
        Args:
            latitude: 緯度
            longitude: 經度
            place_type: 地點類型（例如：convenience_store, government, hospital）
            radius: 搜尋半徑（公尺）
            language: 回應語言
            
        Returns:
            {
                "success": bool,
                "places": [
                    {
                        "name": str,
                        "address": str,
                        "location": {"lat": float, "lng": float},
                        "distance": float,  # 公尺
                        "rating": float,
                        "is_open": bool
                    }
                ],
                "message": str
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "message": "未設定 Google Maps API Key"
            }
        
        try:
            url = f"{self.base_url}/place/nearbysearch/json"
            params = {
                "location": f"{latitude},{longitude}",
                "radius": radius,
                "type": place_type,
                "key": self.api_key,
                "language": language
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            if data["status"] == "OK":
                places = []
                for result in data["results"]:
                    place = {
                        "name": result["name"],
                        "address": result.get("vicinity", ""),
                        "location": result["geometry"]["location"],
                        "place_id": result["place_id"],
                        "rating": result.get("rating"),
                        "is_open": result.get("opening_hours", {}).get("open_now")
                    }
                    places.append(place)
                
                return {
                    "success": True,
                    "places": places,
                    "count": len(places),
                    "message": f"找到 {len(places)} 個地點"
                }
            else:
                return {
                    "success": False,
                    "places": [],
                    "message": f"搜尋失敗: {data.get('status', 'UNKNOWN_ERROR')}"
                }
                
        except Exception as e:
            logger.error(f"地點搜尋錯誤: {e}")
            return {
                "success": False,
                "message": f"地點搜尋錯誤: {str(e)}"
            }
    
    async def get_place_details(self, place_id: str, language: str = "zh-TW") -> Dict:
        """
        取得地點詳細資訊
        
        Args:
            place_id: Google Place ID
            language: 回應語言
            
        Returns:
            {
                "success": bool,
                "name": str,
                "address": str,
                "phone": str,
                "website": str,
                "rating": float,
                "opening_hours": dict,
                "message": str
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "message": "未設定 Google Maps API Key"
            }
        
        try:
            url = f"{self.base_url}/place/details/json"
            params = {
                "place_id": place_id,
                "key": self.api_key,
                "language": language,
                "fields": "name,formatted_address,formatted_phone_number,website,rating,opening_hours,geometry"
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                data = response.json()
            
            if data["status"] == "OK":
                result = data["result"]
                
                return {
                    "success": True,
                    "name": result.get("name"),
                    "address": result.get("formatted_address"),
                    "phone": result.get("formatted_phone_number"),
                    "website": result.get("website"),
                    "rating": result.get("rating"),
                    "opening_hours": result.get("opening_hours"),
                    "location": result.get("geometry", {}).get("location"),
                    "message": "地點資訊取得成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"查詢失敗: {data.get('status', 'UNKNOWN_ERROR')}"
                }
                
        except Exception as e:
            logger.error(f"地點詳情查詢錯誤: {e}")
            return {
                "success": False,
                "message": f"地點詳情查詢錯誤: {str(e)}"
            }
    
    def parse_address_components(self, address_components: List[Dict]) -> Dict:
        """
        解析地址組成元件，提取城市、區域、街道等資訊
        
        Args:
            address_components: 從 geocoding API 取得的地址組成元件
            
        Returns:
            {
                "country": str,
                "city": str,
                "district": str,
                "street": str,
                "postal_code": str
            }
        """
        parsed = {
            "country": "",
            "city": "",
            "district": "",
            "street": "",
            "postal_code": ""
        }
        
        for component in address_components:
            types = component["types"]
            
            if "country" in types:
                parsed["country"] = component["long_name"]
            elif "administrative_area_level_1" in types:
                parsed["city"] = component["long_name"]
            elif "administrative_area_level_3" in types or "locality" in types:
                parsed["district"] = component["long_name"]
            elif "route" in types:
                parsed["street"] = component["long_name"]
            elif "postal_code" in types:
                parsed["postal_code"] = component["long_name"]
        
        return parsed


# 全域服務實例
_google_maps_service: Optional[GoogleMapsService] = None


def get_google_maps_service() -> GoogleMapsService:
    """取得 Google Maps 服務實例（單例模式）"""
    global _google_maps_service
    if _google_maps_service is None:
        _google_maps_service = GoogleMapsService()
    return _google_maps_service
