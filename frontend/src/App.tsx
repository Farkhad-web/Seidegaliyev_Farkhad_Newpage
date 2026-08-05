import { useEffect, useState } from "react";
import { api } from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { ObservabilityPanel } from "./components/ObservabilityPanel";
import { Sidebar } from "./components/Sidebar";
import type { ConversationItem, DocumentItem } from "./types";

export default function App() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [view, setView] = useState<"chat" | "observability">("chat");
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

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

  const readyDocuments = documents.filter((d) => d.status === "ready");

  return (
    <div className="flex h-screen bg-ink-950 text-ink-100">
      <Sidebar
        documents={documents}
        onUpload={handleUpload}
        onDeleteDocument={handleDeleteDocument}
        uploading={uploading}
        conversations={conversations}
        activeConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        view={view}
        onChangeView={setView}
      />

      <main className="relative flex-1 overflow-hidden">
        {view === "chat" ? (
          <ChatPanel conversationId={conversationId} onConversationId={handleConversationId} hasDocuments={readyDocuments.length > 0} />
        ) : (
          <ObservabilityPanel />
        )}
      </main>

      {toast && (
        <div className="fixed bottom-4 right-4 z-50 rounded-lg border border-red-500/30 bg-ink-800 px-4 py-2 text-sm text-red-300 shadow-lg">
          {toast}
        </div>
      )}
    </div>
  );
}
