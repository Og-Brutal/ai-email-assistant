import base64
from pathlib import Path

from app.gmail.parser import b64url_decode, parse_message, parse_mime

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_plain_reply_headers():
    e = parse_mime(load("plain_reply.eml"))
    assert e.from_ == "Ahmed Khan <ahmed@example.com>"
    assert e.to == ["Wahab <me@example.com>"]
    assert e.cc == ["Sara <sara@example.com>", "ops@example.com"]
    assert e.subject == "Re: Pricing for Q3"
    assert e.date is not None and e.date.year == 2026
    assert e.message_id_header == "<abc123@mail.example.com>"


def test_plain_reply_strips_quote_and_signature():
    e = parse_mime(load("plain_reply.eml"))
    assert "$40/user works for us" in e.body_clean
    assert "Sales Lead" not in e.body_clean  # signature removed
    assert "can we agree" not in e.body_clean  # quoted history removed
    assert "can we agree" in e.body_text  # but full text keeps it


def test_html_only_base64_converted_to_text():
    e = parse_mime(load("html_only.eml"))
    assert e.subject == "🎉 Big Sale Today"  # RFC 2047 encoded subject
    assert e.has_html
    assert "Big Sale" in e.body_text
    assert "Get 50% off today." in e.body_text  # &nbsp; normalized
    assert "Ends at midnight." in e.body_text  # <br> became a newline
    assert "Shop now (https://shop.example/sale)" in e.body_text
    assert "alert(1)" not in e.body_text  # scripts dropped
    assert ".hidden" not in e.body_text  # styles dropped


def test_multipart_prefers_plain_and_decodes_charset():
    e = parse_mime(load("multipart_alt_attachment.eml"))
    assert e.body_text == "Please review the contract. Café meeting at 5pm."
    assert "<p>" not in e.body_text


def test_attachment_metadata():
    e = parse_mime(load("multipart_alt_attachment.eml"))
    assert len(e.attachments) == 1
    att = e.attachments[0]
    assert att.filename == "contract.pdf"
    assert att.mime_type == "application/pdf"
    assert att.size > 0


def test_gmail_html_quote_removed():
    e = parse_mime(load("gmail_html_reply.eml"))
    assert e.body_clean == "Thursday 3pm works for me."
    assert "Can we meet this week?" in e.body_text
    assert "EAA_QUOTE" not in e.body_text


def test_outlook_reply_and_mobile_footer_removed():
    e = parse_mime(load("outlook_reply.eml"))
    assert e.body_clean == "Looks good, send it to the client."


def test_parse_message_reads_gmail_raw_format():
    raw = base64.urlsafe_b64encode(load("plain_reply.eml")).decode().rstrip("=")
    e = parse_message(
        {"id": "m1", "threadId": "t1", "labelIds": ["INBOX", "UNREAD"], "snippet": "Hi", "raw": raw}
    )
    assert (e.id, e.thread_id, e.label_ids) == ("m1", "t1", ["INBOX", "UNREAD"])
    assert e.subject == "Re: Pricing for Q3"


def test_b64url_decode_handles_missing_padding():
    assert b64url_decode("aGk") == b"hi"


def test_broken_input_does_not_crash():
    e = parse_mime(b"Subject: x\nContent-Type: text/plain; charset=x-unknown\n\n\xff\xfe ok")
    assert "ok" in e.body_text
