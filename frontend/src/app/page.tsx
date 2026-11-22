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
    </main>
  );
}
