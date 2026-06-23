"use client";

import { SourcesAccordion } from "@/components/rag/SourcesAccordion";
import type { RagChatMessage } from "@/components/rag/ChatContext";

function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
}

export function ChatMessage({ message }: { message: RagChatMessage }) {
  const isAssistant = message.role === "assistant";

  return (
    <article
      className={[
        "rounded-3xl border px-4 py-3 shadow-sm transition-colors",
        isAssistant
          ? "border-slate-800 bg-slate-900/90 text-slate-100"
          : "border-cyan-500/30 bg-cyan-500/10 text-cyan-50",
      ].join(" ")}
    >
      <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.24em]">
        <span className={isAssistant ? "text-sky-300" : "text-cyan-200"}>
          {isAssistant ? "Namma Sarthi" : "You"}
        </span>
        <span className="text-slate-400">{formatTime(message.createdAt)}</span>
      </div>
      <div className="mt-3 whitespace-pre-wrap text-sm leading-7 text-inherit">
        {message.content || (message.pending ? "Thinking through the grounded context..." : "No answer returned.")}
      </div>
      {message.pending ? (
        <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
          <span className="inline-flex h-2 w-2 animate-pulse rounded-full bg-sky-300" />
          Streaming grounded response
        </div>
      ) : null}
      {message.error ? <p className="mt-3 text-xs text-rose-300">The assistant could not complete this answer cleanly.</p> : null}
      {isAssistant ? <SourcesAccordion sources={message.sources} /> : null}
    </article>
  );
}
