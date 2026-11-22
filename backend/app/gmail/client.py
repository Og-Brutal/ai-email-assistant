"""Thin wrapper around the Gmail API (read-only operations for Phase 1)."""

from datetime import datetime, timezone

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from app.gmail.parser import parse_message
from app.gmail.schemas import EmailPage, EmailSummary, Label, ParsedEmail, Thread

_SUMMARY_HEADERS = ["From", "Subject", "Date"]
MAX_PAGE_SIZE = 50


def _header(msg: dict, name: str) -> str:
    for h in msg.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _internal_date(msg: dict) -> datetime | None:
    ms = msg.get("internalDate")
    return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc) if ms else None


class GmailClient:
    def __init__(self, credentials: Credentials, service=None):
        # `service` can be injected in tests; normally we build the real one.
        self._svc = service or build(
            "gmail", "v1", credentials=credentials, cache_discovery=False
        )

    # ------------------------------------------------------------ helpers
    def _batch_get(self, ids: list[str], **params) -> list[dict]:
        """Fetch many messages in ONE HTTP round trip (Gmail batch request)."""
        results: dict[str, dict] = {}

        def _collect(request_id, response, exception):
            if exception is None:
                results[request_id] = response

        batch = self._svc.new_batch_http_request(callback=_collect)
        for mid in ids:
            batch.add(self._svc.users().messages().get(userId="me", id=mid, **params), request_id=mid)
        batch.execute()
        return [results[mid] for mid in ids if mid in results]  # keep Gmail's order

    # ------------------------------------------------------------ public API
    def list_emails(
        self, query: str = "", max_results: int = 20, page_token: str | None = None,
        label_ids: list[str] | None = None,
    ) -> EmailPage:
        max_results = max(1, min(max_results, MAX_PAGE_SIZE))
        params = {"userId": "me", "q": query, "maxResults": max_results}
        if page_token:
            params["pageToken"] = page_token
        if label_ids:
            params["labelIds"] = label_ids
        listing = self._svc.users().messages().list(**params).execute()

        ids = [m["id"] for m in listing.get("messages", [])]
        msgs = self._batch_get(ids, format="metadata", metadataHeaders=_SUMMARY_HEADERS) if ids else []
        emails = [
            EmailSummary(
                id=m["id"],
                thread_id=m["threadId"],
                **{"from": _header(m, "From")},
                subject=_header(m, "Subject"),
                date=_internal_date(m),
                snippet=m.get("snippet", ""),
                label_ids=m.get("labelIds", []),
                unread="UNREAD" in m.get("labelIds", []),
            )
            for m in msgs
        ]
        return EmailPage(emails=emails, next_page_token=listing.get("nextPageToken"))

    def get_email(self, message_id: str) -> ParsedEmail:
        msg = self._svc.users().messages().get(userId="me", id=message_id, format="raw").execute()
        return parse_message(msg)

    def get_thread(self, thread_id: str) -> Thread:
        t = self._svc.users().threads().get(userId="me", id=thread_id, format="minimal").execute()
        ids = [m["id"] for m in t.get("messages", [])]
        messages = [parse_message(m) for m in self._batch_get(ids, format="raw")]
        return Thread(id=thread_id, messages=messages)

    def list_labels(self) -> list[Label]:
        res = self._svc.users().labels().list(userId="me").execute()
        return [
            Label(id=l["id"], name=l["name"], type=l.get("type", "user"))
            for l in res.get("labels", [])
        ]
