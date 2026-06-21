"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { usePathname } from "next/navigation";

import { ChatMessage } from "@/components/rag/ChatMessage";
import { SuggestedQuestions, type SuggestedQuestionItem } from "@/components/rag/SuggestedQuestions";
import { useChat } from "@/components/rag/ChatContext";
import { useSessionStore } from "@/lib/stores/useSessionStore";

function resolveEventId(pathname: string): string | undefined {
  const segments = pathname.split("/").filter(Boolean);
  const eventIndex = segments.findIndex((segment) => segment === "events");
  const eventId = eventIndex >= 0 ? segments[eventIndex + 1] : undefined;
  return eventId ? decodeURIComponent(eventId) : undefined;
}

function buildSuggestedQuestions(accessLevel: string, eventId?: string): SuggestedQuestionItem[] {
  const publicQuestions: SuggestedQuestionItem[] = [
    {
      label: "Active alerts",
      question: "What active traffic issues should the public know about right now?",
    },
    {
      label: "Reporting help",
      question: "How should a citizen submit a useful traffic or congestion report?",
    },
    {
      label: "Nearby pattern",
      question: "What kinds of public traffic issues are being reported most often today?",
    },
  ];

  const operatorQuestions: SuggestedQuestionItem[] = [
    {
      label: "Current status",
      question: eventId
        ? `Give me the latest operational status for event ${eventId}.`
        : "Summarize the latest operational status across active events.",
    },
    {
      label: "Response plan",
      question: eventId
        ? `What manpower, barricade, and diversion plan is stored for event ${eventId}?`
        : "What are the latest manpower and diversion recommendations across active events?",
    },
    {
      label: "Similar history",
      question: eventId
        ? `Which similar historical events best match event ${eventId}, and what matters operationally?`
        : "Which historical event patterns are most relevant for current congestion management?",
    },
  ];

  const adminQuestions: SuggestedQuestionItem[] = [
    {
      label: "Model posture",
      question: "Summarize the current model, hotspot, and index posture for admins.",
    },
    {
      label: "Audit trail",
      question: "What recent admin or control-room actions are visible in the operational audit trail?",
    },
  ];

  if (accessLevel === "admin") {
    return [...operatorQuestions, ...adminQuestions];
  }
  if (accessLevel === "control_room" || accessLevel === "police_officer") {
    return operatorQuestions;
  }
  return publicQuestions;
}

function accessNote(accessLevel: string): string {
  if (accessLevel === "admin") {
    return "Admin answers can include internal operations, audit, model, and after-action sources.";
  }
  if (accessLevel === "control_room" || accessLevel === "police_officer") {
    return "Operational answers stay grounded in control-room data, live updates, hotspots, and stored plans.";
  }
  return "Public answers stay grounded in citizen-visible reports and public-safe summaries only.";
}

export function ChatPanel() {
  const pathname = usePathname();
  const session = useSessionStore();
  const { isOpen, isHydrating, isStreaming, error, messages, sessionId, togglePanel, closePanel, sendQuestion, clearConversation } = useChat();
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const currentEventId = useMemo(() => resolveEventId(pathname), [pathname]);
  const suggestions = useMemo(
    () => buildSuggestedQuestions(session.accessLevel, currentEventId),
    [currentEventId, session.accessLevel]
  );

  useEffect(() => {
    const node = scrollRef.current;
    if (!node) {
      return;
    }
    node.scrollTop = node.scrollHeight;
  }, [messages, isOpen]);

  async function submitDraft(question: string) {
    const trimmed = question.trim();
    if (!trimmed) {
      return;
    }
    setDraft("");
    await sendQuestion(trimmed, { eventId: currentEventId });
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitDraft(draft);
  }

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={togglePanel}
        className="fixed bottom-5 right-5 z-50 rounded-full border border-cyan-400/40 bg-slate-950/90 px-5 py-3 text-sm font-semibold uppercase tracking-[0.24em] text-cyan-200 shadow-[0_20px_60px_rgba(15,23,42,0.45)] backdrop-blur transition hover:border-cyan-300 hover:text-white"
      >
        Ask Sanchar Sarthi
      </button>
    );
  }

  return (
    <aside className="fixed bottom-5 right-5 z-50 flex h-[min(760px,82vh)] w-[min(440px,calc(100vw-1.5rem))] flex-col overflow-hidden rounded-[28px] border border-slate-800 bg-slate-950/96 text-slate-100 shadow-[0_35px_100px_rgba(2,6,23,0.65)] backdrop-blur">
      <header className="border-b border-slate-800 px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.32em] text-cyan-300">Grounded RAG Copilot</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-white">Traffic command assistant</h2>
            <p className="mt-2 text-sm leading-6 text-slate-300">{accessNote(session.accessLevel)}</p>
          </div>
          <button
            type="button"
            onClick={closePanel}
            className="rounded-full border border-slate-700 px-3 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-300 transition hover:border-slate-500 hover:text-white"
          >
            Close
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2 text-xs uppercase tracking-[0.18em] text-slate-400">
          <span className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-2">Role {session.accessLevel.replace(/_/g, " ")}</span>
          {currentEventId ? <span className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-2">Event {currentEventId}</span> : null}
          {sessionId ? <span className="rounded-full border border-slate-800 bg-slate-900/70 px-3 py-2">Session active</span> : null}
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {!messages.length ? (
          <section className="rounded-3xl border border-dashed border-slate-800 bg-slate-900/50 p-4">
            <p className="text-sm leading-7 text-slate-300">
              Ask for active incidents, similar event memory, recommendations, hotspot risk, or public-safe summaries.
            </p>
            <div className="mt-4">
              <SuggestedQuestions items={suggestions} disabled={isHydrating || isStreaming} onSelect={(question) => void submitDraft(question)} />
            </div>
          </section>
        ) : null}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
      </div>

      <footer className="border-t border-slate-800 px-5 py-4">
        {error ? <p className="mb-3 text-sm text-rose-300">{error}</p> : null}
        <form onSubmit={handleSubmit} className="space-y-3">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submitDraft(draft);
              }
            }}
            rows={3}
            placeholder={currentEventId ? `Ask about ${currentEventId}` : "Ask about current traffic, hotspots, incidents, or response plans"}
            className="w-full rounded-3xl border border-slate-800 bg-slate-900 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400"
          />
          <div className="flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => void clearConversation()}
              disabled={isStreaming && !messages.length}
              className="rounded-full border border-slate-700 px-4 py-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-300 transition hover:border-slate-500 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              Clear
            </button>
            <button
              type="submit"
              disabled={isHydrating || isStreaming || !draft.trim()}
              className="rounded-full bg-cyan-400 px-5 py-3 text-xs font-semibold uppercase tracking-[0.22em] text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isStreaming ? "Streaming..." : "Send"}
            </button>
          </div>
        </form>
      </footer>
    </aside>
  );
}
