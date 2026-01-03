"""
kRel - Encryption Service
Encryption/decryption service for sensitive data
"""
import os
from cryptography.fernet import Fernet


class EncryptionService:
    """Service for encrypting and decrypting sensitive data"""
    
    def __init__(self, key_file: str = ".dbkey"):
        self.key_file = key_file
        self._key = None
    
    @property
    def key(self) -> bytes:
        """Get or generate encryption key"""
        if self._key is None:
            self._key = self._load_or_generate_key()
        return self._key
    
    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate new one"""
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            return key
    
    def encrypt(self, value: str) -> str:
        """Encrypt a string value"""
        if not value:
            return ""
        f = Fernet(self.key)
        return f.encrypt(value.encode()).decode()
    
    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt an encrypted string value"""
        if not encrypted_value:
            return ""
        try:
            f = Fernet(self.key)
            return f.decrypt(encrypted_value.encode()).decode()
        except Exception:
            # Return original if decryption fails (might be unencrypted)
            return encrypted_value


# Singleton instance
_instance = None


def get_encryption_service() -> EncryptionService:
    """Get singleton encryption service instance"""
    global _instance
    if _instance is None:
        _instance = EncryptionService()
    return _instance

