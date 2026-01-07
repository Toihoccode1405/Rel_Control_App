"""
kRel - Authentication Service
Handle user login, register, and session management

Security Features:
- Rate limiting for login attempts
- Account lockout after failed attempts
- Strong password policy validation
- Secure session management with timeout
"""
import os
import time
from collections import defaultdict
from configparser import ConfigParser
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.models.user import User
from src.services.database import get_db
from src.services.logger import get_logger, log_audit

# Module logger
logger = get_logger("auth")


class AuthService:
    """
    Authentication and session management service

    Security Features:
    - Rate limiting: Max 5 login attempts per 15 minutes
    - Account lockout: 15 minutes after 5 failed attempts
    - Session timeout: 30 minutes of inactivity
    - Strong password policy enforcement
    """

    _instance: Optional["AuthService"] = None

    # Security settings
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = timedelta(minutes=15)
    RATE_LIMIT_WINDOW = 900  # 15 minutes in seconds
    MIN_PASSWORD_LENGTH = 6

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._current_user: Optional[User] = None
        self._last_activity: Optional[datetime] = None
        self._session_timeout = timedelta(minutes=30)
        self._config_file = "config.ini"

        # Rate limiting and lockout tracking
        self._login_attempts: Dict[str, list] = defaultdict(list)  # username -> [timestamps]
        self._lockout_until: Dict[str, datetime] = {}  # username -> lockout_expiry

    def _clean_old_attempts(self, username: str):
        """Remove login attempts older than rate limit window"""
        cutoff = time.time() - self.RATE_LIMIT_WINDOW
        self._login_attempts[username] = [
            t for t in self._login_attempts[username] if t > cutoff
        ]

    def _is_locked_out(self, username: str) -> bool:
        """Check if account is currently locked out"""
        if username in self._lockout_until:
            if datetime.now() < self._lockout_until[username]:
                return True
            else:
                # Lockout expired, remove it
                del self._lockout_until[username]
                self._login_attempts[username] = []
        return False

    def _record_failed_attempt(self, username: str):
        """Record a failed login attempt and check for lockout"""
        self._login_attempts[username].append(time.time())
        self._clean_old_attempts(username)

        if len(self._login_attempts[username]) >= self.MAX_LOGIN_ATTEMPTS:
            self._lockout_until[username] = datetime.now() + self.LOCKOUT_DURATION
            logger.warning(f"Account '{username}' locked out for {self.LOCKOUT_DURATION.total_seconds()/60} minutes")
            log_audit("ACCOUNT_LOCKED", user=username, details=f"Too many failed attempts")

    def _get_remaining_lockout_time(self, username: str) -> int:
        """Get remaining lockout time in seconds"""
        if username in self._lockout_until:
            remaining = (self._lockout_until[username] - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return 0
    
    def login(self, username: str, password: str) -> tuple[bool, Optional[User], str]:
        """
        Authenticate user with rate limiting and lockout protection.

        Returns: (success, user, message)
        """
        if not username or not password:
            logger.debug("Login attempt with empty credentials")
            return False, None, "Vui lòng nhập đầy đủ thông tin!"

        username_lower = username.lower().strip()

        # Check for account lockout
        if self._is_locked_out(username_lower):
            remaining = self._get_remaining_lockout_time(username_lower)
            minutes = remaining // 60
            seconds = remaining % 60
            logger.warning(f"Login blocked: account '{username}' is locked out")
            return False, None, f"Tài khoản tạm khóa. Thử lại sau {minutes}:{seconds:02d}"

        try:
            db = get_db()
            row = db.fetch_one(
                "SELECT username, password, fullname, email, role FROM users WHERE username = ?",
                (username,)
            )

            if not row:
                self._record_failed_attempt(username_lower)
                logger.warning(f"Login failed: user '{username}' not found")
                log_audit("LOGIN_FAILED", user=username, details="User not found")
                return False, None, "Tài khoản không tồn tại!"

            user = User.from_db_row(row)

            if not User.verify_password(password, user.password):
                self._record_failed_attempt(username_lower)
                attempts_left = self.MAX_LOGIN_ATTEMPTS - len(self._login_attempts.get(username_lower, []))
                logger.warning(f"Login failed: wrong password for '{username}' ({attempts_left} attempts left)")
                log_audit("LOGIN_FAILED", user=username, details="Wrong password")

                if attempts_left > 0:
                    return False, None, f"Sai mật khẩu! Còn {attempts_left} lần thử."
                else:
                    return False, None, "Tài khoản đã bị tạm khóa do đăng nhập sai quá nhiều lần!"

            # Login successful - clear failed attempts
            if username_lower in self._login_attempts:
                del self._login_attempts[username_lower]

            self._current_user = user
            self._last_activity = datetime.now()

            logger.info(f"User '{username}' logged in successfully (role: {user.role})")
            log_audit("LOGIN_SUCCESS", user=username, details=f"Role: {user.role}")

            return True, user, "Đăng nhập thành công!"

        except Exception as e:
            logger.error(f"Login error for '{username}': {str(e)}", exc_info=True)
            return False, None, f"Lỗi kết nối: {str(e)}"

    def logout(self):
        """Clear current session"""
        username = self._current_user.username if self._current_user else "unknown"
        logger.info(f"User '{username}' logged out")
        log_audit("LOGOUT", user=username)
        self._current_user = None
        self._last_activity = None

    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """
        Validate password strength.

        Requirements:
        - Minimum 6 characters
        - At least one letter
        - At least one digit

        Returns: (is_valid, error_message)
        """
        if len(password) < 6:
            return False, "Mật khẩu phải có ít nhất 6 ký tự!"

        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)

        if not has_letter:
            return False, "Mật khẩu phải chứa ít nhất một chữ cái!"

        if not has_digit:
            return False, "Mật khẩu phải chứa ít nhất một chữ số!"

        return True, ""

    def register(self, username: str, password: str, fullname: str = "",
                 email: str = "", role: str = "Operator") -> tuple[bool, str]:
        """
        Register new user with password policy enforcement.

        Returns: (success, message)
        """
        if not username or not password:
            return False, "Vui lòng nhập đầy đủ thông tin!"

        # Validate password strength
        is_valid, error_msg = self.validate_password(password)
        if not is_valid:
            return False, error_msg

        try:
            db = get_db()

            # Check if username exists
            existing = db.fetch_one(
                "SELECT username FROM users WHERE username = ?",
                (username,)
            )
            if existing:
                logger.warning(f"Registration failed: username '{username}' already exists")
                return False, "Tài khoản đã tồn tại!"

            # Create new user
            hashed_password = User.hash_password(password)
            user = User(
                username=username,
                password=hashed_password,
                fullname=fullname,
                email=email,
                role=role
            )

            with db.get_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO users (username, password, fullname, email, role) VALUES (?, ?, ?, ?, ?)",
                    user.to_tuple()
                )

            logger.info(f"New user registered: '{username}' (role: {role})")
            log_audit("USER_REGISTER", user=username, details=f"Role: {role}, Name: {fullname}")

            return True, "Đăng ký thành công!"

        except Exception as e:
            logger.error(f"Registration error for '{username}': {str(e)}", exc_info=True)
            return False, f"Lỗi: {str(e)}"
    
    def get_current_user(self) -> Optional[User]:
        """Get currently logged in user"""
        if self.is_session_expired():
            self.logout()
            return None
        return self._current_user
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in and session is valid"""
        return self._current_user is not None and not self.is_session_expired()
    
    def is_session_expired(self) -> bool:
        """Check if session has expired"""
        if self._last_activity is None:
            return True
        return datetime.now() - self._last_activity > self._session_timeout
    
    def refresh_session(self):
        """Update last activity time"""
        if self._current_user:
            self._last_activity = datetime.now()
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get current user info as dict"""
        user = self.get_current_user()
        if user:
            return {
                "name": user.fullname or user.username,
                "role": user.role,
                "username": user.username
            }
        return None
    
    def save_remember_me(self, username: str, remember: bool):
        """Save or clear remembered username"""
        config = ConfigParser()
        if os.path.exists(self._config_file):
            config.read(self._config_file, encoding="utf-8")
        
        if not config.has_section("login"):
            config.add_section("login")
        
        if remember:
            config["login"]["user"] = username
        elif config.has_option("login", "user"):
            config.remove_option("login", "user")
        
        with open(self._config_file, "w", encoding="utf-8") as f:
            config.write(f)
    
    def get_remembered_username(self) -> str:
        """Get remembered username if any"""
        config = ConfigParser()
        if os.path.exists(self._config_file):
            config.read(self._config_file, encoding="utf-8")
            if config.has_section("login"):
                return config["login"].get("user", "")
        return ""
    
    def change_password(self, username: str, old_password: str, 
                        new_password: str) -> tuple[bool, str]:
        """Change user password"""
        try:
            db = get_db()
            row = db.fetch_one(
                "SELECT password FROM users WHERE username = ?",
                (username,)
            )
            
            if not row:
                return False, "Tài khoản không tồn tại!"
            
            if not User.verify_password(old_password, row[0]):
                return False, "Mật khẩu cũ không đúng!"
            
            new_hash = User.hash_password(new_password)
            
            with db.get_cursor() as cursor:
                cursor.execute(
                    "UPDATE users SET password = ? WHERE username = ?",
                    (new_hash, username)
                )
            
            return True, "Đổi mật khẩu thành công!"
            
        except Exception as e:
            return False, f"Lỗi: {str(e)}"


# Global instance getter  
def get_auth() -> AuthService:
    """Get singleton auth service instance"""
    return AuthService()

