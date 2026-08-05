import { useEffect, useState } from "react";
import { api } from "../api";
import type { TraceDetail, TraceSummary } from "../types";

export function ObservabilityPanel() {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [selected, setSelected] = useState<TraceDetail | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    const data = await api.listTraces();
    setTraces(data);
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function openTrace(id: string) {
    const detail = await api.getTrace(id);
    setSelected(detail);
  }

  return (
    <div className="flex h-full overflow-hidden">
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-ink-100">Observability</h2>
            <p className="text-sm text-ink-400">Every RAG turn: retrieval, confidence, latency, and token usage.</p>
          </div>
          <button
            onClick={refresh}
            className="rounded-lg border border-ink-600 px-3 py-1.5 text-xs text-ink-300 hover:border-brand-400 hover:text-brand-200"
          >
            Refresh
          </button>
        </div>

        {loading && <p className="text-sm text-ink-500">Loading…</p>}
        {!loading && traces.length === 0 && (
          <p className="rounded-lg border border-dashed border-ink-700 p-8 text-center text-sm text-ink-500">
            No traces yet — ask a question in the Chat tab to generate one.
          </p>
        )}

        <div className="overflow-hidden rounded-xl border border-ink-700">
          <table className="w-full text-left text-sm">
            <thead className="bg-ink-800 text-xs uppercase tracking-wide text-ink-400">
              <tr>
                <th className="px-4 py-2 font-medium">Query</th>
                <th className="px-4 py-2 font-medium">Model</th>
                <th className="px-4 py-2 font-medium">Confidence</th>
                <th className="px-4 py-2 font-medium">Latency</th>
                <th className="px-4 py-2 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {traces.map((t) => (
                <tr
                  key={t.id}
                  onClick={() => openTrace(t.id)}
                  className={`cursor-pointer border-t border-ink-800 transition-colors hover:bg-ink-800/60 ${
                    selected?.id === t.id ? "bg-ink-800" : ""
                  }`}
                >
                  <td className="max-w-xs truncate px-4 py-2.5 text-ink-200">{t.raw_query}</td>
                  <td className="px-4 py-2.5 text-ink-400">{t.model || "—"}</td>
                  <td className="px-4 py-2.5">
                    <span className={t.low_confidence ? "text-amber-300" : "text-emerald-300"}>
                      {Math.round(t.confidence * 100)}%
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-ink-400">{Math.round(t.total_latency_ms)}ms</td>
                  <td className="px-4 py-2.5 text-ink-500">{new Date(t.created_at).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selected && <TraceDetailPanel trace={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

function TraceDetailPanel({ trace, onClose }: { trace: TraceDetail; onClose: () => void }) {
  return (
    <div className="w-96 shrink-0 overflow-y-auto border-l border-ink-700 bg-ink-900 p-5">
      <div className="mb-4 flex items-start justify-between">
        <h3 className="text-sm font-semibold text-ink-100">Trace detail</h3>
        <button onClick={onClose} className="text-ink-500 hover:text-ink-200">
          ✕
        </button>
      </div>

      <Field label="Raw query" value={trace.raw_query} />
      {trace.condensed_query && <Field label="Condensed (standalone) query" value={trace.condensed_query} />}
      <Field label="Answer" value={trace.answer} multiline />

      <div className="mt-4 grid grid-cols-2 gap-2">
        <Stat label="Confidence" value={`${Math.round(trace.confidence * 100)}%`} />
        <Stat label="Model" value={trace.model || "—"} />
        <Stat label="Input tokens" value={String(trace.input_tokens)} />
        <Stat label="Output tokens" value={String(trace.output_tokens)} />
      </div>

      <div className="mt-4">
        <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-400">Latency breakdown</div>
        <div className="space-y-1">
          {Object.entries(trace.latency_ms).map(([key, ms]) => (
            <div key={key} className="flex items-center justify-between text-xs">
              <span className="text-ink-400">{key.replace("_ms", "").replace("_", " ")}</span>
              <span className="font-mono text-ink-200">{Math.round(ms)}ms</span>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-4">
        <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-ink-400">
          Retrieved chunks ({trace.retrieved.length})
        </div>
        <div className="space-y-2">
          {trace.retrieved.map((chunk) => (
            <div key={chunk.chunk_id} className="rounded-lg border border-ink-700 bg-ink-800/50 p-2 text-xs">
              <div className="mb-1 flex items-center justify-between text-ink-400">
                <span>
                  #{chunk.rank} · {chunk.filename} p.{chunk.page}
                </span>
                <span className="font-mono">{chunk.fused_score.toFixed(3)}</span>
              </div>
              <p className="line-clamp-3 text-ink-300">{chunk.text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Field({ label, value, multiline }: { label: string; value: string; multiline?: boolean }) {
  return (
    <div className="mb-3">
      <div className="mb-0.5 text-xs font-semibold uppercase tracking-wide text-ink-400">{label}</div>
      <p className={`text-sm text-ink-200 ${multiline ? "whitespace-pre-wrap" : "truncate"}`}>{value}</p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-ink-800 p-2 text-center">
      <div className="text-[11px] text-ink-400">{label}</div>
      <div className="text-sm font-medium text-ink-100">{value}</div>
    </div>
  );
}
