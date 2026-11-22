"""Test setup: safe fake settings so tests never touch real Google or Neon.

Environment variables override backend/.env, so these win over your real keys.
"""

import os
import tempfile

from cryptography.fernet import Fernet

_tmp_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ.update(
    {
        "APP_ENV": "test",
        "DATABASE_URL": f"sqlite:///{_tmp_db}",
        "SECRET_KEY": "test-secret-key-for-signing-cookies-only",
        "FERNET_KEY": Fernet.generate_key().decode(),
        "ALLOWED_EMAIL": "owner@example.com",
        "GOOGLE_CLIENT_ID": "test-client-id",
        "GOOGLE_CLIENT_SECRET": "test-client-secret",
        "FRONTEND_URL": "http://localhost:3000",
    }
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import init_db  # noqa: E402
from app.main import app  # noqa: E402

init_db()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
