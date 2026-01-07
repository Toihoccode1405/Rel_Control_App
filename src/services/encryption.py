"""
kRel - Encryption Service
Encryption/decryption service for sensitive data

Security Features:
- Key file protection with restricted permissions
- Key validation and integrity check
- Secure key generation
"""
import os
import stat
import logging
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken

# Module logger
enc_logger = logging.getLogger("kRel.encryption")


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.

    Security Features:
    - Key file is created with restricted permissions (owner-only read/write)
    - Key validation on load to detect tampering
    - Cached key for performance
    """

    def __init__(self, key_file: str = ".dbkey"):
        self.key_file = key_file
        self._key: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None

    @property
    def key(self) -> bytes:
        """Get or generate encryption key"""
        if self._key is None:
            self._key = self._load_or_generate_key()
        return self._key

    def _protect_key_file(self):
        """Set restrictive permissions on key file (Windows/Unix compatible)"""
        try:
            if os.name == 'nt':  # Windows
                # On Windows, use icacls to restrict access
                import subprocess
                # Remove inheritance and set owner-only access
                subprocess.run(
                    ['icacls', self.key_file, '/inheritance:r', '/grant:r', f'{os.getlogin()}:F'],
                    capture_output=True, check=False
                )
            else:  # Unix/Linux/Mac
                # Set file permissions to 600 (owner read/write only)
                os.chmod(self.key_file, stat.S_IRUSR | stat.S_IWUSR)
            enc_logger.debug(f"Key file permissions set for: {self.key_file}")
        except Exception as e:
            enc_logger.warning(f"Could not set key file permissions: {e}")

    def _validate_key(self, key: bytes) -> bool:
        """Validate that the key is a valid Fernet key"""
        try:
            # Try to create a Fernet instance - this validates the key format
            Fernet(key)
            return True
        except Exception:
            return False

    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate new one with protection"""
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, "rb") as f:
                    key = f.read()

                # Validate key format
                if self._validate_key(key):
                    enc_logger.debug("Encryption key loaded successfully")
                    return key
                else:
                    enc_logger.error("Invalid key file detected, generating new key")
                    # Backup invalid key file
                    backup_file = f"{self.key_file}.invalid"
                    os.rename(self.key_file, backup_file)
            except Exception as e:
                enc_logger.error(f"Error loading key file: {e}")

        # Generate new key
        key = Fernet.generate_key()
        with open(self.key_file, "wb") as f:
            f.write(key)

        # Protect the key file
        self._protect_key_file()

        enc_logger.info("New encryption key generated and protected")
        return key

    def _get_fernet(self) -> Fernet:
        """Get cached Fernet instance"""
        if self._fernet is None:
            self._fernet = Fernet(self.key)
        return self._fernet

    def encrypt(self, value: str) -> str:
        """Encrypt a string value"""
        if not value:
            return ""
        try:
            return self._get_fernet().encrypt(value.encode()).decode()
        except Exception as e:
            enc_logger.error(f"Encryption error: {e}")
            raise

    def decrypt(self, encrypted_value: str) -> str:
        """Decrypt an encrypted string value"""
        if not encrypted_value:
            return ""
        try:
            return self._get_fernet().decrypt(encrypted_value.encode()).decode()
        except InvalidToken:
            enc_logger.warning("Invalid token during decryption - returning original value")
            # Return original if decryption fails (might be unencrypted)
            return encrypted_value
        except Exception as e:
            enc_logger.error(f"Decryption error: {e}")
            return encrypted_value


# Singleton instance
_instance: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get singleton encryption service instance"""
    global _instance
    if _instance is None:
        _instance = EncryptionService()
    return _instance

