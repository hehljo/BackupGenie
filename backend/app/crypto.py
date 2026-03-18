"""
Credential encryption using Fernet (AES-128-CBC with HMAC).
Derives encryption key from SECRET_KEY via PBKDF2.
"""
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Fixed salt - changing this invalidates all encrypted credentials.
# This is acceptable because the SECRET_KEY provides the entropy.
_SALT = b'backupgenie-credential-store-v1'
_fernet = None


def _get_fernet():
    """Lazy-init Fernet cipher from SECRET_KEY."""
    global _fernet
    if _fernet is None:
        from app.config import Config
        secret = Config.SECRET_KEY
        if not secret or secret == 'dev-secret-key-change-in-production':
            raise RuntimeError(
                "SECRET_KEY not set or using default. "
                "Set a strong SECRET_KEY before storing credentials."
            )
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=_SALT,
            iterations=480_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(secret.encode('utf-8')))
        _fernet = Fernet(key)
    return _fernet


def encrypt_value(plaintext):
    """Encrypt a string value. Returns base64-encoded ciphertext."""
    if not plaintext:
        return ''
    return _get_fernet().encrypt(plaintext.encode('utf-8')).decode('utf-8')


def decrypt_value(ciphertext):
    """Decrypt a base64-encoded ciphertext. Returns plaintext string."""
    if not ciphertext:
        return ''
    try:
        return _get_fernet().decrypt(ciphertext.encode('utf-8')).decode('utf-8')
    except Exception:
        # If decryption fails (wrong key, corrupted data), return empty
        return ''
