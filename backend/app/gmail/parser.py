"""Turn raw Gmail messages into clean text.

We ask Gmail for the message in `raw` format (the original RFC 822 bytes, base64url
encoded) and parse it with Python's standard `email` package. It already handles
multipart MIME, base64 / quoted-printable transfer encodings and charsets; we add
HTML -> text conversion, quoted-reply stripping and attachment metadata on top.
"""

import base64
import re
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime

from bs4 import BeautifulSoup

from app.gmail.html_sanitizer import embed_inline_images, sanitize_html
from app.gmail.schemas import Attachment, ParsedEmail


# ---------------------------------------------------------------- decoding
def b64url_decode(data: str) -> bytes:
    """Gmail uses base64url WITHOUT padding; add it back before decoding."""
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _part_text(part: EmailMessage) -> str:
    """Decode a text part using its declared charset, never crashing on bad bytes."""
    payload = part.get_payload(decode=True) or b""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:  # unknown charset name, e.g. "x-unknown"
        return payload.decode("utf-8", errors="replace")


# ---------------------------------------------------------------- HTML -> text
_BLOCK_TAGS = ["p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6", "blockquote"]


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "head", "title", "meta"]):
        tag.decompose()  # never keep scripts/styles (also removes hidden junk)
    # Gmail wraps quoted history in <div class="gmail_quote"> / <blockquote>
    for quote in soup.select("div.gmail_quote, blockquote.gmail_quote"):
        quote.insert_before(soup.new_string("\n" + _HTML_QUOTE_MARKER + "\n"))
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for tag in soup.find_all(_BLOCK_TAGS):
        tag.insert_after("\n")
    for a in soup.find_all("a", href=True):  # keep link targets visible
        text = a.get_text(strip=True)
        if text and a["href"].startswith("http") and a["href"] != text:
            a.replace_with(f"{text} ({a['href']})")
    return normalize_whitespace(soup.get_text())


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace(" ", " ")
    lines = [line.rstrip() for line in text.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)  # collapse big gaps
    return text.strip()


# ---------------------------------------------------------------- quote / signature stripping
_HTML_QUOTE_MARKER = "[[EAA_QUOTE_START]]"

# Lines that start the quoted history of a reply.
_QUOTE_HEADERS = [
    re.compile(r"^On .{3,300}wrote:\s*$", re.IGNORECASE | re.DOTALL),  # Gmail/Apple
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}", re.IGNORECASE),  # Outlook
    re.compile(r"^-{2,}\s*Forwarded message\s*-{2,}", re.IGNORECASE),
    re.compile(r"^From:\s.+", re.IGNORECASE),  # Outlook block: From/Sent/To/Subject
    re.compile(r"^_{10,}\s*$"),  # Outlook separator line
    re.compile(r"^Le .{3,300}a écrit\s*:\s*$", re.IGNORECASE | re.DOTALL),  # French
    re.compile(r"^Am .{3,300}schrieb .*:\s*$", re.IGNORECASE | re.DOTALL),  # German
]
_SIGNATURE_MARKERS = [
    re.compile(r"^--\s?$"),  # standard "-- " signature separator
    re.compile(r"^Sent from my (iPhone|iPad|Android|Galaxy|mobile)", re.IGNORECASE),
    re.compile(r"^Get Outlook for (iOS|Android)", re.IGNORECASE),
]


def strip_quotes_and_signature(text: str) -> str:
    """Return only the NEW part of the message (what this sender actually wrote)."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line == _HTML_QUOTE_MARKER:
            break
        # "On Mon, 1 Jan 2024 at 10:00, Ali <ali@x.com> wrote:" is often wrapped onto 2 lines
        joined = line if i + 1 >= len(lines) else f"{line} {lines[i + 1].strip()}"
        if any(p.match(line) for p in _QUOTE_HEADERS) or (
            line.lower().startswith("on ") and _QUOTE_HEADERS[0].match(joined)
        ):
            # A lone "From:" line only counts if Outlook's "Sent:/Date:" follows soon.
            if line.lower().startswith("from:"):
                window = " ".join(lines[i + 1 : i + 4]).lower()
                if "sent:" not in window and "date:" not in window:
                    out.append(lines[i])
                    i += 1
                    continue
            break
        if line.startswith(">"):  # classic "> quoted" lines
            i += 1
            continue
        if any(p.match(line) for p in _SIGNATURE_MARKERS):
            break
        out.append(lines[i])
        i += 1
    return normalize_whitespace("\n".join(out))


# ---------------------------------------------------------------- main entry points
def _addresses(msg: EmailMessage, header: str) -> list[str]:
    values = msg.get_all(header, [])
    return [
        f"{name} <{addr}>" if name else addr
        for name, addr in getaddresses([str(v) for v in values])
        if addr
    ]


def parse_mime(raw: bytes) -> ParsedEmail:
    """Parse RFC 822 bytes (an .eml file) into a ParsedEmail."""
    msg: EmailMessage = BytesParser(policy=policy.default).parsebytes(raw)

    plain_parts: list[str] = []
    html_parts: list[str] = []
    attachments: list[Attachment] = []
    inline_images: dict[str, tuple[str, bytes]] = {}  # Content-ID -> (type, bytes)

    for part in msg.walk():
        if part.is_multipart():
            continue
        ctype = part.get_content_type()
        disposition = part.get_content_disposition()  # "attachment" / "inline" / None
        filename = part.get_filename()
        content_id = str(part.get("Content-ID", "")).strip().strip("<>")

        # Images referenced from the HTML (src="cid:...") belong in the body, like Gmail.
        if content_id and ctype.startswith("image/") and disposition != "attachment":
            inline_images[content_id] = (ctype, part.get_payload(decode=True) or b"")
        elif disposition == "attachment" or (filename and ctype not in ("text/plain", "text/html")):
            payload = part.get_payload(decode=True) or b""
            attachments.append(
                Attachment(filename=filename or "unnamed", mime_type=ctype, size=len(payload))
            )
        elif ctype == "text/plain":
            plain_parts.append(_part_text(part))
        elif ctype == "text/html":
            html_parts.append(_part_text(part))

    if plain_parts:
        body = normalize_whitespace("\n\n".join(plain_parts))
    elif html_parts:
        body = html_to_text("\n".join(html_parts))
    else:
        body = ""

    # Safe HTML for Gmail-style display (rendered in a sandboxed iframe by the frontend).
    body_html = ""
    if html_parts:
        body_html = sanitize_html(embed_inline_images("\n".join(html_parts), inline_images))

    # For HTML-only mail we keep the gmail_quote marker for stripping, then remove it.
    body_clean = strip_quotes_and_signature(body)
    body = normalize_whitespace(body.replace(_HTML_QUOTE_MARKER, ""))

    date = None
    if msg["Date"]:
        try:
            date = parsedate_to_datetime(str(msg["Date"]))
        except (TypeError, ValueError):
            date = None

    from_list = _addresses(msg, "From")
    reply_to = _addresses(msg, "Reply-To")
    return ParsedEmail(
        **{"from": from_list[0] if from_list else ""},
        to=_addresses(msg, "To"),
        cc=_addresses(msg, "Cc"),
        reply_to=reply_to[0] if reply_to else "",
        subject=str(msg["Subject"] or ""),
        date=date,
        message_id_header=str(msg["Message-ID"] or ""),
        body_text=body,
        body_clean=body_clean,
        body_html=body_html,
        has_html=bool(html_parts),
        attachments=attachments,
    )


def parse_message(gmail_msg: dict) -> ParsedEmail:
    """Parse a Gmail API message fetched with format='raw'."""
    parsed = parse_mime(b64url_decode(gmail_msg["raw"]))
    parsed.id = gmail_msg.get("id", "")
    parsed.thread_id = gmail_msg.get("threadId", "")
    parsed.label_ids = gmail_msg.get("labelIds", [])
    parsed.snippet = gmail_msg.get("snippet", "")
    return parsed
