"""
kRel - Security Utilities
Input sanitization and validation utilities for security
"""
import re
import html
from typing import Optional, Any


class InputSanitizer:
    """
    Input sanitization utilities to prevent injection attacks.
    
    Features:
    - SQL injection prevention
    - XSS prevention (HTML escaping)
    - Path traversal prevention
    - General input cleaning
    """
    
    # Dangerous SQL patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)",
        r"(--|;|/\*|\*/)",
        r"(\bOR\b\s+\d+\s*=\s*\d+)",
        r"(\bAND\b\s+\d+\s*=\s*\d+)",
        r"(\'|\"|`)",
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e/",
        r"\.%2e/",
    ]
    
    @staticmethod
    def sanitize_string(value: Optional[str], max_length: int = 1000) -> str:
        """
        Basic string sanitization.
        
        - Strips whitespace
        - Limits length
        - Removes null bytes
        """
        if value is None:
            return ""
        
        # Convert to string if needed
        value = str(value)
        
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Strip whitespace
        value = value.strip()
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @staticmethod
    def escape_html(value: Optional[str]) -> str:
        """Escape HTML special characters to prevent XSS"""
        if value is None:
            return ""
        return html.escape(str(value))
    
    @staticmethod
    def sanitize_filename(filename: Optional[str]) -> str:
        """
        Sanitize filename to prevent path traversal attacks.
        
        - Removes path separators
        - Removes dangerous characters
        - Limits length
        """
        if not filename:
            return ""
        
        # Get only the filename, not the path
        filename = str(filename)
        
        # Remove path separators
        filename = filename.replace('/', '').replace('\\', '')
        
        # Remove other dangerous characters
        filename = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename
    
    @classmethod
    def check_sql_injection(cls, value: str) -> bool:
        """
        Check if value contains potential SQL injection patterns.
        
        Returns True if suspicious patterns found.
        """
        if not value:
            return False
        
        value_upper = value.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def check_path_traversal(cls, value: str) -> bool:
        """
        Check if value contains path traversal patterns.
        
        Returns True if suspicious patterns found.
        """
        if not value:
            return False
        
        value_lower = value.lower()
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def sanitize_for_log(value: Any, max_length: int = 200) -> str:
        """Sanitize value for safe logging (remove sensitive patterns)"""
        if value is None:
            return "[None]"
        
        value = str(value)
        
        # Mask potential passwords or tokens
        value = re.sub(r'(password|pwd|token|key|secret)\s*[=:]\s*\S+', 
                       r'\1=[MASKED]', value, flags=re.IGNORECASE)
        
        # Limit length
        if len(value) > max_length:
            value = value[:max_length] + "..."
        
        return value


# Convenience functions
def sanitize(value: Optional[str], max_length: int = 1000) -> str:
    """Sanitize input string"""
    return InputSanitizer.sanitize_string(value, max_length)


def escape_html(value: Optional[str]) -> str:
    """Escape HTML characters"""
    return InputSanitizer.escape_html(value)


def safe_filename(filename: Optional[str]) -> str:
    """Get safe filename"""
    return InputSanitizer.sanitize_filename(filename)

