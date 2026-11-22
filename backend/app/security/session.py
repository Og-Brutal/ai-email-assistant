"""Signed session cookie + the `current_user` dependency that protects routes.

The cookie only holds the user's email, signed with SECRET_KEY (it can't be forged
or edited). It is httpOnly, so JavaScript in the browser can't read it.
"""

from fastapi import HTTPException, Request, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import get_settings

_SESSION_SALT = "session"
_OAUTH_STATE_SALT = "oauth-state"
OAUTH_STATE_COOKIE = "eaa_oauth_state"
OAUTH_STATE_MAX_AGE = 10 * 60  # login must finish within 10 minutes


def _serializer(salt: str) -> URLSafeTimedSerializer:
    secret = get_settings().secret_key
    if not secret or secret == "change-me":
        raise RuntimeError("SECRET_KEY is not set in backend/.env")
    return URLSafeTimedSerializer(secret, salt=salt)


def _cookie_kwargs() -> dict:
    s = get_settings()
    # Production: frontend (Vercel) and backend (Render) are different sites,
    # so the cookie must be SameSite=None + Secure. Locally Lax is enough.
    return {
        "httponly": True,
        "secure": s.is_production,
        "samesite": "none" if s.is_production else "lax",
        "path": "/",
    }


# ---------- Session ----------
def set_session(response: Response, email: str) -> None:
    s = get_settings()
    value = _serializer(_SESSION_SALT).dumps({"email": email})
    response.set_cookie(
        s.session_cookie_name, value, max_age=s.session_max_age_seconds, **_cookie_kwargs()
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(get_settings().session_cookie_name, **_cookie_kwargs())


def read_session(request: Request) -> str | None:
    s = get_settings()
    raw = request.cookies.get(s.session_cookie_name)
    if not raw:
        return None
    try:
        data = _serializer(_SESSION_SALT).loads(raw, max_age=s.session_max_age_seconds)
    except (BadSignature, SignatureExpired):
        return None
    email = data.get("email")
    # Defense in depth: even a valid cookie must belong to the allowed user.
    if not email or email.lower() != s.allowed_email.lower():
        return None
    return email


def current_user(request: Request) -> str:
    """FastAPI dependency: returns the logged-in email or raises 401."""
    email = read_session(request)
    if not email:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")
    return email


# ---------- OAuth state (CSRF + PKCE verifier during login) ----------
def set_oauth_state(response: Response, state: str, code_verifier: str) -> None:
    value = _serializer(_OAUTH_STATE_SALT).dumps({"state": state, "cv": code_verifier})
    response.set_cookie(
        OAUTH_STATE_COOKIE, value, max_age=OAUTH_STATE_MAX_AGE,
        **{**_cookie_kwargs(), "samesite": "lax"},  # Google redirects back top-level
    )


def clear_oauth_state(response: Response) -> None:
    response.delete_cookie(OAUTH_STATE_COOKIE, path="/")


def read_oauth_state(request: Request) -> dict | None:
    raw = request.cookies.get(OAUTH_STATE_COOKIE)
    if not raw:
        return None
    try:
        return _serializer(_OAUTH_STATE_SALT).loads(raw, max_age=OAUTH_STATE_MAX_AGE)
    except (BadSignature, SignatureExpired):
        return None
