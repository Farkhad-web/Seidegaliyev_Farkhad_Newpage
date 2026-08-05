export type DocumentStatus = "processing" | "ready" | "failed";

export interface DocumentItem {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  num_pages: number;
  num_chunks: number;
  status: DocumentStatus;
  error: string | null;
  created_at: string;
}

export interface ConversationItem {
  id: string;
  title: string;
  created_at: string;
  message_count: number;
}

export interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  trace_id: string | null;
  created_at: string;
}

export interface RetrievedChunk {
  chunk_id: string;
  document_id: string;
  filename: string;
  page: number;
  text: string;
  vector_score: number;
  bm25_score: number;
  fused_score: number;
  rank: number;
}

export interface TraceSummary {
  id: string;
  conversation_id: string;
  raw_query: string;
  confidence: number;
  low_confidence: boolean;
  model: string;
  total_latency_ms: number;
  created_at: string;
}

export interface TraceDetail extends TraceSummary {
  condensed_query: string | null;
  retrieved: RetrievedChunk[];
  answer: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: Record<string, number>;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources: RetrievedChunk[];
  lowConfidence: boolean;
  streaming: boolean;
  traceId?: string;
}

export type ChatEvent =
  | { type: "meta"; conversation_id: string }
  | { type: "status"; stage: "retrieving" | "generating" }
  | { type: "sources"; sources: RetrievedChunk[]; low_confidence: boolean; confidence: number }
  | { type: "delta"; text: string }
  | { type: "done"; trace_id: string; conversation_id: string }
  | { type: "error"; message: string };
