"""
kRel - Logging Service
Centralized logging with file rotation and audit trail
"""
import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from typing import Optional

from src.config import DEFAULT_LOG_PATH, CONFIG_FILE

# Log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Singleton instance
_logger_service: Optional["LoggerService"] = None


class LoggerService:
    """Centralized logging service with file rotation"""
    
    def __init__(self):
        self._log_dir = self._get_log_directory()
        self._setup_logging()
    
    def _get_log_directory(self) -> str:
        """Get log directory from config or default"""
        log_dir = DEFAULT_LOG_PATH
        
        if os.path.exists(CONFIG_FILE):
            try:
                from configparser import ConfigParser
                cfg = ConfigParser()
                cfg.read(CONFIG_FILE, encoding="utf-8")
                if cfg.has_section("system"):
                    log_dir = cfg["system"].get("log_path", DEFAULT_LOG_PATH)
            except Exception:
                pass
        
        # Create logs subdirectory
        log_path = os.path.join(log_dir, "logs")
        os.makedirs(log_path, exist_ok=True)
        return log_path
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Root logger
        root_logger = logging.getLogger("kRel")
        root_logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # File handler - rotates daily, keeps 30 days
        log_file = os.path.join(self._log_dir, "kRel.log")
        file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        file_handler.suffix = "%Y-%m-%d"
        
        # Audit log - separate file for important actions
        audit_file = os.path.join(self._log_dir, "audit.log")
        audit_handler = TimedRotatingFileHandler(
            audit_file,
            when="midnight",
            interval=1,
            backupCount=90,  # Keep 90 days for audit
            encoding="utf-8"
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        audit_handler.suffix = "%Y-%m-%d"
        
        # Add handlers
        root_logger.addHandler(file_handler)
        
        # Audit logger
        audit_logger = logging.getLogger("kRel.audit")
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
    
    def get_logger(self, name: str = "kRel") -> logging.Logger:
        """Get a logger instance"""
        return logging.getLogger(f"kRel.{name}")
    
    def get_audit_logger(self) -> logging.Logger:
        """Get audit logger for important actions"""
        return logging.getLogger("kRel.audit")
    
    def debug(self, message: str, name: str = "app"):
        """Log debug message"""
        self.get_logger(name).debug(message)
    
    def info(self, message: str, name: str = "app"):
        """Log info message"""
        self.get_logger(name).info(message)
    
    def warning(self, message: str, name: str = "app"):
        """Log warning message"""
        self.get_logger(name).warning(message)
    
    def error(self, message: str, name: str = "app", exc_info: bool = False):
        """Log error message"""
        self.get_logger(name).error(message, exc_info=exc_info)
    
    def audit(self, action: str, user: str = "", details: str = ""):
        """Log audit action (login, data changes, etc.)"""
        msg = f"[{action}]"
        if user:
            msg += f" User: {user}"
        if details:
            msg += f" | {details}"
        self.get_audit_logger().info(msg)
    
    @property
    def log_directory(self) -> str:
        """Get current log directory"""
        return self._log_dir


def get_logger_service() -> LoggerService:
    """Get singleton logger service instance"""
    global _logger_service
    if _logger_service is None:
        _logger_service = LoggerService()
    return _logger_service


def get_logger(name: str = "app") -> logging.Logger:
    """Convenience function to get a logger"""
    return get_logger_service().get_logger(name)


def log_audit(action: str, user: str = "", details: str = ""):
    """Convenience function for audit logging"""
    get_logger_service().audit(action, user, details)

