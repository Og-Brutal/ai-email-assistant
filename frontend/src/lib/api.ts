// Small helpers for calling the FastAPI backend.
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`${status}: ${detail}`);
  }
}

/** fetch wrapper: always sends the session cookie and throws ApiError on failure. */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    credentials: "include",
    cache: "no-store",
    ...init,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* body was not JSON */
    }
    throw new ApiError(res.status, String(detail));
  }
  return res.json() as Promise<T>;
}

/** True when the user must (re)login: no session, expired Google token, etc. */
export function needsLogin(err: unknown): boolean {
  return err instanceof ApiError && err.status === 401;
}

// ---------- Types (mirror backend/app/gmail/schemas.py) ----------
export type Health = { status: string; env: string };
export type Me = { email: string; gmail_connected: boolean };

export type EmailSummary = {
  id: string;
  thread_id: string;
  from: string;
  subject: string;
  date: string | null;
  snippet: string;
  label_ids: string[];
  unread: boolean;
};
export type EmailPage = { emails: EmailSummary[]; next_page_token: string | null };

export type Attachment = { filename: string; mime_type: string; size: number };
export type ParsedEmail = {
  id: string;
  thread_id: string;
  label_ids: string[];
  from: string;
  to: string[];
  cc: string[];
  subject: string;
  date: string | null;
  body_text: string;
  body_clean: string;
  body_html: string; // sanitized by backend; "" for plain-text emails
  has_html: boolean;
  attachments: Attachment[];
};

// ---------- Endpoints ----------
export const getHealth = () => apiFetch<Health>("/health");
export const getMe = () => apiFetch<Me>("/auth/me");
export const logout = () => apiFetch<{ ok: boolean }>("/auth/logout", { method: "POST" });
export const loginUrl = () => `${API_URL}/auth/login`;

export function listEmails(q = "", pageToken?: string) {
  const params = new URLSearchParams({ q, max_results: "20" });
  if (pageToken) params.set("page_token", pageToken);
  return apiFetch<EmailPage>(`/emails?${params}`);
}

export const getEmail = (id: string) =>
  apiFetch<ParsedEmail>(`/emails/${encodeURIComponent(id)}`);
