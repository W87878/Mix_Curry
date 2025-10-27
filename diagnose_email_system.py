#!/usr/bin/env python3
"""
Email 系統診斷腳本
檢查所有配置和路徑是否正確
"""

import sys
import os
from pathlib import Path

print("🔍 災害補助 Email 系統診斷")
print("="*60)

# 1. 檢查 Python 路徑
print("\n1️⃣ Python 環境")
print(f"   Python 版本: {sys.version}")
print(f"   執行路徑: {sys.executable}")

# 2. 檢查專案路徑
project_root = Path(__file__).parent
print(f"\n2️⃣ 專案路徑")
print(f"   專案根目錄: {project_root}")
print(f"   是否存在: {project_root.exists()}")

# 3. 檢查 gmaillib
gmaillib_path = project_root / 'app' / 'services' / 'gmaillib'
print(f"\n3️⃣ gmaillib 路徑")
print(f"   路徑: {gmaillib_path}")
print(f"   是否存在: {gmaillib_path.exists()}")

if gmaillib_path.exists():
    simplegmail_path = gmaillib_path / 'simplegmail'
    print(f"   simplegmail: {simplegmail_path.exists()}")
    if simplegmail_path.exists():
        files = list(simplegmail_path.glob('*.py'))
        print(f"   Python 檔案: {len(files)} 個")
        for f in files[:5]:
            print(f"     - {f.name}")

# 4. 檢查 Gmail profile
profiles_path = project_root / 'app' / 'services' / 'edm' / 'profiles' / 'disaster'
print(f"\n4️⃣ Gmail Profile")
print(f"   路徑: {profiles_path}")
print(f"   是否存在: {profiles_path.exists()}")

if profiles_path.exists():
    client_secret = profiles_path / 'client_secret.json'
    gmail_token = profiles_path / 'gmail_token.json'
    print(f"   client_secret.json: {client_secret.exists()}")
    print(f"   gmail_token.json: {gmail_token.exists()}")

# 5. 檢查 Email 模板
templates_path = project_root / 'app' / 'services' / 'edm' / 'templates'
print(f"\n5️⃣ Email 模板")
print(f"   路徑: {templates_path}")
print(f"   是否存在: {templates_path.exists()}")

if templates_path.exists():
    approval_template = templates_path / 'approval_notification.html'
    rejection_template = templates_path / 'rejection_notification.html'
    print(f"   approval_notification.html: {approval_template.exists()}")
    print(f"   rejection_notification.html: {rejection_template.exists()}")

# 6. 檢查環境變數
print(f"\n6️⃣ 環境變數")
env_file = project_root / '.env'
print(f"   .env 檔案: {env_file.exists()}")

from dotenv import load_dotenv
load_dotenv()

print(f"   SUPABASE_URL: {'✅ 已設定' if os.getenv('SUPABASE_URL') else '❌ 未設定'}")
print(f"   SUPABASE_SERVICE_ROLE: {'✅ 已設定' if os.getenv('SUPABASE_SERVICE_ROLE') else '❌ 未設定'}")
print(f"   NOTIFICATION_EMAIL: {os.getenv('NOTIFICATION_EMAIL', '未設定')}")
print(f"   GMAIL_PROFILE_DIR: {os.getenv('GMAIL_PROFILE_DIR', '未設定')}")

# 7. 測試 import
print(f"\n7️⃣ 測試 Import")
try:
    sys.path.insert(0, str(project_root))
    from app.services.edm.send_disaster_notification import DisasterNotificationService
    print("   ✅ DisasterNotificationService import 成功")
    
    # 嘗試初始化
    try:
        service = DisasterNotificationService()
        print("   ✅ 服務初始化成功")
        print(f"   發件人: {service.sender_email}")
        print(f"   工作目錄: {service.working_dir}")
    except Exception as e:
        print(f"   ❌ 服務初始化失敗: {e}")
        
except Exception as e:
    print(f"   ❌ Import 失敗: {e}")
    import traceback
    traceback.print_exc()

# 8. 檢查 Supabase 連線
print(f"\n8️⃣ Supabase 連線")
try:
    from supabase import create_client
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE')
    
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("   ✅ Supabase 連線成功")
        
        # 測試查詢
        try:
            response = supabase.table('users').select('count').limit(1).execute()
            print(f"   ✅ 資料庫查詢成功")
        except Exception as e:
            print(f"   ⚠️  查詢測試失敗: {e}")
    else:
        print("   ❌ Supabase 環境變數未設定")
        
except Exception as e:
    print(f"   ❌ Supabase 測試失敗: {e}")

print("\n" + "="*60)
print("✅ 診斷完成！")
print("\n如果所有項目都顯示 ✅，表示系統配置正確。")
print("如果有 ❌，請根據錯誤訊息修復相關問題。")
