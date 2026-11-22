"""FastAPI dependency that gives a route a ready GmailClient for the logged-in user."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.google_oauth import credentials_from_refresh_token
from app.auth.token_store import load_refresh_token
from app.db.session import get_db
from app.gmail.client import GmailClient
from app.security.crypto import EncryptionError
from app.security.session import current_user


def get_gmail(email: str = Depends(current_user), db: Session = Depends(get_db)) -> GmailClient:
    try:
        stored = load_refresh_token(db, email)
    except EncryptionError:  # FERNET_KEY changed -> old token unreadable
        stored = None
    if stored is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="gmail_not_connected")
    refresh_token, scopes = stored
    return GmailClient(credentials_from_refresh_token(refresh_token, scopes))
