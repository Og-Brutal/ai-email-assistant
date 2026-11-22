import Link from "next/link";
import BackendStatus from "@/components/BackendStatus";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8 text-center">
      <h1 className="text-4xl font-bold">AI Email Assistant</h1>
      <p className="max-w-md text-gray-600">
        Chat with your Gmail inbox: sort, summarize, search and draft replies,
        with every send approved by you.
      </p>
      <BackendStatus />
      <Link
        href="/inbox"
        className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700"
      >
        Open inbox
      </Link>
    </main>
  );
}
