"""Make an email's HTML safe to display (like Gmail does before showing it).

Email HTML comes from strangers, so we treat it as hostile:
- nh3 (a Rust HTML sanitizer) keeps only an allow-list of layout tags/attributes.
  Scripts, iframes, forms, event handlers (onclick=...), javascript: links: all removed.
- Inline styles and <style> blocks are kept, because emails are designed with them
  (CSS can't run code in modern browsers). The frontend also shows the result in a
  sandboxed iframe with a strict Content-Security-Policy, as a second wall.
- Inline images (cid:...) are embedded as data: URIs so they show without extra requests.
"""

import base64
import re

import nh3

_TAGS = {
    "a", "abbr", "address", "b", "big", "blockquote", "br", "caption", "center", "cite",
    "code", "col", "colgroup", "dd", "del", "div", "dl", "dt", "em", "font", "h1", "h2",
    "h3", "h4", "h5", "h6", "hr", "i", "img", "ins", "kbd", "li", "mark", "ol", "p", "pre",
    "q", "s", "small", "span", "strike", "strong", "style", "sub", "sup", "table", "tbody",
    "td", "tfoot", "th", "thead", "tr", "tt", "u", "ul",
}
_LAYOUT_ATTRS = {
    "align", "valign", "bgcolor", "width", "height", "border", "cellpadding",
    "cellspacing", "colspan", "rowspan", "dir", "lang", "title", "class", "style",
}
_ATTRIBUTES = {
    "*": _LAYOUT_ATTRS,
    "a": {"href", "name", "target"},
    "img": {"src", "alt"},
    "font": {"color", "face", "size"},
    "table": {"background"},
    "td": {"background", "nowrap"},
}
_URL_SCHEMES = {"http", "https", "mailto", "tel", "cid", "data"}
_SAFE_DATA_IMAGE = re.compile(r"^data:image/(png|jpe?g|gif|webp|bmp);base64,", re.IGNORECASE)
MAX_INLINE_IMAGE_BYTES = 2 * 1024 * 1024  # don't bloat the response with huge images


def _attribute_filter(tag: str, attr: str, value: str) -> str | None:
    # data: URLs are only allowed as real images (never as a clickable link).
    if attr in ("href", "background") and value.strip().lower().startswith("data:"):
        return None
    if attr == "src" and value.strip().lower().startswith("data:") and not _SAFE_DATA_IMAGE.match(value.strip()):
        return None
    return value


def embed_inline_images(html: str, inline_images: dict[str, tuple[str, bytes]]) -> str:
    """Replace src="cid:xyz" with a data: URI of the matching MIME part."""

    def _swap(match: re.Match) -> str:
        cid = match.group(2).strip("<>")
        found = inline_images.get(cid)
        if not found or len(found[1]) > MAX_INLINE_IMAGE_BYTES:
            return match.group(0)
        ctype, data = found
        return f'{match.group(1)}data:{ctype};base64,{base64.b64encode(data).decode()}'

    return re.sub(r'''(src\s*=\s*["']?)cid:([^"'\s>]+)''', _swap, html, flags=re.IGNORECASE)


def sanitize_html(html: str) -> str:
    return nh3.clean(
        html,
        tags=_TAGS,
        clean_content_tags={"script", "noscript", "iframe", "object", "embed", "title", "head"},
        attributes=_ATTRIBUTES,
        attribute_filter=_attribute_filter,
        url_schemes=_URL_SCHEMES,
        link_rel="noopener noreferrer nofollow",
        strip_comments=True,
    )
