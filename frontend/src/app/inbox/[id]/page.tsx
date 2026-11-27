"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AppHeader from "@/components/AppHeader";
import EmailView from "@/components/email/EmailView";
import { ApiError, getEmail, needsLogin, type ParsedEmail } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

export default function EmailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { me, error: authError } = useAuth();

  const [email, setEmail] = useState<ParsedEmail | null>(null);
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
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col">
      <AppHeader email={me.email} />
      <div className="p-4 sm:p-6">
        <Link href="/inbox" className="mb-4 inline-block text-sm text-blue-500 hover:underline">
          ← Back to inbox
        </Link>

        {error && <p className="mt-4 text-red-600">{error}</p>}
        {!email && !error && <p className="mt-4 text-gray-500">Loading…</p>}
        {email && <EmailView email={email} myEmail={me.email} />}
      </div>
    </div>
  );
}
