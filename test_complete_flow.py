"""
測試完整的災害補助領取流程
符合真實的政府 API 流程
"""
import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.gov_wallet import get_gov_wallet_service

# ANSI 顏色
GREEN = '\033[92m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_step(step_num, title):
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}步驟 {step_num}: {title}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

async def test_complete_flow():
    """測試完整流程"""
    
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}🎯 完整政府 API 流程測試{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")
    
    gov_service = get_gov_wallet_service()
    
    print(f"{BLUE}發行端 API: {gov_service.issuer_base_url}{RESET}")
    print(f"{BLUE}驗證端 API: {gov_service.verifier_base_url}{RESET}")
    print(f"{BLUE}發行端狀態: {'真實 API ✅' if gov_service.issuer_api_key else '模擬模式 ⚠️'}{RESET}")
    print(f"{BLUE}驗證端狀態: {'真實 API ✅' if gov_service.verifier_api_key else '模擬模式 ⚠️'}{RESET}")
    
    # ==========================================
    # 步驟 1: 災民填寫表單（略過，假設已完成）
    # ==========================================
    print_step("1️⃣", "災民填寫表單（已完成）")
    
    application_data = {
        "applicant_name": "王小明",
        "id_number": "A123456789",
        "phone": "0912345678",
        "address": "台南市中西區民生路100號",
        "disaster_type": "typhoon"
    }
    
    print(f"{YELLOW}災民資料：{RESET}")
    for key, value in application_data.items():
        print(f"  {key}: {value}")
    
    # ==========================================
    # 步驟 2-3: 里長審核 + 發行憑證
    # ==========================================
    print_step("2️⃣-3️⃣", "里長審核 + 發行數位憑證")
    
    print(f"{BLUE}📝 里長審核通過{RESET}")
    print(f"{BLUE}🚀 呼叫政府發行端 API (POST /api/qrcode/data)...{RESET}\n")
    
    # 準備欄位
    now = datetime.now()
    issuance_date = now.strftime("%Y%m%d")
    expired_date = (now.replace(year=now.year + 1)).strftime("%Y%m%d")
    
    fields = [
        {"ename": "name", "content": application_data["applicant_name"]},
        {"ename": "id_number", "content": application_data["id_number"]},
        {"ename": "phone_number", "content": application_data["phone"]},
        {"ename": "registered_address", "content": application_data["address"]},
        {"ename": "address", "content": application_data["address"]}
    ]
    
    # 使用真實 vcUid
    vc_uid = "00000000_subsidy_666"
    
    issue_result = await gov_service.generate_qrcode_data(
        vctid=vc_uid,
        issuance_date=issuance_date,
        expired_date=expired_date,
        fields=fields
    )
    
    if issue_result.get("success"):
        print(f"{GREEN}✅ 憑證發行成功！{RESET}")
        print(f"{YELLOW}發行結果：{RESET}")
        print(f"  transaction_id: {issue_result.get('transaction_id')}")
        print(f"  deep_link: {issue_result.get('deep_link')}")
        print(f"  qr_code_data: [QR Code 資料，長度: {len(issue_result.get('qr_code_data', ''))}]")
        print(f"\n{GREEN}📱 QR Code 已發送給災民{RESET}")
        
        transaction_id_vc = issue_result.get('transaction_id')
    else:
        print(f"{RED}❌ 憑證發行失敗: {issue_result.get('message')}{RESET}")
        if issue_result.get('error_detail'):
            print(f"{RED}詳細錯誤: {issue_result.get('error_detail')}{RESET}")
        return False
    
    # ==========================================
    # 步驟 4: 災民用 APP 掃描 QR Code（略過）
    # ==========================================
    print_step("4️⃣", "災民用 APP 掃描 QR Code（模擬）")
    
    print(f"{BLUE}👤 災民打開「TW FidO 數位憑證皮夾」APP{RESET}")
    print(f"{BLUE}📷 掃描 QR Code{RESET}")
    print(f"{BLUE}💾 憑證已儲存到 APP{RESET}")
    
    await asyncio.sleep(1)
    
    # ==========================================
    # 步驟 5: 7-11 機台產生 VP 驗證 QR Code
    # ==========================================
    print_step("5️⃣", "7-11 機台產生 VP 驗證 QR Code")
    
    print(f"{BLUE}🏪 災民到 7-11{RESET}")
    print(f"{BLUE}🖥️  點擊「災害補助領取」{RESET}")
    print(f"{BLUE}🚀 呼叫政府驗證端 API (GET /api/oidvp/qrcode)...{RESET}\n")
    
    # VP 驗證服務代碼 (從 VP 面板)
    vp_ref = "00000000_subsidy_667"
    
    # 產生隨機 transaction_id
    import uuid
    vp_transaction_id = str(uuid.uuid4())[:50]
    
    vp_qr_result = await gov_service.generate_vp_qrcode(
        ref=vp_ref,
        transaction_id=vp_transaction_id
    )
    
    if vp_qr_result.get("success"):
        print(f"{GREEN}✅ VP QR Code 產生成功！{RESET}")
        print(f"{YELLOW}VP QR Code：{RESET}")
        print(f"  transaction_id: {vp_qr_result.get('transaction_id')}")
        print(f"  auth_uri: {vp_qr_result.get('auth_uri')}")
        print(f"  qrcode_image: [QR Code 圖片資料]")
        print(f"\n{BLUE}📱 災民用 APP 掃描機台 QR Code{RESET}")
        
        final_transaction_id = vp_qr_result.get('transaction_id')
        print(vp_qr_result.get('qrcode_image'))
    else:
        print(f"{RED}❌ VP QR Code 產生失敗: {vp_qr_result.get('message')}{RESET}")
        return False
    
    await asyncio.sleep(2)
    
    # ==========================================
    # 步驟 6: 驗證 VP 並發放補助
    # ==========================================
    print_step("6️⃣", "驗證 VP 並發放補助")
    
    print(f"{BLUE}✅ APP 掃描完成{RESET}")
    print(f"{BLUE}🚀 呼叫政府驗證端 API (POST /api/oidvp/result)...{RESET}\n")
    
    verify_result = await gov_service.verify_vp_result(
        transaction_id=final_transaction_id
    )
    
    if verify_result.get("success") and verify_result.get("verify_result"):
        print(f"{GREEN}{'='*70}{RESET}")
        print(f"{GREEN}✅ 驗證成功！補助已發放！{RESET}")
        print(f"{GREEN}{'='*70}{RESET}\n")
        
        credential_data = verify_result.get("credential_data", {})
        print(f"{YELLOW}災民資訊：{RESET}")
        for key, value in credential_data.items():
            print(f"  {key}: {value}")
        
        print(f"\n{GREEN}💰 補助金額已發放到災民帳戶{RESET}")
    else:
        print(f"{RED}❌ 驗證失敗: {verify_result.get('message')}{RESET}")
        return False
    
    # ==========================================
    # 總結
    # ==========================================
    print(f"\n{BOLD}{GREEN}{'='*70}{RESET}")
    print(f"{BOLD}{GREEN}🎉 完整流程測試成功！{RESET}")
    print(f"{BOLD}{GREEN}{'='*70}{RESET}\n")
    
    print(f"{BLUE}流程總結：{RESET}")
    print(f"  1️⃣  災民填寫表單 → 創建案件")
    print(f"  2️⃣  里長審核通過 → 呼叫發行端 API")
    print(f"  3️⃣  系統發行憑證 → 發送 QR Code 給災民")
    print(f"  4️⃣  災民用 APP 掃描 → 儲存憑證到 APP")
    print(f"  5️⃣  災民到 7-11 → 機台產生 VP QR Code")
    print(f"  6️⃣  APP 掃描機台 QR → 驗證成功 → 發放補助")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(test_complete_flow())
        if success:
            print(f"\n{GREEN}✅ 所有測試通過{RESET}\n")
            sys.exit(0)
        else:
            print(f"\n{RED}❌ 測試失敗{RESET}\n")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  測試被中斷{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}❌ 測試發生錯誤: {e}{RESET}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

