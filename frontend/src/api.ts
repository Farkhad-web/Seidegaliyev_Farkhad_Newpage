import type { ChatEvent, ConversationItem, DocumentItem, MessageItem, TraceDetail, TraceSummary } from "./types";

const BASE = "/api";

async function asJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  listDocuments: () => fetch(`${BASE}/documents`).then((r) => asJson<DocumentItem[]>(r)),

  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${BASE}/documents`, { method: "POST", body: form }).then((r) => asJson<DocumentItem>(r));
  },

  deleteDocument: (id: string) => fetch(`${BASE}/documents/${id}`, { method: "DELETE" }).then((r) => {
    if (!r.ok) throw new Error("Failed to delete document");
  }),

  listConversations: () => fetch(`${BASE}/conversations`).then((r) => asJson<ConversationItem[]>(r)),

  getMessages: (conversationId: string) =>
    fetch(`${BASE}/conversations/${conversationId}/messages`).then((r) => asJson<MessageItem[]>(r)),

  deleteConversation: (id: string) =>
    fetch(`${BASE}/conversations/${id}`, { method: "DELETE" }).then((r) => {
      if (!r.ok) throw new Error("Failed to delete conversation");
    }),

  listTraces: () => fetch(`${BASE}/traces`).then((r) => asJson<TraceSummary[]>(r)),

  getTrace: (id: string) => fetch(`${BASE}/traces/${id}`).then((r) => asJson<TraceDetail>(r)),

  health: () => fetch(`${BASE}/health`).then((r) => asJson<Record<string, unknown>>(r)),
};

/** Streams a chat turn over SSE-over-POST. `fetch` + a manual line parser is
 * used instead of `EventSource` because EventSource can't send a POST body. */
export async function streamChat(
  message: string,
  conversationId: string | null,
  onEvent: (event: ChatEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, conversation_id: conversationId }),
    signal,
  });

  if (!res.ok || !res.body) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    onEvent({ type: "error", message: detail });
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");

    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";

    for (const block of blocks) {
      const dataLine = block.split("\n").find((line) => line.startsWith("data:"));
      if (!dataLine) continue;
      const payload = dataLine.slice("data:".length).trim();
      if (!payload) continue;
      try {
        onEvent(JSON.parse(payload) as ChatEvent);
      } catch {
        // ignore malformed frame
      }
    }
  }
}
