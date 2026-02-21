from cryptography.fernet import Fernet
from django.conf import settings


def _get_fernet() -> Fernet:
    key = settings.STAXREAD_FERNET_KEY
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string and return base64-encoded ciphertext."""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext string and return plaintext."""
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()
