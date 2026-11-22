"""/auth routes: login, Google callback, current user, logout."""

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth import google_oauth
from app.auth.token_store import delete_refresh_token, load_refresh_token, save_refresh_token
from app.config import get_settings
from app.db.session import get_db
from app.security.session import (
    clear_oauth_state,
    clear_session,
    current_user,
    read_oauth_state,
    set_oauth_state,
    set_session,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _to_frontend(path: str, **params: str) -> RedirectResponse:
    url = get_settings().frontend_url.rstrip("/") + path
    if params:
        url += "?" + urlencode(params)
    return RedirectResponse(url, status_code=302)


def _fail(reason: str) -> RedirectResponse:
    response = _to_frontend("/login", error=reason)
    clear_oauth_state(response)
    return response


@router.get("/login")
def login() -> RedirectResponse:
    url, state, code_verifier = google_oauth.build_authorization_url()
    response = RedirectResponse(url, status_code=302)
    set_oauth_state(response, state, code_verifier)
    return response


@router.get("/callback")
def callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    if error:  # user pressed "Cancel" on Google's screen, etc.
        return _fail(error)

    saved = read_oauth_state(request)
    # CSRF check: the state Google sends back must match the one we stored.
    if not saved or not state or not code or saved.get("state") != state:
        return _fail("invalid_state")

    try:
        creds = google_oauth.exchange_code(code, state, saved["cv"])
        email = google_oauth.verified_email(creds)
    except Exception:
        log.exception("OAuth code exchange failed")
        return _fail("oauth_failed")

    # Only the owner may use this app.
    if email.lower() != get_settings().allowed_email.lower():
        log.warning("Rejected login from non-allowed account")
        return _fail("not_allowed")

    granted = set(creds.granted_scopes or creds.scopes or [])
    if not google_oauth.REQUIRED_GMAIL_SCOPES.issubset(granted):
        return _fail("missing_scopes")  # user unticked Gmail permissions

    if not creds.refresh_token:
        return _fail("no_refresh_token")

    save_refresh_token(db, email, creds.refresh_token, sorted(granted))

    response = _to_frontend("/inbox")
    clear_oauth_state(response)
    set_session(response, email)
    return response


@router.get("/me")
def me(email: str = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    connected = load_refresh_token(db, email) is not None
    return {"email": email, "gmail_connected": connected}


@router.post("/logout")
def logout(response: Response) -> dict:
    clear_session(response)
    return {"ok": True}


@router.post("/disconnect")
def disconnect(email: str = Depends(current_user), db: Session = Depends(get_db)) -> dict:
    """Forget the stored Google token (user must log in again)."""
    delete_refresh_token(db, email)
    return {"ok": True}
