"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { logout } from "@/lib/api";

export default function AppHeader({ email }: { email: string }) {
  const router = useRouter();

  async function onLogout() {
    try {
      await logout();
    } finally {
      router.replace("/login");
    }
  }

  return (
    <header className="flex items-center justify-between border-b border-gray-200 px-4 py-3 dark:border-gray-800">
      <Link href="/inbox" className="text-lg font-semibold">
        AI Email Assistant
      </Link>
      <div className="flex items-center gap-3 text-sm">
        <span className="hidden text-gray-500 sm:inline">{email}</span>
        <button
          onClick={onLogout}
          className="rounded-md border border-gray-300 px-3 py-1 hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
        >
          Log out
        </button>
      </div>
    </header>
  );
}
