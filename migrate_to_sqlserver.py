# migrate_to_sqlserver.py - Script chuyển dữ liệu từ SQLite sang SQL Server
import sqlite3
import sys
from configparser import ConfigParser

def migrate_data():
    """Chuyển dữ liệu từ SQLite sang SQL Server"""
    
    print("=" * 60)
    print("SCRIPT CHUYỂN DỮ LIỆU TỪ SQLITE SANG SQL SERVER")
    print("=" * 60)
    
    # 1. Kiểm tra pyodbc
    try:
        import pyodbc
        print("✓ pyodbc đã được cài đặt")
    except ImportError:
        print("✗ Lỗi: Chưa cài đặt pyodbc!")
        print("  Vui lòng chạy: pip install pyodbc")
        return False
    
    # 2. Đọc cấu hình
    config = ConfigParser()
    if not config.read("config.ini", encoding="utf-8"):
        print("✗ Lỗi: Không tìm thấy file config.ini")
        return False
    
    # 3. Kết nối SQLite
    sqlite_db = config["system"].get("db_path", "kRel.db")
    print(f"\n1. Kết nối SQLite: {sqlite_db}")
    try:
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        print("   ✓ Kết nối SQLite thành công")
    except Exception as e:
        print(f"   ✗ Lỗi kết nối SQLite: {e}")
        return False
    
    # 4. Kết nối SQL Server
    print("\n2. Kết nối SQL Server")
    if not config.has_section("database"):
        print("   ✗ Lỗi: Thiếu cấu hình [database] trong config.ini")
        return False
    
    server = config["database"].get("server", "localhost")
    database = config["database"].get("database", "kRel")
    username = config["database"].get("username", "")
    password = config["database"].get("password", "")
    driver = config["database"].get("driver", "{ODBC Driver 17 for SQL Server}")
    
    try:
        if username and password:
            conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        else:
            conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes"
        
        sqlserver_conn = pyodbc.connect(conn_str)
        sqlserver_cursor = sqlserver_conn.cursor()
        print(f"   ✓ Kết nối SQL Server thành công: {server}/{database}")
    except Exception as e:
        print(f"   ✗ Lỗi kết nối SQL Server: {e}")
        print("\n   Kiểm tra:")
        print("   - SQL Server đã chạy chưa?")
        print("   - Thông tin kết nối trong config.ini đúng chưa?")
        print("   - ODBC Driver đã cài đặt chưa?")
        return False
    
    # 5. Lấy danh sách bảng từ SQLite
    print("\n3. Lấy danh sách bảng từ SQLite")
    sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in sqlite_cursor.fetchall()]
    print(f"   Tìm thấy {len(tables)} bảng: {', '.join(tables)}")
    
    # 6. Chuyển dữ liệu từng bảng
    print("\n4. Chuyển dữ liệu:")
    total_rows = 0
    
    for table in tables:
        print(f"\n   Bảng: {table}")
        
        # Lấy dữ liệu từ SQLite
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if not rows:
            print(f"      - Không có dữ liệu")
            continue
        
        # Lấy tên cột
        columns = [desc[0] for desc in sqlite_cursor.description]
        
        # Xóa dữ liệu cũ trong SQL Server (nếu có)
        try:
            sqlserver_cursor.execute(f"DELETE FROM {table}")
            sqlserver_conn.commit()
        except:
            pass
        
        # Chèn dữ liệu vào SQL Server
        placeholders = ','.join(['?'] * len(columns))
        insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
        
        try:
            sqlserver_cursor.executemany(insert_sql, rows)
            sqlserver_conn.commit()
            print(f"      ✓ Đã chuyển {len(rows)} dòng")
            total_rows += len(rows)
        except Exception as e:
            print(f"      ✗ Lỗi: {e}")
            sqlserver_conn.rollback()
    
    # 7. Đóng kết nối
    sqlite_conn.close()
    sqlserver_conn.close()
    
    print("\n" + "=" * 60)
    print(f"HOÀN THÀNH! Đã chuyển tổng cộng {total_rows} dòng dữ liệu")
    print("=" * 60)
    print("\nBước tiếp theo:")
    print("1. Mở file config.ini")
    print("2. Thay đổi: type = sqlserver")
    print("3. Khởi động lại ứng dụng kRel")
    
    return True

if __name__ == "__main__":
    success = migrate_data()
    if not success:
        sys.exit(1)

