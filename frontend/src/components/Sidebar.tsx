import { AlertCircle, Loader2, Plus, RefreshCw, Trash2, Upload, X } from "lucide-react";
import { useState } from "react";
import type { ConversationItem, DocumentItem } from "../types";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { Tabs, TabsList, TabsTrigger } from "./ui/tabs";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";
import { Button } from "./ui/button";
import { UploadDropzone } from "./UploadDropzone";

interface Props {
  documents: DocumentItem[];
  onUpload: (files: File[]) => void;
  onDeleteDocument: (id: string) => void;
  onReindexDocument: (id: string) => void;
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
  onReindexDocument,
  uploading,
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  view,
  onChangeView,
}: Props) {
  const [uploadOpen, setUploadOpen] = useState(false);

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r border-ink-700 bg-ink-900">
      <div className="flex items-center gap-2 px-4 pb-2 pt-5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-500 text-sm font-bold text-white">
          C
        </div>
        <div>
          <div className="text-sm font-semibold leading-tight text-ink-100">Chat With Your Docs</div>
          <div className="text-[11px] text-ink-500">Ask your documents anything</div>
        </div>
      </div>

      <Tabs value={view} onValueChange={(v) => onChangeView(v as "chat" | "observability")} className="mx-4 mt-3">
        <TabsList className="w-full">
          <TabsTrigger value="chat">Chat</TabsTrigger>
          <TabsTrigger value="observability">Observability</TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="mt-4 px-4">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wide text-ink-400">Documents</h3>
          <Dialog open={uploadOpen} onOpenChange={setUploadOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm" className="gap-1">
                <Upload className="h-3 w-3" />
                Upload
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Upload documents</DialogTitle>
                <DialogDescription>PDF, TXT, or Markdown — up to 20MB each.</DialogDescription>
              </DialogHeader>
              <div className="p-4">
                <UploadDropzone
                  disabled={uploading}
                  onFiles={(files) => {
                    onUpload(files);
                  }}
                />
                {uploading && (
                  <p className="mt-2 flex items-center justify-center gap-1.5 text-xs text-brand-300">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Indexing…
                  </p>
                )}
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="mt-1 flex-1 space-y-1 overflow-y-auto px-4">
        {documents.length === 0 && <p className="py-4 text-center text-xs text-ink-500">No documents yet</p>}
        {documents.map((doc) => (
          <DocumentRow key={doc.id} doc={doc} onDelete={onDeleteDocument} onReindex={onReindexDocument} />
        ))}
      </div>

      {view === "chat" && (
        <div className="border-t border-ink-700 p-4">
          <Button variant="outline" size="sm" onClick={onNewConversation} className="mb-2 w-full gap-1.5">
            <Plus className="h-3.5 w-3.5" />
            New conversation
          </Button>
          <div className="max-h-40 space-y-1 overflow-y-auto">
            {conversations.map((c) => (
              <div
                key={c.id}
                onClick={() => onSelectConversation(c.id)}
                className={`group flex cursor-pointer items-center justify-between rounded-md px-2 py-1.5 text-xs ${
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
                  aria-label={`Delete conversation "${c.title}"`}
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}

function DocumentRow({
  doc,
  onDelete,
  onReindex,
}: {
  doc: DocumentItem;
  onDelete: (id: string) => void;
  onReindex: (id: string) => void;
}) {
  const isProcessing = doc.status === "processing";

  return (
    <div className="group flex items-start justify-between gap-2 rounded-md border border-ink-700/60 bg-ink-800/50 px-2.5 py-2">
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <StatusDot status={doc.status} />
          <span className="truncate text-xs font-medium text-ink-200" title={doc.filename}>
            {doc.filename}
          </span>
        </div>
        <div className="mt-0.5 flex items-center gap-1 text-[11px] text-ink-500">
          {doc.status === "ready" && `${doc.num_pages} pages · ${doc.num_chunks} chunks`}
          {doc.status === "processing" && "Processing…"}
          {doc.status === "failed" && (
            <>
              <AlertCircle className="h-3 w-3 shrink-0 text-red-400" />
              <span className="truncate">{doc.error || "Failed to process"}</span>
            </>
          )}
        </div>
      </div>
      <div className="flex shrink-0 items-center opacity-0 transition-opacity group-hover:opacity-100">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              disabled={isProcessing}
              onClick={() => onReindex(doc.id)}
              aria-label={`Reindex ${doc.filename}`}
            >
              <RefreshCw className="h-3.5 w-3.5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Reindex</TooltipContent>
        </Tooltip>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 hover:text-red-300"
              onClick={() => onDelete(doc.id)}
              aria-label={`Delete ${doc.filename}`}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Delete</TooltipContent>
        </Tooltip>
      </div>
    </div>
  );
}

function StatusDot({ status }: { status: DocumentItem["status"] }) {
  const color = status === "ready" ? "bg-emerald-400" : status === "processing" ? "bg-amber-400 animate-pulse" : "bg-red-400";
  return <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${color}`} />;
}
