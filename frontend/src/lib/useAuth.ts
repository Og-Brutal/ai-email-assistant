"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getMe, needsLogin, type Me } from "@/lib/api";

/** Loads the current user; sends the browser to /login if not signed in. */
export function useAuth() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then(setMe)
      .catch((err) => {
        if (needsLogin(err)) router.replace("/login");
        else setError("Could not reach the backend.");
      });
  }, [router]);

  return { me, error };
}
