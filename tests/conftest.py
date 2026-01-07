"""
Pytest configuration and fixtures
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test"""
    # Reset DatabaseService singleton
    from src.services.database import DatabaseService
    DatabaseService._instance = None
    DatabaseService._connection = None
    
    # Reset AuthService singleton
    from src.services.auth import AuthService
    AuthService._instance = None
    
    yield
    
    # Cleanup after test
    DatabaseService._instance = None
    AuthService._instance = None


@pytest.fixture
def mock_db_connection():
    """Fixture for mocked database connection"""
    from unittest.mock import Mock, MagicMock
    
    mock_conn = Mock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    return mock_conn, mock_cursor

