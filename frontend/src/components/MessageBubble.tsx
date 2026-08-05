import { Check, Copy } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useSmoothedText } from "../hooks/useSmoothedText";
import type { ChatMessage, RetrievedChunk } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { SourceChips } from "./SourceChips";
import { Button } from "./ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

interface Props {
  message: ChatMessage;
  onSelectSource: (chunk: RetrievedChunk) => void;
  activeChunkId?: string;
}

// turns "...deficiency [1][3]." into real markdown links so ReactMarkdown's
// own link renderer can turn them into citation badges — no AST plugin needed
function linkifyCitations(markdown: string): string {
  return markdown.replace(/\[(\d+)\](?!\()/g, "[$1](#cite-$1)");
}

export function MessageBubble({ message, onSelectSource, activeChunkId }: Props) {
  const isUser = message.role === "user";
  const displayContent = useSmoothedText(message.content, message.streaming);
  const [copied, setCopied] = useState(false);

  const sourceByRank = new Map(message.sources.map((s) => [String(s.rank), s]));

  function handleCitationClick(rank: string) {
    const chunk = sourceByRank.get(rank);
    if (chunk) onSelectSource(chunk);
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.15, ease: "easeOut" }}
      className={`group flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div className={`max-w-[75ch] ${isUser ? "order-2" : ""}`}>
        <div
          className={`rounded-lg px-4 py-3 text-[15px] leading-relaxed ${
            isUser ? "bg-brand-500 text-white" : "border border-ink-700 bg-ink-800 text-ink-100"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="markdown-body">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a({ href, children, ...props }) {
                    if (href?.startsWith("#cite-")) {
                      const rank = href.replace("#cite-", "");
                      return (
                        <button
                          type="button"
                          onClick={() => handleCitationClick(rank)}
                          className={`mx-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-sm px-1 align-text-top text-[10px] font-semibold transition-colors ${
                            activeChunkId === sourceByRank.get(rank)?.chunk_id
                              ? "bg-brand-500 text-white"
                              : "bg-ink-700 text-ink-300 hover:bg-brand-500/40 hover:text-brand-100"
                          }`}
                        >
                          {rank}
                        </button>
                      );
                    }
                    return (
                      <a href={href} {...props} target="_blank" rel="noreferrer">
                        {children}
                      </a>
                    );
                  },
                }}
              >
                {linkifyCitations(displayContent) || " "}
              </ReactMarkdown>
              {message.streaming && (
                <span className="ml-0.5 inline-block h-4 w-1.5 animate-blink bg-ink-300 align-middle" />
              )}
            </div>
          )}
        </div>

        {!isUser && !message.streaming && message.content && (
          <div className="mt-1 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleCopy} aria-label="Copy answer">
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </TooltipTrigger>
              <TooltipContent>{copied ? "Copied" : "Copy answer"}</TooltipContent>
            </Tooltip>
          </div>
        )}

        {!isUser && !message.streaming && message.sources.length > 0 && (
          <div className="mt-1 flex items-center gap-2">
            <ConfidenceBadge confidence={maxScore(message.sources)} lowConfidence={message.lowConfidence} />
          </div>
        )}
        {!isUser && (
          <SourceChips sources={message.sources} onSelect={onSelectSource} activeChunkId={activeChunkId} />
        )}
      </div>
    </motion.div>
  );
}

function maxScore(sources: RetrievedChunk[]): number {
  return sources.reduce((max, s) => Math.max(max, s.vector_score), 0);
}
