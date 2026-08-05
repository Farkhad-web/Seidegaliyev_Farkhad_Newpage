import type { RetrievedChunk } from "../types";

interface Props {
  chunk: RetrievedChunk | null;
  onClose: () => void;
}

export function SourcesDrawer({ chunk, onClose }: Props) {
  return (
    <aside
      className={`fixed inset-y-0 right-0 z-30 w-full max-w-md transform border-l border-ink-700 bg-ink-900 shadow-2xl transition-transform duration-200 ease-out ${
        chunk ? "translate-x-0" : "translate-x-full"
      }`}
    >
      {chunk && (
        <div className="flex h-full flex-col">
          <div className="flex items-start justify-between border-b border-ink-700 p-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-ink-400">Source {chunk.rank}</div>
              <div className="mt-1 font-medium text-ink-100">{chunk.filename}</div>
              <div className="text-sm text-ink-400">Page {chunk.page}</div>
            </div>
            <button
              onClick={onClose}
              className="rounded-md p-1.5 text-ink-400 hover:bg-ink-800 hover:text-ink-100"
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 border-b border-ink-700 p-4 text-center text-xs">
            <ScoreStat label="Vector" value={chunk.vector_score} />
            <ScoreStat label="BM25" value={chunk.bm25_score} />
            <ScoreStat label="Fused (RRF)" value={chunk.fused_score} />
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-200">{chunk.text}</p>
          </div>
        </div>
      )}
    </aside>
  );
}

function ScoreStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-ink-800 py-2">
      <div className="text-ink-400">{label}</div>
      <div className="font-mono text-sm text-ink-100">{value.toFixed(3)}</div>
    </div>
  );
}
