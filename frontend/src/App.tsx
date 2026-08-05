import { Menu } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { ObservabilityPanel } from "./components/ObservabilityPanel";
import { Sidebar } from "./components/Sidebar";
import { Button } from "./components/ui/button";
import { Sheet, SheetContent } from "./components/ui/sheet";
import { TooltipProvider } from "./components/ui/tooltip";
import type { ConversationItem, DocumentItem } from "./types";

export default function App() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [view, setView] = useState<"chat" | "observability">("chat");
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  async function refreshDocuments() {
    setDocuments(await api.listDocuments());
  }

  async function refreshConversations() {
    setConversations(await api.listConversations());
  }

  useEffect(() => {
    refreshDocuments();
    refreshConversations();
  }, []);

  function notify(message: string) {
    setToast(message);
    setTimeout(() => setToast(null), 4000);
  }

  async function handleUpload(files: File[]) {
    setUploading(true);
    for (const file of files) {
      try {
        await api.uploadDocument(file);
      } catch (err) {
        notify(err instanceof Error ? err.message : "Upload failed");
      }
    }
    await refreshDocuments();
    setUploading(false);
  }

  async function handleDeleteDocument(id: string) {
    await api.deleteDocument(id);
    await refreshDocuments();
  }

  async function handleReindexDocument(id: string) {
    setDocuments((prev) => prev.map((d) => (d.id === id ? { ...d, status: "processing" } : d)));
    try {
      await api.reindexDocument(id);
    } catch (err) {
      notify(err instanceof Error ? err.message : "Reindex failed");
    }
    await refreshDocuments();
  }

  function handleNewConversation() {
    setConversationId(null);
  }

  async function handleSelectConversation(id: string) {
    setConversationId(id);
    setView("chat");
  }

  async function handleDeleteConversation(id: string) {
    await api.deleteConversation(id);
    if (conversationId === id) setConversationId(null);
    await refreshConversations();
  }

  function handleConversationId(id: string) {
    setConversationId(id);
    refreshConversations();
  }

  // Navigating from the mobile drawer should dismiss it so the user sees
  // the result immediately, instead of having to close it by hand.
  function withMobileClose<A extends unknown[]>(fn: (...args: A) => void) {
    return (...args: A) => {
      fn(...args);
      setMobileSidebarOpen(false);
    };
  }

  const readyDocuments = documents.filter((d) => d.status === "ready");

  const sidebarProps = {
    documents,
    onUpload: handleUpload,
    onDeleteDocument: handleDeleteDocument,
    onReindexDocument: handleReindexDocument,
    uploading,
    conversations,
    activeConversationId: conversationId,
  };

  return (
    <TooltipProvider delayDuration={200}>
      <div className="flex h-screen flex-col bg-ink-950 text-ink-100 md:flex-row">
        {/* Desktop: sidebar is always in-flow. Mobile: collapses into a Sheet
            triggered from the top bar below — two renders of <Sidebar>, one
            hidden per breakpoint, is the standard way to avoid re-deriving
            "is this a mobile viewport" in JS just to flip a layout mode. */}
        <div className="hidden h-full md:block">
          <Sidebar
            {...sidebarProps}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            onDeleteConversation={handleDeleteConversation}
            view={view}
            onChangeView={setView}
          />
        </div>

        <div className="flex items-center gap-2 border-b border-ink-700 bg-ink-900 px-3 py-2 md:hidden">
          <Button variant="ghost" size="icon" onClick={() => setMobileSidebarOpen(true)} aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </Button>
          <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-brand-500 text-xs font-bold text-white">
            C
          </div>
          <span className="text-sm font-semibold text-ink-100">Chat With Your Docs</span>
        </div>

        <Sheet open={mobileSidebarOpen} onOpenChange={setMobileSidebarOpen}>
          <SheetContent side="left" className="w-72 max-w-[85vw] p-0">
            <Sidebar
              {...sidebarProps}
              onSelectConversation={withMobileClose(handleSelectConversation)}
              onNewConversation={withMobileClose(handleNewConversation)}
              onDeleteConversation={handleDeleteConversation}
              view={view}
              onChangeView={withMobileClose(setView)}
            />
          </SheetContent>
        </Sheet>

        <main className="relative flex-1 overflow-hidden">
          {view === "chat" ? (
            <ChatPanel conversationId={conversationId} onConversationId={handleConversationId} hasDocuments={readyDocuments.length > 0} />
          ) : (
            <ObservabilityPanel />
          )}
        </main>

        {toast && (
          <div className="fixed bottom-4 right-4 z-50 rounded-lg border border-red-500/30 bg-ink-800 px-4 py-2 text-sm text-red-300 shadow-soft">
            {toast}
          </div>
        )}
      </div>
    </TooltipProvider>
  );
}
