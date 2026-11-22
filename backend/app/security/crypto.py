"""Symmetric encryption for secrets stored in the database (Google refresh token)."""

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


class EncryptionError(Exception):
    pass


def _fernet() -> Fernet:
    key = get_settings().fernet_key
    if not key or key == "change-me":
        raise EncryptionError("FERNET_KEY is not set in backend/.env")
    return Fernet(key.encode())


def encrypt(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken as exc:  # wrong key or tampered data
        raise EncryptionError("Could not decrypt stored secret") from exc
