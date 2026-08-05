interface Props {
  stage: "retrieving" | "generating" | null;
}

export function StatusIndicator({ stage }: Props) {
  if (!stage) return null;
  const label = stage === "retrieving" ? "Searching your documents…" : "Writing an answer…";
  return (
    <div className="flex items-center gap-2 px-1 text-sm text-ink-400">
      <span className="flex gap-1">
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-ink-400 [animation-delay:-0.3s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-ink-400 [animation-delay:-0.15s]" />
        <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-ink-400" />
      </span>
      {label}
    </div>
  );
}
