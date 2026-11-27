import type { Attachment } from "@/lib/api";
import { fileSize } from "@/lib/format";

function icon(mime: string): string {
  if (mime === "application/pdf") return "📕";
  if (mime.startsWith("image/")) return "🖼️";
  if (mime.includes("sheet") || mime.includes("excel") || mime.includes("csv")) return "📊";
  if (mime.includes("word") || mime.includes("document")) return "📘";
  if (mime.includes("zip") || mime.includes("compressed")) return "🗜️";
  return "📎";
}

/** Gmail-style attachment cards under the message. */
export default function Attachments({ items }: { items: Attachment[] }) {
  if (items.length === 0) return null;
  return (
    <section className="mt-6 border-t border-gray-200 pt-4 dark:border-gray-800">
      <h2 className="mb-3 text-sm font-medium text-gray-500">
        {items.length} attachment{items.length > 1 ? "s" : ""}
      </h2>
      <ul className="flex flex-wrap gap-3">
        {items.map((a, i) => (
          <li
            key={i}
            className="flex w-56 items-center gap-3 rounded-lg border border-gray-200 px-3 py-2 dark:border-gray-700"
          >
            <span className="text-2xl" aria-hidden>{icon(a.mime_type)}</span>
            <span className="min-w-0">
              <span className="block truncate text-sm" title={a.filename}>{a.filename}</span>
              <span className="text-xs text-gray-500">{fileSize(a.size)}</span>
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
