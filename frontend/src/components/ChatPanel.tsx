import { useEffect, useRef, useState } from "react";
import { api, streamChat } from "../api";
import type { ChatMessage, RetrievedChunk } from "../types";
import { MessageBubble } from "./MessageBubble";
import { SourcesDrawer } from "./SourcesDrawer";
import { StatusIndicator } from "./StatusIndicator";

interface Props {
  conversationId: string | null;
  onConversationId: (id: string) => void;
  hasDocuments: boolean;
}

let idCounter = 0;
const localId = () => `local-${Date.now()}-${idCounter++}`;

export function ChatPanel({ conversationId, onConversationId, hasDocuments }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [stage, setStage] = useState<"retrieving" | "generating" | null>(null);
  const [activeChunk, setActiveChunk] = useState<RetrievedChunk | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!conversationId) {
      setMessages([]);
      return;
    }
    let cancelled = false;
    (async () => {
      const msgs = await api.getMessages(conversationId);
      const withSources = await Promise.all(
        msgs.map(async (m) => {
          let sources: RetrievedChunk[] = [];
          let lowConfidence = false;
          if (m.trace_id) {
            try {
              const trace = await api.getTrace(m.trace_id);
              sources = trace.retrieved;
              lowConfidence = trace.low_confidence;
            } catch {
              // trace may have been pruned; degrade gracefully
            }
          }
          const chatMsg: ChatMessage = {
            id: m.id,
            role: m.role,
            content: m.content,
            sources,
            lowConfidence,
            streaming: false,
            traceId: m.trace_id ?? undefined,
          };
          return chatMsg;
        })
      );
      if (!cancelled) setMessages(withSources);
    })();
    return () => {
      cancelled = true;
    };
  }, [conversationId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, stage]);

  async function handleSend() {
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput("");
    setIsStreaming(true);
    setStage("retrieving");

    const userMsg: ChatMessage = { id: localId(), role: "user", content: text, sources: [], lowConfidence: false, streaming: false };
    const assistantMsg: ChatMessage = { id: localId(), role: "assistant", content: "", sources: [], lowConfidence: false, streaming: true };
    setMessages((prev) => [...prev, userMsg, assistantMsg]);

    const controller = new AbortController();
    abortRef.current = controller;

    await streamChat(
      text,
      conversationId,
      (event) => {
        if (event.type === "meta") {
          if (!conversationId) onConversationId(event.conversation_id);
        } else if (event.type === "status") {
          setStage(event.stage);
        } else if (event.type === "sources") {
          setStage("generating");
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsg.id ? { ...m, sources: event.sources, lowConfidence: event.low_confidence } : m))
          );
        } else if (event.type === "delta") {
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsg.id ? { ...m, content: m.content + event.text } : m))
          );
        } else if (event.type === "done") {
          setStage(null);
          setMessages((prev) =>
            prev.map((m) => (m.id === assistantMsg.id ? { ...m, streaming: false, traceId: event.trace_id } : m))
          );
        } else if (event.type === "error") {
          setStage(null);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantMsg.id ? { ...m, streaming: false, content: `⚠️ ${event.message}` } : m
            )
          );
        }
      },
      controller.signal
    );

    setIsStreaming(false);
    setStage(null);
  }

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-6 sm:px-8">
        {messages.length === 0 && <EmptyState hasDocuments={hasDocuments} />}
        {messages.map((m) => (
          <MessageBubble
            key={m.id}
            message={m}
            onSelectSource={(chunk) => setActiveChunk(chunk)}
            activeChunkId={activeChunk?.chunk_id}
          />
        ))}
        {stage && <StatusIndicator stage={stage} />}
      </div>

      <div className="border-t border-ink-700 bg-ink-900/80 p-4 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-ink-600 bg-ink-800 p-2 focus-within:border-brand-400">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={hasDocuments ? "Ask a question about your documents…" : "Upload a document to get started…"}
            rows={1}
            className="max-h-40 flex-1 resize-none bg-transparent px-2 py-2 text-[15px] text-ink-100 placeholder:text-ink-500 focus:outline-none"
          />
          <button
            onClick={handleSend}
            disabled={isStreaming || !input.trim()}
            className="mb-0.5 rounded-xl bg-brand-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-400 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isStreaming ? "…" : "Send"}
          </button>
        </div>
        <p className="mx-auto mt-2 max-w-3xl text-center text-xs text-ink-500">
          DocuMind answers only from your uploaded documents and cites its sources — it will say so when it doesn't know.
        </p>
      </div>

      <SourcesDrawer chunk={activeChunk} onClose={() => setActiveChunk(null)} />
    </div>
  );
}

function EmptyState({ hasDocuments }: { hasDocuments: boolean }) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-2 py-24 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-500/15 text-2xl">💬</div>
      <h2 className="text-lg font-medium text-ink-100">
        {hasDocuments ? "Ask anything about your documents" : "Start by uploading a document"}
      </h2>
      <p className="max-w-sm text-sm text-ink-400">
        {hasDocuments
          ? "DocuMind retrieves the most relevant excerpts and answers with citations you can inspect."
          : "Use the sidebar to upload a PDF, text, or Markdown file — then come back here to ask questions about it."}
      </p>
    </div>
  );
}
