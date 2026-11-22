"""SQLAlchemy engine, session factory and FastAPI dependency."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_url = get_settings().sqlalchemy_url
engine = create_engine(
    _url,
    pool_pre_ping=True,  # Neon closes idle connections; ping before use
    connect_args={"check_same_thread": False} if _url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables if they don't exist (simple for v1; migrations can come later)."""
    from app.db import models  # noqa: F401  (registers models on Base)

    Base.metadata.create_all(bind=engine)
