"""
Unit tests for Database Service
Tests for connection health check, timeout, and thread safety
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import threading

from src.services.database import DatabaseService


class TestDatabaseServiceSingleton:
    """Tests for singleton pattern"""
    
    def test_singleton_returns_same_instance(self):
        """Test that singleton returns same instance"""
        # Reset singleton for test
        DatabaseService._instance = None
        
        db1 = DatabaseService()
        db2 = DatabaseService()
        
        assert db1 is db2
    
    def test_singleton_thread_safe(self):
        """Test that singleton is thread-safe"""
        DatabaseService._instance = None
        instances = []
        
        def get_instance():
            instances.append(DatabaseService())
        
        threads = [threading.Thread(target=get_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All instances should be the same
        assert all(inst is instances[0] for inst in instances)


class TestEncryptionKeyCaching:
    """Tests for encryption key caching"""
    
    def setup_method(self):
        """Setup fresh DatabaseService for each test"""
        DatabaseService._instance = None
        self.db = DatabaseService()
    
    @patch('src.services.database.os.path.exists')
    @patch('builtins.open', create=True)
    @patch('src.services.database.Fernet')
    def test_encryption_key_is_cached(self, mock_fernet, mock_open, mock_exists):
        """Test that encryption key is cached after first load"""
        mock_exists.return_value = True
        mock_open.return_value.__enter__ = Mock(return_value=Mock(read=Mock(return_value=b'test_key')))
        mock_open.return_value.__exit__ = Mock(return_value=False)
        
        # First call
        key1 = self.db._get_encryption_key()
        
        # Second call - should use cached key
        key2 = self.db._get_encryption_key()
        
        assert key1 == key2
        # File should only be read once
        assert mock_open.call_count == 1


class TestConnectionHealthCheck:
    """Tests for connection health check"""
    
    def setup_method(self):
        """Setup fresh DatabaseService for each test"""
        DatabaseService._instance = None
        self.db = DatabaseService()
    
    def test_is_connection_healthy_returns_false_when_no_connection(self):
        """Test health check returns False when no connection"""
        self.db._connection = None
        
        assert self.db._is_connection_healthy() is False
    
    def test_is_connection_healthy_with_valid_connection(self):
        """Test health check with valid mock connection"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn.cursor.return_value = mock_cursor
        self.db._connection = mock_conn
        
        result = self.db._is_connection_healthy()
        
        assert result is True
        mock_cursor.execute.assert_called_with("SELECT 1")
    
    def test_is_connection_healthy_returns_false_on_error(self):
        """Test health check returns False on database error"""
        mock_conn = Mock()
        mock_conn.cursor.side_effect = Exception("Connection lost")
        self.db._connection = mock_conn
        
        result = self.db._is_connection_healthy()
        
        assert result is False
    
    def test_should_health_check_based_on_interval(self):
        """Test that health check is triggered based on interval"""
        # Just checked
        self.db._last_health_check = time.time()
        assert self.db._should_health_check() is False
        
        # Long time ago
        self.db._last_health_check = time.time() - 1000
        assert self.db._should_health_check() is True


class TestConnectionManagement:
    """Tests for connection management"""
    
    def setup_method(self):
        """Setup fresh DatabaseService for each test"""
        DatabaseService._instance = None
        self.db = DatabaseService()
    
    def test_close_connection_clears_connection(self):
        """Test that close clears the connection"""
        mock_conn = Mock()
        self.db._connection = mock_conn
        
        self.db.close()
        
        assert self.db._connection is None
        mock_conn.close.assert_called_once()
    
    def test_close_connection_handles_error(self):
        """Test that close handles errors gracefully"""
        mock_conn = Mock()
        mock_conn.close.side_effect = Exception("Error")
        self.db._connection = mock_conn
        
        # Should not raise
        self.db.close()
        
        assert self.db._connection is None
    
    def test_is_connected_returns_false_when_no_connection(self):
        """Test is_connected returns False when no connection"""
        self.db._connection = None
        
        assert self.db.is_connected() is False


class TestDatabaseServiceConstants:
    """Tests for service constants"""
    
    def test_connection_timeout_is_reasonable(self):
        """Test that connection timeout is set"""
        assert DatabaseService.CONNECTION_TIMEOUT > 0
        assert DatabaseService.CONNECTION_TIMEOUT <= 30
    
    def test_query_timeout_is_reasonable(self):
        """Test that query timeout is set"""
        assert DatabaseService.QUERY_TIMEOUT > 0
        assert DatabaseService.QUERY_TIMEOUT <= 60
    
    def test_health_check_interval_is_reasonable(self):
        """Test that health check interval is set"""
        assert DatabaseService.HEALTH_CHECK_INTERVAL > 0
        assert DatabaseService.HEALTH_CHECK_INTERVAL <= 300

