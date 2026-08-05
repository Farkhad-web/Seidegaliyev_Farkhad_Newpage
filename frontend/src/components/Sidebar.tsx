import type { ConversationItem, DocumentItem } from "../types";
import { UploadDropzone } from "./UploadDropzone";

interface Props {
  documents: DocumentItem[];
  onUpload: (files: File[]) => void;
  onDeleteDocument: (id: string) => void;
  uploading: boolean;
  conversations: ConversationItem[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  view: "chat" | "observability";
  onChangeView: (view: "chat" | "observability") => void;
}

export function Sidebar({
  documents,
  onUpload,
  onDeleteDocument,
  uploading,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  view,
  onChangeView,
}: Props) {
  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-ink-700 bg-ink-900">
      <div className="flex items-center gap-2 px-4 pb-2 pt-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-500 text-sm font-bold text-white">
          D
        </div>
        <div>
          <div className="text-sm font-semibold text-ink-100">DocuMind</div>
          <div className="text-[11px] text-ink-500">Chat with your docs</div>
        </div>
      </div>

      <div className="mx-4 mt-3 flex rounded-lg bg-ink-800 p-1 text-xs font-medium">
        <button
          onClick={() => onChangeView("chat")}
          className={`flex-1 rounded-md py-1.5 transition-colors ${view === "chat" ? "bg-ink-700 text-ink-100" : "text-ink-400 hover:text-ink-200"}`}
        >
          Chat
        </button>
        <button
          onClick={() => onChangeView("observability")}
          className={`flex-1 rounded-md py-1.5 transition-colors ${view === "observability" ? "bg-ink-700 text-ink-100" : "text-ink-400 hover:text-ink-200"}`}
        >
          Observability
        </button>
      </div>

      <div className="mt-4 px-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-400">Documents</h3>
          {uploading && <span className="text-[11px] text-brand-300">Indexing…</span>}
        </div>
        <UploadDropzone onFiles={onUpload} disabled={uploading} />
      </div>

      <div className="mt-3 flex-1 space-y-1 overflow-y-auto px-4">
        {documents.length === 0 && <p className="py-4 text-center text-xs text-ink-500">No documents yet</p>}
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="group flex items-start justify-between gap-2 rounded-lg border border-ink-700/60 bg-ink-800/50 px-2.5 py-2"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <StatusDot status={doc.status} />
                <span className="truncate text-xs font-medium text-ink-200" title={doc.filename}>
                  {doc.filename}
                </span>
              </div>
              <div className="mt-0.5 text-[11px] text-ink-500">
                {doc.status === "ready" && `${doc.num_pages} pages · ${doc.num_chunks} chunks`}
                {doc.status === "processing" && "Processing…"}
                {doc.status === "failed" && (doc.error || "Failed to process")}
              </div>
            </div>
            <button
              onClick={() => onDeleteDocument(doc.id)}
              className="shrink-0 rounded p-1 text-ink-500 opacity-0 transition hover:bg-ink-700 hover:text-red-300 group-hover:opacity-100"
              aria-label={`Delete ${doc.filename}`}
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      {view === "chat" && (
        <div className="border-t border-ink-700 p-4">
          <button
            onClick={onNewConversation}
            className="mb-2 w-full rounded-lg border border-ink-600 py-1.5 text-xs font-medium text-ink-200 transition hover:border-brand-400 hover:text-brand-200"
          >
            + New conversation
          </button>
          <div className="max-h-40 space-y-1 overflow-y-auto">
            {conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => onSelectConversation(c.id)}
                className={`group flex cursor-pointer items-center justify-between rounded-lg px-2 py-1.5 text-xs ${
                  activeConversationId === c.id ? "bg-ink-700 text-ink-100" : "text-ink-400 hover:bg-ink-800"
                }`}
              >
                <span className="truncate">{c.title}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(c.id);
                  }}
                  className="ml-2 shrink-0 opacity-0 hover:text-red-300 group-hover:opacity-100"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}

function StatusDot({ status }: { status: DocumentItem["status"] }) {
  const color = status === "ready" ? "bg-emerald-400" : status === "processing" ? "bg-amber-400 animate-pulse" : "bg-red-400";
  return <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${color}`} />;
}
