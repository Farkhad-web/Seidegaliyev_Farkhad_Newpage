import { lazy, Suspense } from "react";
import { api } from "../api";
import type { RetrievedChunk } from "../types";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "./ui/sheet";

// react-pdf pulls in pdf.js, the single heaviest dependency in this app —
// load it only when a source panel actually needs to render a PDF page,
// not on initial page load.
const PdfSourcePreview = lazy(() => import("./PdfSourcePreview"));

interface Props {
  chunk: RetrievedChunk | null;
  onClose: () => void;
}

export function SourcesDrawer({ chunk, onClose }: Props) {
  const isPdf = chunk?.filename.toLowerCase().endsWith(".pdf") ?? false;

  return (
    <Sheet open={!!chunk} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right">
        {chunk && (
          <div className="flex h-full flex-col">
            <SheetHeader>
              <div className="text-xs uppercase tracking-wide text-ink-400">Source {chunk.rank}</div>
              <SheetTitle className="mt-1 text-base">{chunk.filename}</SheetTitle>
              <SheetDescription>Page {chunk.page}</SheetDescription>
            </SheetHeader>

            <div className="grid grid-cols-3 gap-2 border-b border-ink-700 p-4 text-center text-xs">
              <ScoreStat label="Vector" value={chunk.vector_score} />
              <ScoreStat label="BM25" value={chunk.bm25_score} />
              <ScoreStat label="Fused (RRF)" value={chunk.fused_score} />
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {isPdf && (
                <div className="mb-4 flex justify-center">
                  <Suspense fallback={<div className="h-[440px] w-[340px] animate-pulse rounded-md bg-ink-800" />}>
                    <PdfSourcePreview fileUrl={api.documentFileUrl(chunk.document_id)} page={chunk.page} />
                  </Suspense>
                </div>
              )}
              <div className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-ink-400">
                Matched excerpt
              </div>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-200">{chunk.text}</p>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

function ScoreStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md bg-ink-800 py-2">
      <div className="text-ink-400">{label}</div>
      <div className="font-mono text-sm text-ink-100">{value.toFixed(3)}</div>
    </div>
  );
}
