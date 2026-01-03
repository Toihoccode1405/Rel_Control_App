"""
kRel - Database Service
Singleton database connection manager with SQL Server support
"""
import os
from configparser import ConfigParser
from typing import Optional, Any
from contextlib import contextmanager

try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


class DatabaseService:
    """Singleton Database Connection Manager"""
    
    _instance: Optional["DatabaseService"] = None
    _connection: Optional[Any] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config = ConfigParser()
        self._key_file = ".dbkey"
        self._config_file = "config.ini"
        self._load_config()
    
    def _load_config(self):
        """Load configuration from config.ini"""
        if os.path.exists(self._config_file):
            self._config.read(self._config_file, encoding="utf-8")
    
    def _get_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        if not Fernet:
            raise ImportError("cryptography package required")
        
        if os.path.exists(self._key_file):
            with open(self._key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self._key_file, "wb") as f:
                f.write(key)
            return key
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a string value"""
        if not value:
            return ""
        f = Fernet(self._get_encryption_key())
        return f.encrypt(value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt an encrypted value"""
        if not encrypted_value:
            return ""
        try:
            f = Fernet(self._get_encryption_key())
            return f.decrypt(encrypted_value.encode()).decode()
        except Exception:
            # Return as-is if not encrypted (for backward compatibility)
            return encrypted_value
    
    def _get_available_driver(self) -> str:
        """Get first available ODBC driver for SQL Server"""
        if not pyodbc:
            return "{ODBC Driver 17 for SQL Server}"

        # List of preferred drivers in order
        preferred_drivers = [
            "ODBC Driver 18 for SQL Server",
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13.1 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "ODBC Driver 11 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server Native Client 10.0",
            "SQL Server",
        ]

        available = pyodbc.drivers()

        for driver in preferred_drivers:
            if driver in available:
                return "{" + driver + "}"

        # Return default if none found
        return "{ODBC Driver 17 for SQL Server}"

    def _get_connection_string(self) -> str:
        """Build SQL Server connection string from config"""
        if not self._config.has_section("database"):
            raise ValueError("Database configuration not found in config.ini")

        db_section = self._config["database"]

        server = self.decrypt_value(db_section.get("server", "localhost"))
        database = self.decrypt_value(db_section.get("database", "kRel"))
        username = self.decrypt_value(db_section.get("username", ""))
        password = self.decrypt_value(db_section.get("password", ""))

        # Get driver from config, or auto-detect if not specified or invalid
        driver_config = self.decrypt_value(db_section.get("driver", ""))
        if driver_config and driver_config.strip():
            driver = driver_config
        else:
            driver = self._get_available_driver()

        if username and password:
            return f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        else:
            return f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes"
    
    def connect(self) -> Any:
        """Get database connection (creates new if needed)"""
        if not pyodbc:
            raise ImportError("pyodbc package required for SQL Server")
        
        if self._connection is None:
            conn_str = self._get_connection_string()
            self._connection = pyodbc.connect(conn_str)
        
        return self._connection
    
    def get_connection(self) -> Any:
        """Alias for connect()"""
        return self.connect()
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor with auto-commit"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    
    def execute(self, query: str, params: tuple = None) -> Any:
        """Execute query and return cursor"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[tuple]:
        """Execute query and fetch one row"""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()
    
    def fetch_all(self, query: str, params: tuple = None) -> list:
        """Execute query and fetch all rows"""
        conn = self.connect()
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def save_config(self, server: str, database: str, username: str, 
                    password: str, driver: str = "{ODBC Driver 17 for SQL Server}"):
        """Save encrypted database configuration"""
        if not self._config.has_section("database"):
            self._config.add_section("database")
        
        self._config["database"]["server"] = self.encrypt_value(server)
        self._config["database"]["database"] = self.encrypt_value(database)
        self._config["database"]["username"] = self.encrypt_value(username)
        self._config["database"]["password"] = self.encrypt_value(password)
        self._config["database"]["driver"] = self.encrypt_value(driver)
        
        with open(self._config_file, "w", encoding="utf-8") as f:
            self._config.write(f)
        
        # Reset connection to use new config
        self.close()
        self._load_config()
    
    def test_connection(self, server: str, database: str, username: str,
                        password: str, driver: str) -> tuple[bool, str]:
        """Test database connection with given parameters"""
        try:
            if username and password:
                conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
            else:
                conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes"
            
            test_conn = pyodbc.connect(conn_str, timeout=5)
            test_conn.close()
            return True, "Kết nối thành công!"
        except Exception as e:
            return False, str(e)


# Global instance getter
def get_db() -> DatabaseService:
    """Get singleton database service instance"""
    return DatabaseService()

