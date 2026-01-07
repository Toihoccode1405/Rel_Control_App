"""
kRel - Database Service
Singleton database connection manager with SQL Server support
Optimized with connection health check, timeout, and performance enhancements
"""
import os
import logging
import time
import threading
from configparser import ConfigParser
from typing import Optional, Any, List
from contextlib import contextmanager
from functools import lru_cache

try:
    import pyodbc
except ImportError:
    pyodbc = None

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

# Use basic logging to avoid circular import with logger service
db_logger = logging.getLogger("kRel.database")


class DatabaseService:
    """
    Singleton Database Connection Manager

    Features:
    - Connection health check and auto-reconnect
    - Connection timeout handling
    - Thread-safe operations
    - Cached encryption key for performance
    """

    _instance: Optional["DatabaseService"] = None
    _connection: Optional[Any] = None
    _lock = threading.Lock()

    # Connection settings
    CONNECTION_TIMEOUT = 10  # seconds
    QUERY_TIMEOUT = 30  # seconds
    HEALTH_CHECK_INTERVAL = 60  # seconds

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
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
        self._encryption_key: Optional[bytes] = None  # Cached key
        self._last_health_check: float = 0
        self._load_config()
    
    def _load_config(self):
        """Load configuration from config.ini"""
        if os.path.exists(self._config_file):
            self._config.read(self._config_file, encoding="utf-8")
    
    def _get_encryption_key(self) -> bytes:
        """Get or create encryption key (cached for performance)"""
        if not Fernet:
            raise ImportError("cryptography package required")

        # Return cached key if available
        if self._encryption_key is not None:
            return self._encryption_key

        if os.path.exists(self._key_file):
            with open(self._key_file, "rb") as f:
                self._encryption_key = f.read()
        else:
            self._encryption_key = Fernet.generate_key()
            with open(self._key_file, "wb") as f:
                f.write(self._encryption_key)

        return self._encryption_key

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

    def _is_connection_healthy(self) -> bool:
        """Check if current connection is still valid"""
        if self._connection is None:
            return False

        try:
            # Quick health check query
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception:
            return False

    def _should_health_check(self) -> bool:
        """Determine if we should perform a health check"""
        return time.time() - self._last_health_check > self.HEALTH_CHECK_INTERVAL
    
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
        """
        Get database connection with health check and auto-reconnect.

        Features:
        - Connection timeout for faster failure detection
        - Periodic health check to detect stale connections
        - Auto-reconnect on connection failure
        """
        if not pyodbc:
            raise ImportError("pyodbc package required for SQL Server")

        with self._lock:
            # Check if we need to reconnect
            need_reconnect = False

            if self._connection is None:
                need_reconnect = True
            elif self._should_health_check():
                if not self._is_connection_healthy():
                    db_logger.warning("Connection health check failed, reconnecting...")
                    self._close_connection()
                    need_reconnect = True
                else:
                    self._last_health_check = time.time()

            if need_reconnect:
                conn_str = self._get_connection_string()
                db_logger.debug("Establishing database connection...")
                try:
                    self._connection = pyodbc.connect(
                        conn_str,
                        timeout=self.CONNECTION_TIMEOUT
                    )
                    # Set query timeout
                    self._connection.timeout = self.QUERY_TIMEOUT
                    self._last_health_check = time.time()
                    db_logger.info("Database connection established successfully")
                except pyodbc.Error as e:
                    db_logger.error(f"Failed to connect to database: {e}")
                    raise

        return self._connection

    def get_connection(self) -> Any:
        """Alias for connect()"""
        return self.connect()

    def _close_connection(self):
        """Internal method to close connection without lock"""
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None

    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor with auto-commit"""
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except pyodbc.Error as e:
            conn.rollback()
            # Check if it's a connection error
            if "08" in str(e.args[0]) if e.args else False:
                db_logger.warning("Connection error detected, resetting connection...")
                self._close_connection()
            db_logger.error(f"Database error, transaction rolled back: {str(e)}")
            raise
        except Exception as e:
            conn.rollback()
            db_logger.error(f"Database error, transaction rolled back: {str(e)}")
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
        if params is not None:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    
    def close(self):
        """Close database connection (thread-safe)"""
        with self._lock:
            self._close_connection()

    def is_connected(self) -> bool:
        """Check if database is currently connected"""
        return self._connection is not None and self._is_connection_healthy()
    
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

