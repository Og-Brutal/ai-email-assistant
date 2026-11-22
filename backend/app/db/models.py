"""Database tables."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OAuthToken(Base):
    """Google refresh token for a user, stored ENCRYPTED (never plain text)."""

    __tablename__ = "oauth_tokens"

    email: Mapped[str] = mapped_column(String(320), primary_key=True)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
