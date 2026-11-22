"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { loginUrl } from "@/lib/api";

// Friendly text for the `?error=` codes the backend sends back.
const ERRORS: Record<string, string> = {
  access_denied: "You cancelled the Google sign-in.",
  invalid_state: "Login session expired or was tampered with. Please try again.",
  oauth_failed: "Google sign-in failed. Please try again.",
  not_allowed: "This Google account is not allowed to use this app.",
  missing_scopes:
    "Please tick ALL Gmail permissions on Google's screen; the app needs them to work.",
  no_refresh_token: "Google did not return a refresh token. Please try again.",
};

function LoginContent() {
  const error = useSearchParams().get("error");
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <h1 className="text-3xl font-bold">AI Email Assistant</h1>
      <p className="max-w-sm text-gray-500">Sign in with the Google account you want to manage.</p>

      {error && (
        <p role="alert" className="max-w-sm rounded-md bg-red-100 px-4 py-2 text-sm text-red-800">
          {ERRORS[error] ?? `Sign-in error: ${error}`}
        </p>
      )}

      {/* Full-page navigation: the backend redirects to Google's consent screen. */}
      <a
        href={loginUrl()}
        className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700"
      >
        Sign in with Google
      </a>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginContent />
    </Suspense>
  );
}
