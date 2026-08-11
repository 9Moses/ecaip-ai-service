from functools import lru_cache

from cryptography.fernet import Fernet

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_cipher() -> Fernet:
    if not settings.bi_credentials_encryption_key:
        raise RuntimeError(
            """BI_CREDENTIALS_ENCRYPTION_KEY is not set —
            generate one with """
            """python -c \"from cryptography.fernet import Fernet;
            print(Fernet.generate_key().decode())\""""
        )
    return Fernet(settings.bi_credentials_encryption_key.encode())


def encrypt_credentials(plaintext: str) -> bytes:
    return get_cipher().encrypt(plaintext.encode())


def decrypt_credentials(ciphertext: bytes) -> str:
    return get_cipher().decrypt(ciphertext).decode()
