"""FastAPI entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError

from app.auth.routes import router as auth_router
from app.config import get_settings
from app.db.session import init_db
from app.gmail.routes import router as gmail_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    missing = settings.missing_required()
    if missing:  # fail fast with a clear message instead of 500s later
        raise RuntimeError(f"Missing settings in backend/.env: {', '.join(missing)}")
    init_db()  # create tables on startup
    yield


app = FastAPI(title="AI Email Assistant API", version="0.2.0", lifespan=lifespan)

# Only the frontend may call the API, with cookies (needed for login sessions).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)

app.include_router(auth_router)
app.include_router(gmail_router)


# ---------- Error handling ----------
@app.exception_handler(RefreshError)
async def google_refresh_error(request: Request, exc: RefreshError):
    # Refresh token expired or revoked (e.g. 7-day limit in Testing mode).
    log.warning("Google refresh token rejected: %s", exc)
    return JSONResponse(status_code=401, content={"detail": "reauth_required"})


@app.exception_handler(HttpError)
async def gmail_http_error(request: Request, exc: HttpError):
    status = exc.resp.status if exc.resp is not None else 502
    if status == 404:
        return JSONResponse(status_code=404, content={"detail": "not_found"})
    if status == 429:
        return JSONResponse(status_code=429, content={"detail": "gmail_rate_limited"})
    log.error("Gmail API error %s: %s", status, exc)
    return JSONResponse(status_code=502, content={"detail": "gmail_error"})


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "env": settings.app_env}
