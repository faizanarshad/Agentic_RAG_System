"""Encryption at rest for sensitive fields (AES-256-GCM).

The key comes from DATA_ENCRYPTION_KEY (base64, 32 bytes) or, if unset, a key file created once in the
platform data folder with owner-only permissions. Keep the key out of backups of the database itself.
"""

import base64
import os
import secrets
import threading
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from core.config import settings

PREFIX = "enc:v1:"
_key: Optional[bytes] = None
_lock = threading.Lock()


def _load_key() -> bytes:
    global _key
    with _lock:
        if _key is not None:
            return _key
        configured = os.getenv("DATA_ENCRYPTION_KEY", "").strip()
        if configured:
            key = base64.urlsafe_b64decode(configured + "=" * (-len(configured) % 4))
            if len(key) != 32:
                raise ValueError("DATA_ENCRYPTION_KEY must decode to 32 bytes")
        else:
            os.makedirs(settings.PLATFORM_DATA_DIR, exist_ok=True)
            path = os.path.join(settings.PLATFORM_DATA_DIR, "encryption.key")
            if not os.path.exists(path):
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w") as f:
                    f.write(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())
            with open(path) as f:
                key = base64.urlsafe_b64decode(f.read().strip())
        _key = key
        return key


def encrypt(value: Optional[str]) -> Optional[str]:
    if value is None or value.startswith(PREFIX):
        return value
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(_load_key()).encrypt(nonce, value.encode("utf-8"), None)
    return PREFIX + base64.urlsafe_b64encode(nonce + ciphertext).decode()


def decrypt(value: Optional[str]) -> Optional[str]:
    """Decrypt a stored value; plaintext from before encryption was introduced is returned unchanged."""
    if not value or not value.startswith(PREFIX):
        return value
    raw = base64.urlsafe_b64decode(value[len(PREFIX):])
    return AESGCM(_load_key()).decrypt(raw[:12], raw[12:], None).decode("utf-8")
