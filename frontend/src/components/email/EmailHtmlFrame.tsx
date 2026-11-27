"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type Props = {
  html: string; // already sanitized by the backend
  showImages: boolean;
  showQuoted: boolean;
};

/**
 * Shows an HTML email exactly as designed, the way Gmail does, but isolated:
 * - sandbox WITHOUT allow-scripts: no JavaScript can ever run inside.
 * - Content-Security-Policy: blocks all network loads except images (and only when
 *   the user clicks "Show images"), so tracking pixels can't see you opened it.
 * - <base target="_blank">: links open in a new tab, never inside the app.
 */
export default function EmailHtmlFrame({ html, showImages, showQuoted }: Props) {
  const ref = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(200);

  const srcDoc = useMemo(() => {
    const imgSrc = showImages ? "data: https: http: cid:" : "data:";
    const csp = [
      "default-src 'none'",
      `img-src ${imgSrc}`,
      "style-src 'unsafe-inline'",
      "font-src data: https:",
    ].join("; ");
    const quoteCss = showQuoted ? "" : ".gmail_quote,blockquote[type=cite]{display:none!important}";
    return `<!doctype html><html><head><meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="${csp}">
<base target="_blank">
<style>
  html,body{margin:0;padding:0;background:#ffffff;color:#202124;}
  body{padding:16px;font:14px/1.5 Arial,Helvetica,sans-serif;overflow-wrap:anywhere;}
  img{max-width:100%;height:auto;}
  table{max-width:100%;}
  a{color:#1a73e8;}
  ${quoteCss}
</style></head><body>${html}</body></html>`;
  }, [html, showImages, showQuoted]);

  // Grow the iframe to fit its content (allowed because allow-same-origin; scripts stay off).
  const observer = useRef<ResizeObserver | null>(null);
  const fit = () => {
    const doc = ref.current?.contentDocument;
    if (!doc?.body) return;
    const measure = () => setHeight(doc.documentElement.scrollHeight);
    measure();
    observer.current?.disconnect();
    observer.current = new ResizeObserver(measure); // re-fit when images load / quotes toggle
    observer.current.observe(doc.body);
  };
  // The iframe can finish loading BEFORE React attaches onLoad (server-rendered HTML),
  // so also measure right away if it's already loaded.
  useEffect(() => {
    if (ref.current?.contentDocument?.readyState === "complete") fit();
  });
  useEffect(() => () => observer.current?.disconnect(), []);

  return (
    <iframe
      ref={ref}
      title="Email content"
      srcDoc={srcDoc}
      onLoad={fit}
      sandbox="allow-same-origin allow-popups allow-popups-to-escape-sandbox"
      referrerPolicy="no-referrer"
      style={{ height }}
      className="w-full rounded-lg border-0 bg-white"
    />
  );
}
