import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ChatMessage, RetrievedChunk } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { SourceChips } from "./SourceChips";

interface Props {
  message: ChatMessage;
  onSelectSource: (chunk: RetrievedChunk) => void;
  activeChunkId?: string;
}

export function MessageBubble({ message, onSelectSource, activeChunkId }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex animate-fadeIn ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[75ch] ${isUser ? "order-2" : ""}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-[15px] leading-relaxed ${
            isUser
              ? "bg-brand-500 text-white"
              : "border border-ink-700 bg-ink-800 text-ink-100"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content || " "}
              </ReactMarkdown>
              {message.streaming && <span className="ml-0.5 inline-block h-4 w-1.5 animate-blink bg-ink-300 align-middle" />}
            </div>
          )}
        </div>

        {!isUser && !message.streaming && message.sources.length > 0 && (
          <div className="mt-1.5 flex items-center gap-2">
            <ConfidenceBadge confidence={maxScore(message.sources)} lowConfidence={message.lowConfidence} />
          </div>
        )}
        {!isUser && <SourceChips sources={message.sources} onSelect={onSelectSource} activeChunkId={activeChunkId} />}
      </div>
    </div>
  );
}

function maxScore(sources: RetrievedChunk[]): number {
  return sources.reduce((max, s) => Math.max(max, s.vector_score), 0);
}
