"""App settings, loaded from environment variables / backend/.env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    # Always read backend/.env, no matter which folder uvicorn is started from.
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # App
    app_env: str = "development"
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    allowed_email: str = ""
    secret_key: str = ""
    fernet_key: str = ""

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Gemini
    google_api_key: str = ""

    # Qdrant
    qdrant_url: str = ""
    qdrant_api_key: str = ""

    # Postgres (empty -> local SQLite file, handy for tests/offline dev)
    database_url: str = ""

    # Session cookie
    session_cookie_name: str = "eaa_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 7  # 7 days

    def missing_required(self) -> list[str]:
        """Names of settings the app can't run without (checked at startup)."""
        required = {
            "SECRET_KEY": self.secret_key,
            "FERNET_KEY": self.fernet_key,
            "ALLOWED_EMAIL": self.allowed_email,
            "GOOGLE_CLIENT_ID": self.google_client_id,
            "GOOGLE_CLIENT_SECRET": self.google_client_secret,
        }
        return [name for name, value in required.items() if not value or value == "change-me"]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def sqlalchemy_url(self) -> str:
        """Neon gives 'postgresql://...'; SQLAlchemy needs the psycopg driver name."""
        url = self.database_url or "sqlite:///./local.db"
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
