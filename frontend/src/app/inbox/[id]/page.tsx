"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppHeader from "@/components/AppHeader";
import { ApiError, getEmail, needsLogin, type ParsedEmail } from "@/lib/api";
import { fileSize } from "@/lib/format";
import { useAuth } from "@/lib/useAuth";

export default function EmailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { me, error: authError } = useAuth();

  const [email, setEmail] = useState<ParsedEmail | null>(null);
  const [showFull, setShowFull] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!me) return;
    getEmail(id)
      .then(setEmail)
      .catch((err) => {
        if (needsLogin(err)) router.replace("/login");
        else if (err instanceof ApiError && err.status === 404) setError("Email not found.");
        else setError("Could not load this email.");
      });
  }, [me, id, router]);

  if (authError) return <p className="p-8 text-red-600">{authError}</p>;
  if (!me) return <p className="p-8 text-gray-500">Loading…</p>;

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col">
      <AppHeader email={me.email} />
      <div className="p-4">
        <Link href="/inbox" className="text-sm text-blue-600 hover:underline">
          ← Back to inbox
        </Link>

        {error && <p className="mt-4 text-red-600">{error}</p>}
        {!email && !error && <p className="mt-4 text-gray-500">Loading…</p>}

        {email && (
          <article className="mt-4 space-y-4">
            <h1 className="text-2xl font-semibold">{email.subject || "(no subject)"}</h1>
            <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-sm">
              <dt className="text-gray-500">From</dt>
              <dd className="break-all">{email.from}</dd>
              <dt className="text-gray-500">To</dt>
              <dd className="break-all">{email.to.join(", ")}</dd>
              {email.cc.length > 0 && (
                <>
                  <dt className="text-gray-500">Cc</dt>
                  <dd className="break-all">{email.cc.join(", ")}</dd>
                </>
              )}
              <dt className="text-gray-500">Date</dt>
              <dd>{email.date ? new Date(email.date).toLocaleString() : ""}</dd>
            </dl>

            {/* Rendered as plain text (never as HTML) so email content can't run code. */}
            <pre className="whitespace-pre-wrap break-words rounded-md border border-gray-200 p-4 font-sans dark:border-gray-800">
              {showFull ? email.body_text : email.body_clean || email.body_text}
            </pre>

            {email.body_clean !== email.body_text && (
              <button onClick={() => setShowFull(!showFull)} className="text-sm text-blue-600 hover:underline">
                {showFull ? "Hide quoted text" : "Show full message (with quoted history)"}
              </button>
            )}

            {email.attachments.length > 0 && (
              <div>
                <h2 className="mb-1 text-sm font-medium text-gray-500">Attachments</h2>
                <ul className="text-sm">
                  {email.attachments.map((a, i) => (
                    <li key={i}>
                      📎 {a.filename} <span className="text-gray-500">({fileSize(a.size)})</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </article>
        )}
      </div>
    </div>
  );
}
