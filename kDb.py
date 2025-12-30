# kDb.py - Database Abstraction Layer
import os
from configparser import ConfigParser
from cryptography.fernet import Fernet

class DatabaseConnection:
    """Lớp trừu tượng để kết nối database SQL Server"""

    def __init__(self, config_file="config.ini"):
        self.config_file = config_file
        self.conn = None
        self.db_type = "sqlserver"
        self.config = self._load_config()

    def _load_config(self):
        """Đọc cấu hình từ file config.ini"""
        cfg = ConfigParser()
        if os.path.exists(self.config_file):
            cfg.read(self.config_file, encoding="utf-8")
        return cfg

    def _get_encryption_key(self):
        key_file = ".dbkey"
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, "wb") as f:
                f.write(key)
            return key

    def _decrypt_value(self, encrypted_value):
        if not encrypted_value: return ""
        try:
            key = self._get_encryption_key()
            f = Fernet(key)
            return f.decrypt(encrypted_value.encode()).decode()
        except:
            return encrypted_value

    def connect(self):
        """Kết nối đến database SQL Server"""
        self.conn = self._connect_sqlserver()
        return self.conn

    def _connect_sqlserver(self):
        """Kết nối SQL Server"""
        try:
            import pyodbc
        except ImportError:
            raise ImportError("Cần cài đặt pyodbc để kết nối SQL Server: pip install pyodbc")

        if not self.config.has_section("database"):
            from PyQt6.QtWidgets import QMessageBox, QApplication
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            QMessageBox.warning(None, "Lỗi DB", "Thiếu cấu hình [database] trong config.ini")
            raise ValueError("Thiếu cấu hình [database] trong config.ini")

        server = self._decrypt_value(self.config["database"].get("server", ""))
        database = self._decrypt_value(self.config["database"].get("database", ""))
        username = self._decrypt_value(self.config["database"].get("username", ""))
        password = self._decrypt_value(self.config["database"].get("password", ""))
        driver = self._decrypt_value(self.config["database"].get("driver", "{ODBC Driver 17 for SQL Server}"))

        if not server or not database:
            from PyQt6.QtWidgets import QMessageBox, QApplication
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            QMessageBox.warning(None, "Cấu hình thiếu", "Vui lòng vào tab CÀI ĐẶT > Cấu hình SQL Server để thiết lập Server và Database!")
            raise ValueError("Server hoặc Database chưa được cấu hình")

        if username and password:
            conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        else:
            conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes"

        return pyodbc.connect(conn_str)

    def execute(self, query, params=None):
        """Thực thi câu lệnh SQL"""
        if self.conn is None:
            self.connect()

        cursor = self.conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def executemany(self, query, params_list):
        """Thực thi nhiều câu lệnh SQL"""
        if self.conn is None:
            self.connect()

        cursor = self.conn.cursor()
        cursor.executemany(query, params_list)
        return cursor

    def commit(self):
        """Commit transaction"""
        if self.conn:
            self.conn.commit()

    def rollback(self):
        """Rollback transaction"""
        if self.conn:
            self.conn.rollback()

    def close(self):
        """Đóng kết nối"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def fetchone(self, query, params=None):
        """Lấy một dòng kết quả"""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query, params=None):
        """Lấy tất cả kết quả"""
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def get_placeholder(self):
        """Trả về ký tự placeholder phù hợp với database type"""
        return "?"

    def insert_or_ignore(self, table, columns, values):
        """Thực hiện INSERT OR IGNORE tương thích với SQL Server"""
        cursor = self.conn.cursor()
        placeholders = ','.join(['?'] * len(values))
        check_col = columns.split(',')[0] if ',' in columns else columns
        cursor.execute(f"IF NOT EXISTS (SELECT 1 FROM {table} WHERE {check_col}=?) INSERT INTO {table} ({columns}) VALUES ({placeholders})", [values[0]] + list(values))
        return cursor

    def __enter__(self):
        """Context manager enter"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()

    def cursor(self):
        """Trả về cursor từ connection"""
        if self.conn is None:
            self.connect()
        return self.conn.cursor()

