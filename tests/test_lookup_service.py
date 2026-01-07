"""
Unit tests for Lookup Service
Tests for caching mechanism and cache invalidation
"""
import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from src.services.lookup_service import LookupService, CacheEntry


class TestCacheEntry:
    """Tests for CacheEntry class"""
    
    def test_cache_entry_not_expired(self):
        """Test that new cache entry is not expired"""
        entry = CacheEntry(data="test", ttl_seconds=300)
        
        assert entry.is_expired() is False
    
    def test_cache_entry_expired(self):
        """Test that old cache entry is expired"""
        entry = CacheEntry(data="test", ttl_seconds=0)
        time.sleep(0.1)  # Wait a bit
        
        assert entry.is_expired() is True
    
    def test_cache_entry_stores_data(self):
        """Test that cache entry stores data correctly"""
        data = {"key": "value", "list": [1, 2, 3]}
        entry = CacheEntry(data=data, ttl_seconds=300)
        
        assert entry.data == data


class TestLookupServiceValidation:
    """Tests for table name validation"""
    
    def setup_method(self):
        """Setup fresh LookupService for each test"""
        self.service = LookupService()
    
    def test_valid_table_names(self):
        """Test that valid table names pass validation"""
        valid_tables = ["factory", "project", "phase", "category", "status"]
        
        for table in valid_tables:
            assert self.service._validate_table_name(table) is True
    
    def test_invalid_table_names(self):
        """Test that invalid table names fail validation"""
        invalid_tables = ["users", "requests", "equipment", "invalid", "DROP TABLE"]
        
        for table in invalid_tables:
            assert self.service._validate_table_name(table) is False


class TestLookupServiceCaching:
    """Tests for caching mechanism"""
    
    def setup_method(self):
        """Setup fresh LookupService for each test"""
        self.service = LookupService()
    
    def test_set_and_get_cache(self):
        """Test setting and getting cache values"""
        self.service._set_cache("test_key", ["value1", "value2"])
        
        result = self.service._get_from_cache("test_key")
        
        assert result == ["value1", "value2"]
    
    def test_get_cache_returns_none_for_missing(self):
        """Test that missing cache returns None"""
        result = self.service._get_from_cache("nonexistent_key")
        
        assert result is None
    
    def test_get_cache_returns_none_for_expired(self):
        """Test that expired cache returns None"""
        # Set cache with 0 TTL
        self.service._cache["test_key"] = CacheEntry(data="test", ttl_seconds=0)
        time.sleep(0.1)
        
        result = self.service._get_from_cache("test_key")
        
        assert result is None
    
    def test_invalidate_specific_cache(self):
        """Test invalidating specific cache"""
        self.service._set_cache("lookup_factory", ["F1", "F2"])
        self.service._set_cache("lookup_project", ["P1", "P2"])
        
        self.service.invalidate_cache("factory")
        
        assert self.service._get_from_cache("lookup_factory") is None
        assert self.service._get_from_cache("lookup_project") is not None
    
    def test_invalidate_all_cache(self):
        """Test invalidating all caches"""
        self.service._set_cache("lookup_factory", ["F1", "F2"])
        self.service._set_cache("lookup_project", ["P1", "P2"])
        self.service._equipment_cache = CacheEntry(data=[], ttl_seconds=300)
        
        self.service.invalidate_cache()
        
        assert len(self.service._cache) == 0
        assert self.service._equipment_cache is None


class TestLookupServiceWithMock:
    """Tests for lookup service with mocked database"""
    
    def setup_method(self):
        """Setup fresh LookupService for each test"""
        self.service = LookupService()
    
    @patch('src.services.lookup_service.get_db')
    def test_get_lookup_values_caches_result(self, mock_get_db):
        """Test that lookup values are cached"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = [("Value1",), ("Value2",)]
        mock_get_db.return_value = mock_db
        
        # First call - should hit database
        result1 = self.service.get_lookup_values("factory")
        
        # Second call - should use cache
        result2 = self.service.get_lookup_values("factory")
        
        assert result1 == ["Value1", "Value2"]
        assert result2 == ["Value1", "Value2"]
        # Database should only be called once
        assert mock_db.fetch_all.call_count == 1
    
    def test_get_lookup_values_invalid_table(self):
        """Test that invalid table returns empty list"""
        result = self.service.get_lookup_values("invalid_table")
        
        assert result == []
    
    @patch('src.services.lookup_service.get_db')
    def test_add_lookup_value_invalidates_cache(self, mock_get_db):
        """Test that adding value invalidates cache"""
        mock_db = Mock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_db.get_cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_db.get_cursor.return_value.__exit__ = Mock(return_value=False)
        mock_get_db.return_value = mock_db
        
        # Pre-populate cache
        self.service._set_cache("lookup_factory", ["Old"])
        
        # Add new value
        self.service.add_lookup_value("factory", "New")
        
        # Cache should be invalidated
        assert self.service._get_from_cache("lookup_factory") is None
    
    def test_add_lookup_value_invalid_table(self):
        """Test that adding to invalid table fails"""
        success, msg = self.service.add_lookup_value("invalid", "value")
        
        assert success is False
        assert "không hợp lệ" in msg


class TestEquipmentCaching:
    """Tests for equipment caching"""
    
    def setup_method(self):
        """Setup fresh LookupService for each test"""
        self.service = LookupService()
    
    @patch('src.services.lookup_service.get_db')
    def test_get_equipment_list_caches_result(self, mock_get_db):
        """Test that equipment list is cached"""
        mock_db = Mock()
        mock_db.fetch_all.return_value = [("EQ001",), ("EQ002",)]
        mock_get_db.return_value = mock_db
        
        # First call
        result1 = self.service.get_equipment_list()
        
        # Second call
        result2 = self.service.get_equipment_list()
        
        assert result1 == ["EQ001", "EQ002"]
        assert result2 == ["EQ001", "EQ002"]
        assert mock_db.fetch_all.call_count == 1
    
    def test_invalidate_equipment_cache(self):
        """Test invalidating equipment cache"""
        self.service._equipment_cache = CacheEntry(data=[], ttl_seconds=300)
        self.service._set_cache("equipment_list", ["EQ001"])
        
        self.service.invalidate_equipment_cache()
        
        assert self.service._equipment_cache is None
        assert self.service._get_from_cache("equipment_list") is None

