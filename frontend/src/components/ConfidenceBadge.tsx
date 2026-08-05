interface Props {
  confidence: number;
  lowConfidence: boolean;
}

export function ConfidenceBadge({ confidence, lowConfidence }: Props) {
  const pct = Math.round(confidence * 100);
  const tone = lowConfidence
    ? "bg-amber-500/15 text-amber-300 border-amber-500/30"
    : "bg-emerald-500/15 text-emerald-300 border-emerald-500/30";
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${tone}`}
      title="Highest retrieval similarity score across cited sources"
    >
      <span className={`h-1.5 w-1.5 rounded-full ${lowConfidence ? "bg-amber-400" : "bg-emerald-400"}`} />
      {lowConfidence ? "Low confidence" : "Grounded"} · {pct}%
    </span>
  );
}
