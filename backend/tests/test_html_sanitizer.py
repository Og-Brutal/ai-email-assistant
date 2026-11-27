from pathlib import Path

from app.gmail.html_sanitizer import sanitize_html
from app.gmail.parser import parse_mime

FIXTURES = Path(__file__).parent / "fixtures"


def test_scripts_and_event_handlers_removed():
    dirty = (
        '<div onclick="steal()">Hi<script>alert(1)</script></div>'
        '<img src="x" onerror="alert(2)">'
        '<iframe src="https://evil.example"></iframe>'
        '<form action="https://evil.example"><input name="password"></form>'
    )
    clean = sanitize_html(dirty)
    for bad in ("script", "alert", "onclick", "onerror", "iframe", "<form", "<input"):
        assert bad not in clean
    assert "Hi" in clean


def test_javascript_and_data_links_removed():
    clean = sanitize_html(
        '<a href="javascript:alert(1)">a</a>'
        '<a href="data:text/html,<script>alert(1)</script>">b</a>'
        '<img src="data:text/html;base64,PHNjcmlwdD4=">'
    )
    assert "javascript:" not in clean
    assert "data:text/html" not in clean


def test_email_layout_and_styles_kept():
    clean = sanitize_html(
        '<style>.btn{color:red}</style>'
        '<table width="600" bgcolor="#fff"><tr><td style="padding:8px" class="btn">'
        '<a href="https://example.com">Open</a></td></tr></table>'
    )
    assert "<style>" in clean
    assert 'width="600"' in clean
    assert 'style="padding:8px"' in clean
    assert 'href="https://example.com"' in clean
    assert 'rel="noopener noreferrer nofollow"' in clean


def test_inline_cid_image_embedded_not_listed_as_attachment():
    e = parse_mime((FIXTURES / "html_inline_image.eml").read_bytes())
    assert 'src="data:image/png;base64,' in e.body_html
    assert "cid:" not in e.body_html
    assert e.attachments == []
    assert "Thanks for your order!" in e.body_text


def test_plain_text_email_has_no_html():
    e = parse_mime((FIXTURES / "plain_reply.eml").read_bytes())
    assert e.body_html == ""


def test_parsed_html_email_is_sanitized():
    e = parse_mime((FIXTURES / "html_only.eml").read_bytes())
    assert "Big Sale" in e.body_html
    assert "alert(1)" not in e.body_html
