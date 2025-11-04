"""Encryption utilities for sensitive data like API keys."""

import base64
from hashlib import sha256
from cryptography.fernet import Fernet
from ..config import Config


def get_encryption_key():
    """Get or generate encryption key for API keys.
    
    Returns:
        Fernet encryption key
    """
    key = Config.SECRET_KEY.encode('utf-8')
    # Hash to get exactly 32 bytes, then base64 encode for Fernet
    hashed = sha256(key).digest()
    return Fernet(base64.urlsafe_b64encode(hashed))


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for storage.
    
    Args:
        api_key: Plain text API key
        
    Returns:
        Encrypted API key as string
    """
    if not api_key:
        return ''
    
    fernet = get_encryption_key()
    encrypted = fernet.encrypt(api_key.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key from storage.
    
    Args:
        encrypted_key: Encrypted API key string
        
    Returns:
        Decrypted API key as plain text
    """
    if not encrypted_key:
        return ''
    
    try:
        fernet = get_encryption_key()
        decrypted = fernet.decrypt(encrypted_key.encode('utf-8'))
        return decrypted.decode('utf-8')
    except Exception as e:
        print(f"Error decrypting API key: {e}")
        return ''