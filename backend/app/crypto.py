"""Chiffrement des secrets stockés en base (clés Moodle…) à partir de SECRET_KEY."""

import base64
import hashlib

from cryptography.fernet import Fernet

from .config import settings

_fernet = Fernet(base64.urlsafe_b64encode(hashlib.sha256(f"campus:{settings.secret_key}".encode()).digest()))


def encrypt(value: str) -> str:
    return _fernet.encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _fernet.decrypt(value.encode()).decode()
