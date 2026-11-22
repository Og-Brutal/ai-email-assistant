"""Read-only Gmail endpoints used by the inbox UI."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.gmail.client import MAX_PAGE_SIZE, GmailClient
from app.gmail.deps import get_gmail
from app.gmail.schemas import EmailPage, Label, ParsedEmail, Thread

router = APIRouter(tags=["gmail"])

# Gmail IDs are hex strings; rejecting anything else blocks path tricks early.
GmailId = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,64}$")]


@router.get("/emails", response_model=EmailPage, response_model_by_alias=True)
def list_emails(
    q: str = Query("", max_length=500, description="Gmail search, e.g. 'is:unread newer_than:1d'"),
    label: str | None = Query(None, max_length=100),
    max_results: int = Query(20, ge=1, le=MAX_PAGE_SIZE),
    page_token: str | None = Query(None, max_length=200),
    gmail: GmailClient = Depends(get_gmail),
) -> EmailPage:
    return gmail.list_emails(
        query=q, max_results=max_results, page_token=page_token,
        label_ids=[label] if label else None,
    )


@router.get("/emails/{message_id}", response_model=ParsedEmail, response_model_by_alias=True)
def get_email(message_id: GmailId, gmail: GmailClient = Depends(get_gmail)) -> ParsedEmail:
    return gmail.get_email(message_id)


@router.get("/threads/{thread_id}", response_model=Thread, response_model_by_alias=True)
def get_thread(thread_id: GmailId, gmail: GmailClient = Depends(get_gmail)) -> Thread:
    return gmail.get_thread(thread_id)


@router.get("/labels", response_model=list[Label])
def list_labels(gmail: GmailClient = Depends(get_gmail)) -> list[Label]:
    return gmail.list_labels()
