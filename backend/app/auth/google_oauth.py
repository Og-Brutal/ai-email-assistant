"""Google OAuth 2.0 (Authorization Code flow + PKCE) helpers."""

import os
import secrets

# Google may return scopes in a different order/alias ("email" vs userinfo.email).
# Without this, oauthlib raises "Scope has changed". We check required scopes ourselves.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from app.config import get_settings

TOKEN_URI = "https://oauth2.googleapis.com/token"

# Least privilege: identity + read/label/draft + send. No full mail delete.
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
]
REQUIRED_GMAIL_SCOPES = {
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
}


def _client_config() -> dict:
    s = get_settings()
    return {
        "web": {
            "client_id": s.google_client_id,
            "client_secret": s.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": TOKEN_URI,
            "redirect_uris": [s.google_redirect_uri],
        }
    }


def _flow(state: str | None = None, code_verifier: str | None = None) -> Flow:
    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = get_settings().google_redirect_uri
    return flow


def build_authorization_url() -> tuple[str, str, str]:
    """Returns (url, state, code_verifier). state+verifier are kept in a signed cookie."""
    code_verifier = secrets.token_urlsafe(64)
    flow = _flow(code_verifier=code_verifier)
    url, state = flow.authorization_url(
        access_type="offline",  # we need a refresh token
        prompt="consent",  # always return a refresh token
        include_granted_scopes="false",
    )
    return url, state, code_verifier


def exchange_code(code: str, state: str, code_verifier: str) -> Credentials:
    flow = _flow(state=state, code_verifier=code_verifier)
    flow.fetch_token(code=code)
    return flow.credentials


def verified_email(creds: Credentials) -> str:
    """Read the email from Google's signed ID token (verified signature + audience)."""
    info = id_token.verify_oauth2_token(
        creds.id_token, GoogleRequest(), get_settings().google_client_id
    )
    if not info.get("email_verified"):
        raise ValueError("Google email is not verified")
    return info["email"]


def credentials_from_refresh_token(refresh_token: str, scopes: list[str]) -> Credentials:
    """Rebuild credentials; google-auth refreshes the short-lived access token itself."""
    s = get_settings()
    return Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri=TOKEN_URI,
        client_id=s.google_client_id,
        client_secret=s.google_client_secret,
        scopes=scopes,
    )
