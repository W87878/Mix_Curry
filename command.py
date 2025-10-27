#!/usr/bin/env python
"""
災民補助申請系統 - 管理命令腳本
提供資料庫管理、測試資料生成等功能
"""
import sys
import os
import argparse
from datetime import datetime, date, timedelta
from decimal import Decimal
from pathlib import Path
from app.models.database import db_service
from app.settings import get_settings

settings = get_settings()

# 顏色輸出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def confirm_action(prompt):
    """確認操作"""
    response = input(f"{Colors.WARNING}{prompt} (yes/no): {Colors.ENDC}").lower()
    return response in ['yes', 'y']

# ==========================================
# 資料庫清除功能
# ==========================================

def clear_all_tables(force=False):
    """
    清除所有資料表的內容
    按照外鍵依賴順序刪除
    """
    print_header("🗑️  清除所有資料表")
    
    if not force:
        print_warning("此操作將刪除所有資料表中的資料！")
        print_warning(f"資料庫: {settings.SUPABASE_URL}")
        
        if not confirm_action("確定要繼續嗎？"):
            print_info("操作已取消")
            return
    
    # 資料表清除順序（考慮外鍵依賴）
    tables = [
        "subsidy_items",
        "digital_certificates",
        "review_records",
        "damage_photos",
        "applications",
        "users",
        "system_settings",
    ]
    
    print_info("開始清除資料表...")
    
    for table in tables:
        try:
            result = db_service.client.table(table).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            count = len(result.data) if result.data else 0
            print_success(f"{table}: 已刪除 {count} 筆資料")
        except Exception as e:
            print_error(f"{table}: 刪除失敗 - {str(e)}")
    
    print_success("\n所有資料表已清除完成！")

def clear_table(table_name, force=False):
    """清除指定資料表"""
    print_header(f"🗑️  清除資料表: {table_name}")
    
    if not force:
        if not confirm_action(f"確定要清除 {table_name} 的所有資料嗎？"):
            print_info("操作已取消")
            return
    
    try:
        result = db_service.client.table(table_name).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        count = len(result.data) if result.data else 0
        print_success(f"已刪除 {count} 筆資料")
    except Exception as e:
        print_error(f"刪除失敗: {str(e)}")

# ==========================================
# 資料表結構管理
# ==========================================

def drop_all_tables(force=False):
    """
    刪除所有資料表（DROP TABLE）
    ⚠️ 危險操作！會完全移除資料表結構
    """
    print_header("💣 刪除所有資料表（DROP TABLE）")
    
    if not force:
        print_error("⚠️  此操作將完全刪除所有資料表結構和資料！")
        print_error("⚠️  這是不可逆的操作！")
        print_warning(f"資料庫: {settings.SUPABASE_URL}")
        print_warning("\n請輸入 'DROP ALL TABLES' 來確認操作（大小寫敏感）")
        
        confirmation = input(f"{Colors.WARNING}確認文字: {Colors.ENDC}")
        if confirmation != "DROP ALL TABLES":
            print_info("操作已取消")
            return
    
    # 資料表刪除順序（考慮外鍵依賴）
    tables = [
        "subsidy_items",
        "bank_verification_records",
        "notifications",
        "digital_certificates",
        "review_records",
        "damage_photos",
        "applications",
        "users",
        "districts",
        "system_settings",
    ]
    
    print_info("開始刪除資料表...")
    
    success_count = 0
    failed_count = 0
    
    for table in tables:
        try:
            # 使用 Supabase RPC 或直接 SQL 執行 DROP TABLE
            # 注意：Supabase 的 Python client 不直接支援 DROP TABLE
            # 需要透過 RPC 或使用管理 API
            print_warning(f"準備刪除資料表: {table}")
            
            # 這裡我們使用 PostgreSQL 的 SQL 來刪除表
            # 因為 Supabase Python client 不支援 DDL 操作
            # 建議使用 psql 或 Supabase Dashboard 來執行
            print_error(f"⚠️  {table}: 需要手動執行 SQL: DROP TABLE IF EXISTS {table} CASCADE;")
            failed_count += 1
            
        except Exception as e:
            print_error(f"{table}: 刪除失敗 - {str(e)}")
            failed_count += 1
    
    print_warning(f"\n⚠️  Supabase Python Client 不支援直接執行 DROP TABLE 操作")
    print_info("請使用以下方式刪除資料表：")
    print_info("1. 在 Supabase Dashboard 的 SQL Editor 中執行")
    print_info("2. 使用 psql 連接資料庫並執行 SQL")
    print_info("3. 使用 migration/drop_tables.sql 腳本")
    
    # 生成 DROP TABLE SQL 腳本
    sql_file = Path(__file__).parent / "migration" / "drop_all_tables.sql"
    generate_drop_tables_sql(sql_file, tables)
    print_success(f"\n✅ 已生成 DROP TABLE SQL 腳本: {sql_file}")

def generate_drop_tables_sql(output_path: Path, tables: list):
    """生成 DROP TABLE SQL 腳本"""
    output_path.parent.mkdir(exist_ok=True)
    
    sql_content = """-- ==========================================
-- 災民補助申請系統 - 刪除所有資料表
-- ⚠️ 危險操作！請謹慎使用！
-- 生成時間: {timestamp}
-- ==========================================

-- 停用觸發器
DROP TRIGGER IF EXISTS update_districts_updated_at ON districts;
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_applications_updated_at ON applications;
DROP TRIGGER IF EXISTS update_system_settings_updated_at ON system_settings;
DROP TRIGGER IF EXISTS trigger_auto_assign_reviewer ON applications;

-- 刪除函數
DROP FUNCTION IF EXISTS update_updated_at_column();
DROP FUNCTION IF EXISTS generate_case_no();
DROP FUNCTION IF EXISTS auto_assign_reviewer();

-- 刪除資料表（按照依賴順序）
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    for table in tables:
        sql_content += f"DROP TABLE IF EXISTS {table} CASCADE;\n"
    
    sql_content += """
-- ==========================================
-- 完成
-- ==========================================
"""
    
    output_path.write_text(sql_content, encoding='utf-8')

def create_all_tables(force=False):
    """
    根據 database_schema.sql 創建所有資料表
    """
    print_header("🏗️  創建所有資料表")
    
    schema_file = Path(__file__).parent / "migration" / "database_schema.sql"
    
    if not schema_file.exists():
        print_error(f"找不到資料庫結構檔案: {schema_file}")
        return
    
    if not force:
        print_warning("此操作將根據 database_schema.sql 創建所有資料表")
        print_warning(f"Schema 檔案: {schema_file}")
        print_warning(f"資料庫: {settings.SUPABASE_URL}")
        
        if not confirm_action("確定要繼續嗎？"):
            print_info("操作已取消")
            return
    
    print_info(f"讀取 SQL 檔案: {schema_file}")
    
    try:
        sql_content = schema_file.read_text(encoding='utf-8')
        
        # 分析 SQL 內容
        lines = sql_content.split('\n')
        total_lines = len(lines)
        print_info(f"SQL 檔案共 {total_lines} 行")
        
        # 統計資料表數量
        create_table_count = sql_content.count('CREATE TABLE')
        create_index_count = sql_content.count('CREATE INDEX')
        create_function_count = sql_content.count('CREATE OR REPLACE FUNCTION')
        create_trigger_count = sql_content.count('CREATE TRIGGER')
        
        print_info(f"將創建: {create_table_count} 個資料表")
        print_info(f"將創建: {create_index_count} 個索引")
        print_info(f"將創建: {create_function_count} 個函數")
        print_info(f"將創建: {create_trigger_count} 個觸發器")
        
        print_warning("\n⚠️  Supabase Python Client 不支援直接執行 DDL 操作")
        print_info("請使用以下方式創建資料表：")
        print_info("1. 在 Supabase Dashboard 的 SQL Editor 中執行")
        print_info("2. 使用 psql 連接資料庫並執行 SQL")
        print_info(f"3. 直接執行: psql <connection_string> -f {schema_file}")
        
        # 提供便捷的複製指令
        print_info("\n📋 複製以下指令到 Supabase SQL Editor：")
        print(f"\n{Colors.OKCYAN}-- 在 Supabase Dashboard > SQL Editor 貼上並執行{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'-' * 60}{Colors.ENDC}")
        
        # 顯示前 20 行作為預覽
        preview_lines = lines[:20]
        for line in preview_lines:
            if line.strip() and not line.strip().startswith('--'):
                print(f"{Colors.OKCYAN}{line}{Colors.ENDC}")
        
        print(f"{Colors.OKCYAN}...（省略 {total_lines - 20} 行）{Colors.ENDC}")
        print(f"{Colors.OKCYAN}{'-' * 60}{Colors.ENDC}\n")
        
        print_success(f"✅ SQL 檔案已準備好: {schema_file}")
        print_info("請手動在 Supabase Dashboard 執行此檔案")
        
    except Exception as e:
        print_error(f"讀取 SQL 檔案失敗: {str(e)}")
        import traceback
        traceback.print_exc()

# ==========================================
# 測試資料生成
# ==========================================

def create_test_data():
    """建立測試資料"""
    print_header("📝 建立測試資料")
    
    try:
        # 1. 建立測試使用者
        print_info("建立測試使用者...")
        
        # 災民
        applicant = db_service.create_user({
            "email": "test.applicant@example.com",
            "phone": "0912345678",
            "full_name": "測試災民",
            "id_number": "A123456789",
            "role": "applicant"
        })
        print_success(f"災民建立成功: {applicant['full_name']} ({applicant['id']})")
        
        # 審核員
        reviewer = db_service.create_user({
            "email": "test.reviewer@example.com",
            "phone": "0987654321",
            "full_name": "測試審核員",
            "id_number": "B987654321",
            "role": "reviewer"
        })
        print_success(f"審核員建立成功: {reviewer['full_name']} ({reviewer['id']})")
        
        # 2. 建立測試申請案件
        print_info("\n建立測試申請案件...")
        
        application = db_service.create_application({
            "applicant_id": applicant['id'],
            "applicant_name": applicant['full_name'],
            "id_number": applicant['id_number'],
            "phone": applicant['phone'],
            "address": "台南市中西區民權路100號",
            "disaster_date": date.today() - timedelta(days=7),
            "disaster_type": "typhoon",
            "damage_description": "一樓淹水約50公分，客廳家具、電器設備受損嚴重",
            "damage_location": "台南市中西區民權路100號1樓",
            "estimated_loss": 80000,
            "subsidy_type": "housing",
            "requested_amount": 50000,
        })
        print_success(f"申請案件建立成功: {application['case_no']}")
        
        # 3. 建立審核記錄
        print_info("\n建立審核記錄...")
        
        review = db_service.create_review_record({
            "application_id": application['id'],
            "reviewer_id": reviewer['id'],
            "reviewer_name": reviewer['full_name'],
            "action": "under_review",
            "previous_status": "pending",
            "new_status": "under_review",
            "comments": "案件已進入審核流程"
        })
        print_success("審核記錄建立成功")
        
        # 4. 更新案件狀態
        db_service.update_application_status(
            application['id'],
            status='under_review'
        )
        
        print_success("\n✨ 測試資料建立完成！")
        print_info(f"\n測試帳號資訊：")
        print_info(f"  災民: {applicant['email']} (ID: {applicant['id']})")
        print_info(f"  審核員: {reviewer['email']} (ID: {reviewer['id']})")
        print_info(f"  申請案件: {application['case_no']} (ID: {application['id']})")
        
    except Exception as e:
        print_error(f"建立測試資料失敗: {str(e)}")
        import traceback
        traceback.print_exc()

# ==========================================
# 統計資訊
# ==========================================

def show_statistics():
    """顯示資料庫統計資訊"""
    print_header("📊 資料庫統計資訊")
    
    tables = {
        "users": "使用者",
        "applications": "申請案件",
        "damage_photos": "災損照片",
        "review_records": "審核記錄",
        "digital_certificates": "數位憑證",
        "subsidy_items": "補助項目",
    }
    
    print(f"{'資料表':<25} {'中文名稱':<15} {'資料筆數':>10}")
    print("-" * 60)
    
    total = 0
    for table, name in tables.items():
        try:
            result = db_service.client.table(table).select('id', count='exact').execute()
            count = result.count if hasattr(result, 'count') else len(result.data)
            total += count
            print(f"{table:<25} {name:<15} {count:>10}")
        except Exception as e:
            print(f"{table:<25} {name:<15} {'錯誤':>10}")
    
    print("-" * 60)
    print(f"{'總計':<40} {total:>10}")
    
    # 顯示案件狀態統計
    print_info("\n申請案件狀態分佈：")
    try:
        statuses = ["pending", "under_review", "site_inspection", "approved", "rejected", "completed"]
        for status in statuses:
            apps = db_service.get_applications_by_status(status, limit=1000)
            if len(apps) > 0:
                print(f"  {status:<20}: {len(apps)} 筆")
    except Exception as e:
        print_error(f"無法取得狀態統計: {str(e)}")

# ==========================================
# 資料庫連線測試
# ==========================================

def test_connection():
    """測試資料庫連線"""
    print_header("🔌 測試資料庫連線")
    
    try:
        print_info(f"Supabase URL: {settings.SUPABASE_URL}")
        
        # 測試連線
        result = db_service.client.table('users').select('id').limit(1).execute()
        print_success("資料庫連線成功！")
        
        # 測試 RPC 函數
        try:
            case_no = db_service.client.rpc('generate_case_no').execute()
            print_success(f"RPC 函數測試成功！下一個案件編號: {case_no.data}")
        except Exception as e:
            print_warning(f"RPC 函數測試失敗: {str(e)}")
        
    except Exception as e:
        print_error(f"資料庫連線失敗: {str(e)}")

# ==========================================
# 主程式
# ==========================================

def main():
    parser = argparse.ArgumentParser(
        description='災民補助申請系統 - 管理命令工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  python command.py clear                 # 清除所有資料表的資料（保留結構）
  python command.py clear-table users     # 清除指定資料表的資料
  python command.py drop-all-tables       # 刪除所有資料表（DROP TABLE）
  python command.py create-all-tables     # 創建所有資料表
  python command.py create-test-data      # 建立測試資料
  python command.py stats                 # 顯示統計資訊
  python command.py test                  # 測試資料庫連線
        """
    )
    
    parser.add_argument(
        'action',
        choices=['clear', 'clear-table', 'drop-all-tables', 'create-all-tables', 'create-test-data', 'stats', 'test'],
        help='要執行的操作'
    )
    
    parser.add_argument(
        'table',
        nargs='?',
        help='資料表名稱（用於 clear-table）'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='強制執行，不要求確認'
    )
    
    args = parser.parse_args()
    
    # 執行對應的操作
    if args.action == 'clear':
        clear_all_tables(force=args.force)
    
    elif args.action == 'clear-table':
        if not args.table:
            print_error("請指定要清除的資料表名稱")
            print_info("例如: python command.py clear-table users")
            sys.exit(1)
        clear_table(args.table, force=args.force)
    
    elif args.action == 'drop-all-tables':
        drop_all_tables(force=args.force)
    
    elif args.action == 'create-all-tables':
        create_all_tables(force=args.force)
    
    elif args.action == 'create-test-data':
        create_test_data()
    
    elif args.action == 'stats':
        show_statistics()
    
    elif args.action == 'test':
        test_connection()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_warning("\n\n操作已中斷")
        sys.exit(0)
    except Exception as e:
        print_error(f"\n發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

