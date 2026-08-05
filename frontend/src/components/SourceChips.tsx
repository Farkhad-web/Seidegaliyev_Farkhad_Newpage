import type { RetrievedChunk } from "../types";

interface Props {
  sources: RetrievedChunk[];
  onSelect: (chunk: RetrievedChunk) => void;
  activeChunkId?: string;
}

export function SourceChips({ sources, onSelect, activeChunkId }: Props) {
  if (sources.length === 0) return null;
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {sources.map((chunk) => (
        <button
          key={chunk.chunk_id}
          onClick={() => onSelect(chunk)}
          className={`group flex items-center gap-1 rounded-lg border px-2 py-1 text-[11px] transition-colors ${
            activeChunkId === chunk.chunk_id
              ? "border-brand-400 bg-brand-500/15 text-brand-200"
              : "border-ink-600 bg-ink-800 text-ink-300 hover:border-brand-400/60 hover:text-ink-100"
          }`}
          title={`View excerpt from ${chunk.filename}, page ${chunk.page}`}
        >
          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-ink-700 text-[10px] font-semibold text-ink-200 group-hover:bg-brand-500/30">
            {chunk.rank}
          </span>
          <span className="max-w-[10rem] truncate">{chunk.filename}</span>
          <span className="text-ink-500">p.{chunk.page}</span>
        </button>
      ))}
    </div>
  );
}
