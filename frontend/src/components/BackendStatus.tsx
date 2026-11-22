"use client";

import { useEffect, useState } from "react";
import { getHealth } from "@/lib/api";

type State = "checking" | "online" | "offline";

export default function BackendStatus() {
  const [state, setState] = useState<State>("checking");

  useEffect(() => {
    getHealth()
      .then(() => setState("online"))
      .catch(() => setState("offline"));
  }, []);

  const styles: Record<State, string> = {
    checking: "bg-gray-100 text-gray-700",
    online: "bg-green-100 text-green-800",
    offline: "bg-red-100 text-red-800",
  };
  const labels: Record<State, string> = {
    checking: "Checking backend…",
    online: "Backend online",
    offline: "Backend offline",
  };

  return (
    <span
      data-testid="backend-status"
      className={`inline-block rounded-full px-3 py-1 text-sm font-medium ${styles[state]}`}
    >
      {labels[state]}
    </span>
  );
}
