// Small helper for calling the FastAPI backend.
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Health = { status: string; env: string };

export async function getHealth(): Promise<Health> {
  const res = await fetch(`${API_URL}/health`, {
    credentials: "include",
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Backend returned ${res.status}`);
  return res.json();
}
