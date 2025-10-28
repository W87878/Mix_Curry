#!/usr/bin/env python3
"""
完整測試地圖功能 - 從登入到路線規劃
"""
import requests
import json

API_BASE = "http://localhost:8080/api/v1"

def test_map_feature():
    """測試地圖功能的完整流程"""
    
    print("=" * 70)
    print("🧪 測試地圖功能 - 完整流程")
    print("=" * 70)
    
    # Step 1: 登入里長帳號
    print("\n📝 Step 1: 登入里長帳號...")
    login_data = {
        "email": "wangyouzhi248@gmail.com",
        "password": "password123"
    }
    
    login_response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    
    if not login_response.ok:
        print(f"❌ 登入失敗: {login_response.status_code}")
        print(login_response.text)
        return
    
    login_result = login_response.json()
    access_token = login_result.get("access_token")
    user_info = login_result.get("user", {})
    district_id = user_info.get("district_id")
    
    print(f"✅ 登入成功")
    print(f"   用戶: {user_info.get('email')}")
    print(f"   角色: {user_info.get('role')}")
    print(f"   District ID: {district_id or '未設定'}")
    
    if not district_id:
        print("\n⚠️  警告: 使用者沒有 district_id")
        print("   將查詢所有案件...")
    
    # Step 2: 取得案件列表
    print(f"\n📝 Step 2: 取得案件列表...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    if district_id:
        apps_url = f"{API_BASE}/applications/district/{district_id}?status=pending"
        print(f"   URL: {apps_url}")
    else:
        apps_url = f"{API_BASE}/applications/status/pending"
        print(f"   URL: {apps_url}")
    
    apps_response = requests.get(apps_url, headers=headers)
    
    if not apps_response.ok:
        print(f"❌ 取得案件失敗: {apps_response.status_code}")
        print(apps_response.text)
        return
    
    apps_result = apps_response.json()
    applications = apps_result.get("data", {}).get("applications", [])
    
    print(f"✅ 找到 {len(applications)} 個案件")
    
    if not applications:
        print("\n⚠️  沒有案件可以測試")
        print("   請先創建測試案件: python tests/create_test_applications.py")
        return
    
    # Step 3: 檢查案件地址
    print(f"\n📝 Step 3: 檢查案件地址...")
    
    valid_apps = []
    for app in applications[:5]:  # 只檢查前 5 個
        case_no = app.get("case_no")
        damage_location = app.get("damage_location")
        address = app.get("address")
        
        has_address = bool(damage_location or address)
        status = "✅" if has_address else "❌"
        
        print(f"   {status} {case_no}")
        print(f"      災損地點: {damage_location or '未填寫'}")
        print(f"      聯絡地址: {address or '未填寫'}")
        
        if has_address:
            valid_apps.append(app)
    
    if not valid_apps:
        print("\n❌ 沒有案件有地址資訊")
        print("   執行以下命令添加地址: python tests/quick_update_addresses.py")
        return
    
    print(f"\n✅ 有 {len(valid_apps)} 個案件可用於地圖功能")
    
    # Step 4: 測試路線規劃
    print(f"\n📝 Step 4: 測試路線規劃 API...")
    
    # 準備目的地列表
    destinations = []
    for app in valid_apps[:3]:  # 最多選 3 個
        addr = app.get("damage_location") or app.get("address")
        if addr:
            destinations.append(addr)
    
    route_data = {
        "start_location": "台北市政府",
        "destinations": destinations
    }
    
    print(f"   起點: {route_data['start_location']}")
    print(f"   目的地: {len(destinations)} 個")
    for i, dest in enumerate(destinations, 1):
        print(f"      {i}. {dest}")
    
    route_response = requests.post(
        f"{API_BASE}/maps/routes/optimize",
        json=route_data,
        headers=headers
    )
    
    if not route_response.ok:
        print(f"\n❌ 路線規劃失敗: {route_response.status_code}")
        error_data = route_response.json()
        print(json.dumps(error_data, indent=2, ensure_ascii=False))
        return
    
    route_result = route_response.json()
    routes = route_result.get("data", {}).get("routes", [])
    
    print(f"\n✅ 路線規劃成功！")
    print(f"   找到 {len(routes)} 條路線\n")
    
    # 顯示前 3 條路線
    for i, route in enumerate(routes[:3], 1):
        print(f"   路線 {i}:")
        print(f"      總距離: {route.get('total_distance')}")
        print(f"      預估時間: {route.get('total_duration')}")
        print(f"      順序: {' → '.join(route.get('order', []))}")
        print()
    
    # Step 5: 總結
    print("=" * 70)
    print("🎉 測試完成！")
    print("=" * 70)
    print("\n✅ 所有功能正常運作！")
    print("\n📋 前端測試步驟：")
    print("   1. 訪問 http://localhost:8080/admin")
    print("   2. 使用以下帳號登入：")
    print("      Email: wangyouzhi248@gmail.com")
    print("      Password: password123")
    print("   3. 點擊「📍 地圖」標籤")
    print("   4. 點擊「載入案件列表」")
    print("   5. 勾選案件（建議 2-3 個）")
    print("   6. 點擊「規劃最佳路線」")
    print("   7. 查看地圖上的標記和路線")
    print("\n💡 提示：打開瀏覽器 Console 可以看到詳細的診斷資訊")

if __name__ == "__main__":
    try:
        test_map_feature()
    except requests.exceptions.ConnectionError:
        print("\n❌ 無法連接到伺服器")
        print("   請確認伺服器正在執行: python main.py")
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
