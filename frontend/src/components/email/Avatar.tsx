const COLORS = [
  "bg-blue-600", "bg-emerald-600", "bg-purple-600", "bg-rose-600",
  "bg-amber-600", "bg-cyan-600", "bg-indigo-600", "bg-teal-600",
];

/** Gmail-style circle with the sender's first letter; same sender = same color. */
export default function Avatar({ name }: { name: string }) {
  const letter = (name.trim()[0] ?? "?").toUpperCase();
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return (
    <div
      aria-hidden
      className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-lg font-medium text-white ${COLORS[hash % COLORS.length]}`}
    >
      {letter}
    </div>
  );
}
