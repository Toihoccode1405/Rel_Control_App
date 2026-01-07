"""
Unit tests for Authentication Service
Tests for rate limiting, password policy, and account lockout
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.services.auth import AuthService


class TestPasswordValidation:
    """Tests for password validation"""
    
    def test_password_too_short(self):
        """Test that short passwords are rejected"""
        is_valid, msg = AuthService.validate_password("abc")
        assert is_valid is False
        assert "6" in msg  # Should mention minimum length
    
    def test_password_no_letter(self):
        """Test that passwords without letters are rejected"""
        is_valid, msg = AuthService.validate_password("123456")
        assert is_valid is False
        assert "chữ cái" in msg
    
    def test_password_no_digit(self):
        """Test that passwords without digits are rejected"""
        is_valid, msg = AuthService.validate_password("abcdef")
        assert is_valid is False
        assert "chữ số" in msg
    
    def test_valid_password(self):
        """Test that valid passwords pass"""
        is_valid, msg = AuthService.validate_password("abc123")
        assert is_valid is True
        assert msg == ""
    
    def test_valid_password_complex(self):
        """Test that complex passwords pass"""
        is_valid, msg = AuthService.validate_password("MyP@ssw0rd!")
        assert is_valid is True


class TestRateLimiting:
    """Tests for login rate limiting"""
    
    def setup_method(self):
        """Setup fresh AuthService for each test"""
        # Reset singleton
        AuthService._instance = None
        self.auth = AuthService()
    
    def test_clean_old_attempts(self):
        """Test that old attempts are cleaned up"""
        username = "testuser"
        # Add old attempts (older than rate limit window)
        old_time = time.time() - 1000  # 1000 seconds ago
        self.auth._login_attempts[username] = [old_time, old_time + 1]
        
        self.auth._clean_old_attempts(username)
        
        assert len(self.auth._login_attempts[username]) == 0
    
    def test_record_failed_attempt(self):
        """Test that failed attempts are recorded"""
        username = "testuser"
        
        self.auth._record_failed_attempt(username)
        
        assert len(self.auth._login_attempts[username]) == 1
    
    def test_lockout_after_max_attempts(self):
        """Test that account is locked after max attempts"""
        username = "testuser"
        
        # Record max attempts
        for _ in range(AuthService.MAX_LOGIN_ATTEMPTS):
            self.auth._record_failed_attempt(username)
        
        assert self.auth._is_locked_out(username) is True
    
    def test_lockout_expires(self):
        """Test that lockout expires after duration"""
        username = "testuser"
        
        # Set lockout to past time
        self.auth._lockout_until[username] = datetime.now() - timedelta(seconds=1)
        
        assert self.auth._is_locked_out(username) is False
    
    def test_get_remaining_lockout_time(self):
        """Test getting remaining lockout time"""
        username = "testuser"
        
        # Set lockout to 5 minutes from now
        self.auth._lockout_until[username] = datetime.now() + timedelta(minutes=5)
        
        remaining = self.auth._get_remaining_lockout_time(username)
        
        assert 290 <= remaining <= 300  # About 5 minutes


class TestLoginWithMock:
    """Tests for login with mocked database"""
    
    def setup_method(self):
        """Setup fresh AuthService for each test"""
        AuthService._instance = None
        self.auth = AuthService()
    
    def test_login_empty_credentials(self):
        """Test login with empty credentials"""
        success, user, msg = self.auth.login("", "")
        
        assert success is False
        assert user is None
        assert "đầy đủ" in msg
    
    def test_login_empty_password(self):
        """Test login with empty password"""
        success, user, msg = self.auth.login("user", "")
        
        assert success is False
        assert user is None
    
    @patch('src.services.auth.get_db')
    def test_login_user_not_found(self, mock_get_db):
        """Test login with non-existent user"""
        mock_db = Mock()
        mock_db.fetch_one.return_value = None
        mock_get_db.return_value = mock_db
        
        success, user, msg = self.auth.login("nonexistent", "password")
        
        assert success is False
        assert "không tồn tại" in msg
    
    def test_login_blocked_when_locked_out(self):
        """Test that login is blocked when account is locked"""
        username = "lockeduser"
        
        # Lock the account
        self.auth._lockout_until[username] = datetime.now() + timedelta(minutes=10)
        
        success, user, msg = self.auth.login(username, "password")
        
        assert success is False
        assert "tạm khóa" in msg


class TestSessionManagement:
    """Tests for session management"""
    
    def setup_method(self):
        """Setup fresh AuthService for each test"""
        AuthService._instance = None
        self.auth = AuthService()
    
    def test_logout_clears_session(self):
        """Test that logout clears the session"""
        # Setup mock user
        mock_user = Mock()
        mock_user.username = "testuser"
        self.auth._current_user = mock_user
        self.auth._last_activity = datetime.now()
        
        self.auth.logout()
        
        assert self.auth._current_user is None
        assert self.auth._last_activity is None
    
    def test_session_expired_when_no_user(self):
        """Test that session is expired when no user"""
        self.auth._current_user = None

        assert self.auth.is_session_expired() is True

