"""Save / load the user's Google refresh token (encrypted at rest)."""

from sqlalchemy.orm import Session

from app.db.models import OAuthToken
from app.security.crypto import decrypt, encrypt


def save_refresh_token(db: Session, email: str, refresh_token: str, scopes: list[str]) -> None:
    row = db.get(OAuthToken, email.lower())
    if row is None:
        row = OAuthToken(email=email.lower(), encrypted_refresh_token="")
        db.add(row)
    row.encrypted_refresh_token = encrypt(refresh_token)
    row.scopes = " ".join(sorted(scopes))
    db.commit()


def load_refresh_token(db: Session, email: str) -> tuple[str, list[str]] | None:
    row = db.get(OAuthToken, email.lower())
    if row is None:
        return None
    return decrypt(row.encrypted_refresh_token), row.scopes.split()


def delete_refresh_token(db: Session, email: str) -> None:
    row = db.get(OAuthToken, email.lower())
    if row is not None:
        db.delete(row)
        db.commit()
