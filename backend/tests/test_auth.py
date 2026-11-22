from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

from app.auth import google_oauth
from app.config import get_settings
from app.db.models import OAuthToken
from app.db.session import SessionLocal
from app.security.session import OAUTH_STATE_COOKIE

ALL_SCOPES = google_oauth.SCOPES


def _start_login(client) -> str:
    """Hit /auth/login, return the state Google would echo back."""
    r = client.get("/auth/login", follow_redirects=False)
    assert r.status_code == 302
    url = urlparse(r.headers["location"])
    assert url.netloc == "accounts.google.com"
    q = parse_qs(url.query)
    assert q["access_type"] == ["offline"]
    assert q["code_challenge_method"] == ["S256"]  # PKCE on
    assert OAUTH_STATE_COOKIE in r.cookies
    return q["state"][0]


def _fake_google(monkeypatch, email: str, scopes=ALL_SCOPES, refresh="1//refresh-abc"):
    creds = SimpleNamespace(refresh_token=refresh, granted_scopes=scopes, scopes=scopes)
    monkeypatch.setattr(google_oauth, "exchange_code", lambda code, state, cv: creds)
    monkeypatch.setattr(google_oauth, "verified_email", lambda c: email)


def _error_of(response) -> str | None:
    return parse_qs(urlparse(response.headers["location"]).query).get("error", [None])[0]


def test_me_requires_login(client):
    assert client.get("/auth/me").status_code == 401


def test_forged_session_cookie_rejected(client):
    client.cookies.set(get_settings().session_cookie_name, "fake.value.here")
    assert client.get("/auth/me").status_code == 401


def test_callback_rejects_wrong_state(client, monkeypatch):
    _fake_google(monkeypatch, "owner@example.com")
    _start_login(client)
    r = client.get("/auth/callback?code=abc&state=attacker", follow_redirects=False)
    assert _error_of(r) == "invalid_state"


def test_callback_rejects_missing_state_cookie(client, monkeypatch):
    _fake_google(monkeypatch, "owner@example.com")
    r = client.get("/auth/callback?code=abc&state=x", follow_redirects=False)
    assert _error_of(r) == "invalid_state"


def test_callback_rejects_other_account(client, monkeypatch):
    _fake_google(monkeypatch, "stranger@example.com")
    state = _start_login(client)
    r = client.get(f"/auth/callback?code=abc&state={state}", follow_redirects=False)
    assert _error_of(r) == "not_allowed"
    assert client.get("/auth/me").status_code == 401


def test_callback_rejects_missing_gmail_scopes(client, monkeypatch):
    _fake_google(monkeypatch, "owner@example.com", scopes=["openid"])
    state = _start_login(client)
    r = client.get(f"/auth/callback?code=abc&state={state}", follow_redirects=False)
    assert _error_of(r) == "missing_scopes"


def test_successful_login_stores_encrypted_token(client, monkeypatch):
    _fake_google(monkeypatch, "Owner@Example.com", refresh="1//super-secret")
    state = _start_login(client)
    r = client.get(f"/auth/callback?code=abc&state={state}", follow_redirects=False)
    assert r.headers["location"] == "http://localhost:3000/inbox"

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json() == {"email": "Owner@Example.com", "gmail_connected": True}

    with SessionLocal() as db:
        row = db.get(OAuthToken, "owner@example.com")
        assert row is not None
        assert "super-secret" not in row.encrypted_refresh_token

    # state cookie is single-use
    again = client.get(f"/auth/callback?code=abc&state={state}", follow_redirects=False)
    assert _error_of(again) == "invalid_state"


def test_logout_clears_session(client, monkeypatch):
    _fake_google(monkeypatch, "owner@example.com")
    state = _start_login(client)
    client.get(f"/auth/callback?code=abc&state={state}", follow_redirects=False)
    assert client.get("/auth/me").status_code == 200
    client.post("/auth/logout")
    assert client.get("/auth/me").status_code == 401


@pytest.fixture(autouse=True)
def _clean_tokens():
    yield
    with SessionLocal() as db:
        db.query(OAuthToken).delete()
        db.commit()
