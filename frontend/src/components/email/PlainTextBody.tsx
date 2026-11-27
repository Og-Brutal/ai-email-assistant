import { Fragment } from "react";

const URL_RE = /(https?:\/\/[^\s<>"')\]]+)/g;

/** Long tracking URLs -> "linkedin.com/comm/mynetwork/…" (full URL still opens). */
function shortUrl(url: string): string {
  try {
    const u = new URL(url);
    const path = u.pathname.length > 28 ? u.pathname.slice(0, 28) + "…" : u.pathname;
    return u.hostname.replace(/^www\./, "") + (path === "/" ? "" : path);
  } catch {
    return url.slice(0, 40) + "…";
  }
}

/** Plain-text email with clickable, shortened links. Rendered as text, never HTML. */
export default function PlainTextBody({ text }: { text: string }) {
  return (
    <div className="whitespace-pre-wrap break-words text-[15px] leading-relaxed">
      {text.split("\n").map((line, i) => (
        <Fragment key={i}>
          {line.split(URL_RE).map((chunk, j) =>
            j % 2 === 1 ? (
              <a
                key={j}
                href={chunk}
                target="_blank"
                rel="noopener noreferrer nofollow"
                title={chunk}
                className="text-blue-500 hover:underline"
              >
                {shortUrl(chunk)}
              </a>
            ) : (
              <Fragment key={j}>{chunk}</Fragment>
            ),
          )}
          {"\n"}
        </Fragment>
      ))}
    </div>
  );
}
