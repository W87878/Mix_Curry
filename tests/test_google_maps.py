#!/usr/bin/env python3
"""
測試 Google Maps API 功能
"""
import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent))

from app.services.google_maps import GoogleMapsService


async def test_google_maps():
    """測試 Google Maps 各項功能"""
    
    print("=" * 60)
    print("🗺️  Google Maps API 功能測試")
    print("=" * 60)
    
    # 初始化服務
    maps_service = GoogleMapsService()
    
    if not maps_service.api_key:
        print("\n⚠️  警告：未設定 GOOGLE_MAPS_API_KEY 環境變數")
        print("請在 .env 檔案中設定：GOOGLE_MAPS_API_KEY=your_api_key")
        print("\n部分功能將無法使用，但可以看到錯誤處理機制")
    
    # 測試用地址
    test_addresses = [
        "台南市中西區民權路一段100號",
        "台南市政府",
        "台南市安平區永華路二段6號"
    ]
    
    # 1. 測試地理編碼
    print("\n" + "=" * 60)
    print("1️⃣  測試地理編碼（地址 → 經緯度）")
    print("=" * 60)
    
    for address in test_addresses:
        print(f"\n📍 測試地址: {address}")
        result = await maps_service.geocode_address(address)
        
        if result["success"]:
            print(f"   ✅ 成功")
            print(f"   格式化地址: {result['formatted_address']}")
            print(f"   經度: {result['longitude']}")
            print(f"   緯度: {result['latitude']}")
            print(f"   Place ID: {result['place_id'][:20]}...")
        else:
            print(f"   ❌ 失敗: {result['message']}")
    
    # 2. 測試反向地理編碼
    print("\n" + "=" * 60)
    print("2️⃣  測試反向地理編碼（經緯度 → 地址）")
    print("=" * 60)
    
    # 台南市政府座標
    lat, lng = 22.9908, 120.1847
    print(f"\n🌐 測試座標: ({lat}, {lng})")
    
    result = await maps_service.reverse_geocode(lat, lng)
    
    if result["success"]:
        print(f"   ✅ 成功")
        print(f"   地址: {result['formatted_address']}")
    else:
        print(f"   ❌ 失敗: {result['message']}")
    
    # 3. 測試地址驗證
    print("\n" + "=" * 60)
    print("3️⃣  測試地址驗證")
    print("=" * 60)
    
    test_validation_addresses = [
        "台南市中西區民權路一段100號",
        "台南市中西區",
        "無效地址12345678"
    ]
    
    for address in test_validation_addresses:
        print(f"\n📍 驗證地址: {address}")
        result = await maps_service.validate_address(address)
        
        if result["success"]:
            if result["valid"]:
                print(f"   ✅ 地址有效")
                print(f"   精確度: {'精確' if result.get('is_precise') else '不夠精確'}")
                print(f"   建議地址: {result.get('formatted_address', '無')}")
            else:
                print(f"   ❌ 地址無效")
        else:
            print(f"   ❌ 驗證失敗: {result['message']}")
    
    # 4. 測試距離計算
    print("\n" + "=" * 60)
    print("4️⃣  測試距離計算")
    print("=" * 60)
    
    origin = "台南市中西區民權路一段100號"
    destination = "台南市政府"
    
    print(f"\n📏 計算距離:")
    print(f"   起點: {origin}")
    print(f"   終點: {destination}")
    
    result = await maps_service.calculate_distance(origin, destination)
    
    if result["success"]:
        print(f"   ✅ 成功")
        print(f"   距離: {result['distance']['text']} ({result['distance']['value']} 公尺)")
        print(f"   時間: {result['duration']['text']} ({result['duration']['value']} 秒)")
    else:
        print(f"   ❌ 失敗: {result['message']}")
    
    # 5. 測試附近地點搜尋
    print("\n" + "=" * 60)
    print("5️⃣  測試附近地點搜尋（便利商店）")
    print("=" * 60)
    
    # 台南火車站附近
    lat, lng = 22.9971, 120.2127
    print(f"\n🔍 搜尋位置: ({lat}, {lng})")
    print(f"   搜尋類型: 便利商店")
    print(f"   搜尋半徑: 500 公尺")
    
    result = await maps_service.find_nearby_places(
        latitude=lat,
        longitude=lng,
        place_type="convenience_store",
        radius=500
    )
    
    if result["success"]:
        print(f"   ✅ 成功，找到 {result['count']} 個地點")
        for i, place in enumerate(result['places'][:3], 1):  # 只顯示前3個
            print(f"\n   {i}. {place['name']}")
            print(f"      地址: {place['address']}")
            print(f"      評分: {place.get('rating', '無')} ⭐")
            print(f"      營業中: {'是' if place.get('is_open') else '否'}")
    else:
        print(f"   ❌ 失敗: {result['message']}")
    
    # 6. 測試地址解析
    print("\n" + "=" * 60)
    print("6️⃣  測試地址組成解析")
    print("=" * 60)
    
    address = "台南市中西區民權路一段100號"
    print(f"\n📋 解析地址: {address}")
    
    geocode_result = await maps_service.geocode_address(address)
    
    if geocode_result["success"]:
        parsed = maps_service.parse_address_components(
            geocode_result["address_components"]
        )
        print(f"   ✅ 解析成功")
        print(f"   國家: {parsed['country']}")
        print(f"   城市: {parsed['city']}")
        print(f"   區域: {parsed['district']}")
        print(f"   街道: {parsed['street']}")
        print(f"   郵遞區號: {parsed['postal_code']}")
    else:
        print(f"   ❌ 解析失敗: {geocode_result['message']}")
    
    print("\n" + "=" * 60)
    print("✅ 測試完成！")
    print("=" * 60)
    
    # 使用說明
    print("\n📚 使用說明：")
    print("1. 在 .env 檔案中設定 GOOGLE_MAPS_API_KEY")
    print("2. 啟用 Google Maps API (Geocoding, Distance Matrix, Places)")
    print("3. 在 Google Cloud Console 設定 API 金鑰限制")
    print("4. 使用 FastAPI 端點: /api/v1/maps/*")
    print("\n範例:")
    print("  POST /api/v1/maps/validate-address")
    print('  {"address": "台南市中西區民權路一段100號"}')


if __name__ == "__main__":
    try:
        asyncio.run(test_google_maps())
    except KeyboardInterrupt:
        print("\n\n⚠️  測試已中斷")
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
