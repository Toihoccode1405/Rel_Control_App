"""
Unit tests for Encryption Service
Tests for key management, encryption/decryption, and key file protection
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

from src.services.encryption import EncryptionService, get_encryption_service


class TestEncryptionServiceKeyManagement:
    """Tests for key management"""
    
    def setup_method(self):
        """Setup with temporary key file"""
        self.temp_dir = tempfile.mkdtemp()
        self.key_file = os.path.join(self.temp_dir, ".testkey")
        self.service = EncryptionService(key_file=self.key_file)
    
    def teardown_method(self):
        """Cleanup temporary files"""
        if os.path.exists(self.key_file):
            os.remove(self.key_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_generates_new_key_if_not_exists(self):
        """Test that new key is generated if file doesn't exist"""
        assert not os.path.exists(self.key_file)
        
        key = self.service.key
        
        assert key is not None
        assert len(key) > 0
        assert os.path.exists(self.key_file)
    
    def test_loads_existing_key(self):
        """Test that existing key is loaded"""
        # Generate key first
        key1 = self.service.key
        
        # Create new service instance
        service2 = EncryptionService(key_file=self.key_file)
        key2 = service2.key
        
        assert key1 == key2
    
    def test_key_is_cached(self):
        """Test that key is cached after first load"""
        key1 = self.service.key
        key2 = self.service.key
        
        assert key1 is key2  # Same object reference


class TestKeyValidation:
    """Tests for key validation"""
    
    def setup_method(self):
        """Setup with temporary key file"""
        self.temp_dir = tempfile.mkdtemp()
        self.key_file = os.path.join(self.temp_dir, ".testkey")
        self.service = EncryptionService(key_file=self.key_file)
    
    def teardown_method(self):
        """Cleanup temporary files"""
        for f in [self.key_file, f"{self.key_file}.invalid"]:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_validate_valid_key(self):
        """Test that valid Fernet key passes validation"""
        from cryptography.fernet import Fernet
        valid_key = Fernet.generate_key()
        
        assert self.service._validate_key(valid_key) is True
    
    def test_validate_invalid_key(self):
        """Test that invalid key fails validation"""
        invalid_key = b"not_a_valid_fernet_key"
        
        assert self.service._validate_key(invalid_key) is False
    
    def test_invalid_key_file_is_backed_up(self):
        """Test that invalid key file is backed up and new key generated"""
        # Write invalid key to file
        with open(self.key_file, "wb") as f:
            f.write(b"invalid_key_data")
        
        # Load key - should detect invalid and generate new
        key = self.service._load_or_generate_key()
        
        assert key is not None
        assert self.service._validate_key(key) is True
        assert os.path.exists(f"{self.key_file}.invalid")


class TestEncryptDecrypt:
    """Tests for encryption and decryption"""
    
    def setup_method(self):
        """Setup with temporary key file"""
        self.temp_dir = tempfile.mkdtemp()
        self.key_file = os.path.join(self.temp_dir, ".testkey")
        self.service = EncryptionService(key_file=self.key_file)
    
    def teardown_method(self):
        """Cleanup temporary files"""
        if os.path.exists(self.key_file):
            os.remove(self.key_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_encrypt_decrypt_roundtrip(self):
        """Test that encrypt/decrypt returns original value"""
        original = "Hello, World! 你好世界"
        
        encrypted = self.service.encrypt(original)
        decrypted = self.service.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_returns_different_value(self):
        """Test that encrypted value is different from original"""
        original = "secret_password"
        
        encrypted = self.service.encrypt(original)
        
        assert encrypted != original
    
    def test_encrypt_empty_string(self):
        """Test encrypting empty string"""
        assert self.service.encrypt("") == ""
    
    def test_decrypt_empty_string(self):
        """Test decrypting empty string"""
        assert self.service.decrypt("") == ""
    
    def test_decrypt_invalid_returns_original(self):
        """Test that decrypting invalid data returns original"""
        invalid_data = "not_encrypted_data"
        
        result = self.service.decrypt(invalid_data)
        
        assert result == invalid_data
    
    def test_encrypt_special_characters(self):
        """Test encrypting special characters"""
        special = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        
        encrypted = self.service.encrypt(special)
        decrypted = self.service.decrypt(encrypted)
        
        assert decrypted == special
    
    def test_encrypt_unicode(self):
        """Test encrypting unicode characters"""
        unicode_text = "日本語 한국어 العربية"
        
        encrypted = self.service.encrypt(unicode_text)
        decrypted = self.service.decrypt(encrypted)
        
        assert decrypted == unicode_text


class TestFernetCaching:
    """Tests for Fernet instance caching"""
    
    def setup_method(self):
        """Setup with temporary key file"""
        self.temp_dir = tempfile.mkdtemp()
        self.key_file = os.path.join(self.temp_dir, ".testkey")
        self.service = EncryptionService(key_file=self.key_file)
    
    def teardown_method(self):
        """Cleanup temporary files"""
        if os.path.exists(self.key_file):
            os.remove(self.key_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def test_fernet_is_cached(self):
        """Test that Fernet instance is cached"""
        fernet1 = self.service._get_fernet()
        fernet2 = self.service._get_fernet()
        
        assert fernet1 is fernet2


class TestSingletonPattern:
    """Tests for singleton pattern"""
    
    def test_get_encryption_service_returns_singleton(self):
        """Test that get_encryption_service returns same instance"""
        # Note: This modifies global state
        service1 = get_encryption_service()
        service2 = get_encryption_service()
        
        assert service1 is service2

