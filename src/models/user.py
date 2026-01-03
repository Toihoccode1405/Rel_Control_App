"""
kRel - User Model
"""
from dataclasses import dataclass, field
from typing import Optional
import hashlib

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


@dataclass
class User:
    """User entity model"""
    username: str
    password: str = ""  # Hashed password
    fullname: str = ""
    email: str = ""
    role: str = "Operator"
    
    @classmethod
    def from_db_row(cls, row: tuple) -> "User":
        """Create User from database row"""
        return cls(
            username=row[0],
            password=row[1] if len(row) > 1 else "",
            fullname=row[2] if len(row) > 2 else "",
            email=row[3] if len(row) > 3 else "",
            role=row[4] if len(row) > 4 else "Operator"
        )
    
    def to_tuple(self) -> tuple:
        """Convert to tuple for database insert"""
        return (self.username, self.password, self.fullname, self.email, self.role)
    
    @staticmethod
    def hash_password(plain_password: str, use_bcrypt: bool = True) -> str:
        """Hash password using bcrypt (preferred) or SHA256 (fallback)"""
        if use_bcrypt and HAS_BCRYPT:
            return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()
        return hashlib.sha256(plain_password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        if HAS_BCRYPT and hashed_password.startswith("$2"):
            # bcrypt hash
            return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        # SHA256 fallback
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    
    def is_super(self) -> bool:
        """Check if user has super admin role"""
        return self.role == "Super"
    
    def is_manager_or_above(self) -> bool:
        """Check if user has manager or super role"""
        return self.role in ("Manager", "Super")
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users"""
        return self.is_super()
    
    def can_edit_settings(self) -> bool:
        """Check if user can edit system settings"""
        return self.is_manager_or_above()

