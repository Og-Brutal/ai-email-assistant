"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppHeader from "@/components/AppHeader";
import { listEmails, needsLogin, type EmailSummary } from "@/lib/api";
import { displayName, shortDate } from "@/lib/format";
import { useAuth } from "@/lib/useAuth";

export default function InboxPage() {
  const router = useRouter();
  const { me, error: authError } = useAuth();

  const [emails, setEmails] = useState<EmailSummary[]>([]);
  const [nextToken, setNextToken] = useState<string | null>(null);
  const [query, setQuery] = useState("in:inbox");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (q: string, pageToken?: string) => {
      setLoading(true);
      setError(null);
      try {
        const page = await listEmails(q, pageToken);
        setEmails((prev) => (pageToken ? [...prev, ...page.emails] : page.emails));
        setNextToken(page.next_page_token);
      } catch (err) {
        if (needsLogin(err)) router.replace("/login");
        else setError("Could not load emails.");
      } finally {
        setLoading(false);
      }
    },
    [router],
  );

  useEffect(() => {
    if (me) load("in:inbox");
  }, [me, load]);

  if (authError) return <p className="p-8 text-red-600">{authError}</p>;
  if (!me) return <p className="p-8 text-gray-500">Loading…</p>;

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col">
      <AppHeader email={me.email} />

      <form
        className="flex gap-2 p-4"
        onSubmit={(e) => {
          e.preventDefault();
          load(query);
        }}
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Gmail search, e.g. is:unread newer_than:2d"
          className="flex-1 rounded-md border border-gray-300 bg-transparent px-3 py-2 dark:border-gray-700"
        />
        <button className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">Search</button>
      </form>

      {error && <p className="px-4 text-red-600">{error}</p>}

      <ul className="divide-y divide-gray-200 dark:divide-gray-800">
        {emails.map((e) => (
          <li key={e.id}>
            <Link
              href={`/inbox/${e.id}`}
              className="flex flex-col gap-0.5 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-900 sm:flex-row sm:items-baseline sm:gap-4"
            >
              <span className={`w-48 shrink-0 truncate ${e.unread ? "font-semibold" : ""}`}>
                {displayName(e.from)}
              </span>
              <span className="min-w-0 flex-1 truncate">
                <span className={e.unread ? "font-semibold" : ""}>{e.subject || "(no subject)"}</span>
                <span className="text-gray-500"> — {e.snippet}</span>
              </span>
              <span className="shrink-0 text-sm text-gray-500">{shortDate(e.date)}</span>
            </Link>
          </li>
        ))}
      </ul>

      {!loading && emails.length === 0 && !error && (
        <p className="p-8 text-center text-gray-500">No emails found.</p>
      )}
      {loading && <p className="p-4 text-center text-gray-500">Loading…</p>}
      {nextToken && !loading && (
        <button onClick={() => load(query, nextToken)} className="m-4 self-center text-blue-600 hover:underline">
          Load more
        </button>
      )}
    </div>
  );
}
