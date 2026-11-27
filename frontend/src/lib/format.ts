/** "Ahmed Khan <ahmed@x.com>" -> "Ahmed Khan" */
export function displayName(from: string): string {
  const m = from.match(/^\s*"?([^"<]+?)"?\s*<.+>\s*$/);
  return m ? m[1] : from;
}

/** Today -> "14:05", this year -> "Nov 16", older -> "16/11/2024" */
export function shortDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  if (d.toDateString() === now.toDateString())
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (d.getFullYear() === now.getFullYear())
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
  return d.toLocaleDateString();
}

/** "Ahmed Khan <ahmed@x.com>" -> { name: "Ahmed Khan", email: "ahmed@x.com" } */
export function parseAddress(value: string): { name: string; email: string } {
  const m = value.match(/^\s*"?([^"<]*?)"?\s*<([^>]+)>\s*$/);
  if (m) return { name: m[1] || m[2], email: m[2] };
  return { name: value, email: value };
}

/** Gmail-style: "Nov 25, 2026, 10:57 PM (2 days ago)" */
export function longDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  const text = d.toLocaleString([], {
    month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit",
  });
  const mins = Math.round((Date.now() - d.getTime()) / 60000);
  let ago = "";
  if (mins < 60) ago = `${Math.max(mins, 1)} min ago`;
  else if (mins < 60 * 24) ago = `${Math.round(mins / 60)} hours ago`;
  else if (mins < 60 * 24 * 30) ago = `${Math.round(mins / 60 / 24)} days ago`;
  return ago ? `${text} (${ago})` : text;
}

/** Hide Gmail's internal labels; show the meaningful ones as chips. */
const SYSTEM_LABELS: Record<string, string> = {
  INBOX: "Inbox", IMPORTANT: "Important", STARRED: "Starred",
  CATEGORY_SOCIAL: "Social", CATEGORY_PROMOTIONS: "Promotions",
  CATEGORY_UPDATES: "Updates", CATEGORY_FORUMS: "Forums",
};
export function visibleLabels(ids: string[]): string[] {
  return ids.filter((id) => id in SYSTEM_LABELS).map((id) => SYSTEM_LABELS[id]);
}

export function fileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
