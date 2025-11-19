"""
測試憑證歷史記錄功能
"""
import asyncio
from datetime import datetime
from app.models.database import get_db_service
from app.routers.complete_flow import record_credential_history

db_service = get_db_service()


async def test_record_issued():
    """測試記錄憑證發行"""
    print("=" * 60)
    print("測試 1: 記錄憑證發行")
    print("=" * 60)
    
    # 假設我們有一個測試用的 application_id
    test_app_id = "test-app-id-123"
    test_user_id = "test-user-id-456"
    
    result = await record_credential_history(
        application_id=test_app_id,
        user_id=test_user_id,
        action_type="credential_issued",
        status="issued",
        transaction_id="test-txn-001",
        issuer_organization="台南市政府災害救助中心",
        notes="測試憑證發行記錄"
    )
    
    print(f"✅ 憑證發行記錄已建立")
    print(f"   Record ID: {result.get('id') if result else 'N/A'}")
    return result


async def test_record_verified():
    """測試記錄憑證驗證"""
    print("\n" + "=" * 60)
    print("測試 2: 記錄憑證驗證")
    print("=" * 60)
    
    test_app_id = "test-app-id-123"
    test_user_id = "test-user-id-456"
    
    result = await record_credential_history(
        application_id=test_app_id,
        user_id=test_user_id,
        action_type="credential_verified",
        status="verified",
        transaction_id="test-txn-002",
        verifier_organization="7-11 中正門市",
        verification_location={
            "type": "711_store",
            "store_id": "7-11-001",
            "address": "台南市中西區中正路123號",
            "latitude": 22.9908,
            "longitude": 120.2133,
            "verified_at": datetime.now().isoformat()
        },
        notes="測試憑證驗證記錄"
    )
    
    print(f"✅ 憑證驗證記錄已建立")
    print(f"   Record ID: {result.get('id') if result else 'N/A'}")
    return result


async def test_query_history():
    """測試查詢歷史記錄"""
    print("\n" + "=" * 60)
    print("測試 3: 查詢歷史記錄")
    print("=" * 60)
    
    test_app_id = "test-app-id-123"
    
    try:
        result = db_service.client.table("credential_history")\
            .select("*")\
            .eq("application_id", test_app_id)\
            .order("action_time", desc=True)\
            .execute()
        
        print(f"✅ 找到 {len(result.data)} 筆歷史記錄")
        
        for i, record in enumerate(result.data, 1):
            print(f"\n記錄 {i}:")
            print(f"  動作類型: {record.get('action_type')}")
            print(f"  狀態: {record.get('status')}")
            print(f"  時間: {record.get('action_time')}")
            
            if record.get('issuer_organization'):
                print(f"  發行機構: {record.get('issuer_organization')}")
            
            if record.get('verifier_organization'):
                print(f"  驗證機構: {record.get('verifier_organization')}")
            
            if record.get('verification_location'):
                print(f"  驗證地點: {record.get('verification_location')}")
            
            print(f"  備註: {record.get('notes')}")
        
        return result.data
        
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
        return None


async def test_statistics():
    """測試統計功能"""
    print("\n" + "=" * 60)
    print("測試 4: 統計數據")
    print("=" * 60)
    
    try:
        result = db_service.client.table("credential_history")\
            .select("*")\
            .execute()
        
        # 統計
        total = len(result.data)
        issued = len([r for r in result.data if r.get('status') == 'issued'])
        verified = len([r for r in result.data if r.get('status') == 'verified'])
        
        print(f"✅ 統計結果:")
        print(f"  總記錄數: {total}")
        print(f"  已發行: {issued}")
        print(f"  已驗證: {verified}")
        
        # 按災害類型統計
        disaster_types = {}
        for record in result.data:
            dt = record.get('disaster_type', 'unknown')
            disaster_types[dt] = disaster_types.get(dt, 0) + 1
        
        if disaster_types:
            print(f"\n  災害類型分布:")
            for dt, count in disaster_types.items():
                print(f"    {dt}: {count}")
        
        # 機構統計
        issuers = {}
        verifiers = {}
        
        for record in result.data:
            if record.get('issuer_organization'):
                org = record.get('issuer_organization')
                issuers[org] = issuers.get(org, 0) + 1
            
            if record.get('verifier_organization'):
                org = record.get('verifier_organization')
                verifiers[org] = verifiers.get(org, 0) + 1
        
        if issuers:
            print(f"\n  發行機構統計:")
            for org, count in issuers.items():
                print(f"    {org}: {count}")
        
        if verifiers:
            print(f"\n  驗證機構統計:")
            for org, count in verifiers.items():
                print(f"    {org}: {count}")
        
        return {
            "total": total,
            "issued": issued,
            "verified": verified,
            "disaster_types": disaster_types,
            "issuers": issuers,
            "verifiers": verifiers
        }
        
    except Exception as e:
        print(f"❌ 統計失敗: {e}")
        return None


async def cleanup_test_data():
    """清理測試資料"""
    print("\n" + "=" * 60)
    print("清理測試資料")
    print("=" * 60)
    
    test_app_id = "test-app-id-123"
    
    try:
        result = db_service.client.table("credential_history")\
            .delete()\
            .eq("application_id", test_app_id)\
            .execute()
        
        print(f"✅ 已刪除測試資料")
        
    except Exception as e:
        print(f"❌ 清理失敗: {e}")


async def main():
    """主測試流程"""
    print("\n" + "=" * 60)
    print("🧪 憑證歷史記錄功能測試")
    print("=" * 60)
    
    # 注意：這些測試需要有真實的 application 記錄才能執行
    # 如果沒有，record_credential_history 會找不到申請資料
    
    print("\n⚠️  注意：此測試需要資料庫中有對應的 application 記錄")
    print("請先確保有測試用的 application_id")
    
    # 如果要執行完整測試，請取消以下註解：
    # await test_record_issued()
    # await test_record_verified()
    # await test_query_history()
    # await test_statistics()
    # await cleanup_test_data()
    
    print("\n" + "=" * 60)
    print("✅ 測試完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
