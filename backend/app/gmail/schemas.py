"""Pydantic models returned by the Gmail layer."""

from datetime import datetime

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    filename: str
    mime_type: str
    size: int  # bytes


class ParsedEmail(BaseModel):
    id: str = ""
    thread_id: str = ""
    label_ids: list[str] = Field(default_factory=list)
    snippet: str = ""

    from_: str = Field("", alias="from")
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    reply_to: str = ""
    subject: str = ""
    date: datetime | None = None
    message_id_header: str = ""  # RFC "Message-ID", needed later to reply in-thread

    body_text: str = ""  # full plain text (HTML converted if needed)
    body_clean: str = ""  # quoted history + signature removed
    body_html: str = ""  # SANITIZED html for display ("" for plain-text emails)
    has_html: bool = False
    attachments: list[Attachment] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class EmailSummary(BaseModel):
    """Lightweight row for the inbox list."""

    id: str
    thread_id: str
    from_: str = Field("", alias="from")
    subject: str = ""
    date: datetime | None = None
    snippet: str = ""
    label_ids: list[str] = Field(default_factory=list)
    unread: bool = False

    model_config = {"populate_by_name": True}


class EmailPage(BaseModel):
    emails: list[EmailSummary]
    next_page_token: str | None = None


class Thread(BaseModel):
    id: str
    messages: list[ParsedEmail]


class Label(BaseModel):
    id: str
    name: str
    type: str  # "system" or "user"
