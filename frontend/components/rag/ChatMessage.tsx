"use client";

import { SourcesAccordion } from "@/components/rag/SourcesAccordion";
import type { RagChatMessage } from "@/components/rag/ChatContext";

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

function renderContent(content: string) {
  if (!content) return null;
  const parts = content.split(/(\*\*.*?\*\*|\*.*?\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-bold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return (
        <em key={i} className="italic">
          {part.slice(1, -1)}
        </em>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export function ChatMessage({ message }: { message: RagChatMessage }) {
  const isAssistant = message.role === "assistant";

  return (
    <article
      className={[
        "rounded-3xl border px-5 py-4 shadow-sm transition-all duration-300",
        isAssistant
          ? "border-slate-800 bg-slate-900 text-slate-100 shadow-md"
          : "border-blue-100 bg-gradient-to-br from-blue-50 to-indigo-50/50 text-slate-800",
      ].join(" ")}
    >
      <div className="flex items-center justify-between gap-3 text-[10px] font-bold uppercase tracking-[0.2em]">
        <span className={isAssistant ? "text-sky-400" : "text-indigo-600"}>
          {isAssistant ? "Namma Sarthi" : "You"}
        </span>
        <span className={isAssistant ? "text-slate-500" : "text-blue-400"}>{formatTime(message.createdAt)}</span>
      </div>
      <div className="mt-3 whitespace-pre-wrap text-[15px] leading-relaxed text-inherit">
        {message.content ? renderContent(message.content) : (message.pending ? "Thinking through the grounded context..." : "No answer returned.")}
      </div>
      {message.pending ? (
        <div className="mt-4 flex items-center gap-2 text-xs font-medium tracking-wide text-slate-400">
          <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-sky-400" />
          Streaming grounded response
        </div>
      ) : null}
      {message.error ? <p className="mt-3 text-xs font-medium text-rose-400">The assistant could not complete this answer cleanly.</p> : null}
      {isAssistant ? <div className="mt-4"><SourcesAccordion sources={message.sources} /></div> : null}
    </article>
  );
}
