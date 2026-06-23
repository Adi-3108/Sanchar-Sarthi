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
        className="fixed bottom-5 right-5 z-50 flex h-20 w-20 items-center justify-center rounded-full border-2 border-blue-500 bg-white shadow-xl transition-all hover:-translate-y-1 hover:shadow-2xl active:scale-95 active:translate-y-0 overflow-hidden"
        aria-label="Ask Namma Sarthi"
      >
        <img src="/namma_sarthi.png" alt="Namma Sarthi" className="h-full w-full object-cover" />
      </button>
    );
  }

  return (
    <aside className="fixed bottom-5 right-5 z-50 flex h-[min(760px,82vh)] w-[min(440px,calc(100vw-1.5rem))] flex-col overflow-hidden rounded-3xl border border-slate-200 bg-white/95 text-slate-900 shadow-2xl backdrop-blur-md">
      <header className="border-b border-slate-100 bg-slate-50/50 px-5 py-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.32em] text-blue-600">Namma Sarthi Copilot</p>
            <h2 className="mt-1 text-xl font-bold tracking-tight text-slate-900">Namma Sarthi AI Assistant</h2>
            <p className="mt-1 text-xs leading-relaxed text-slate-600">{accessNote(session.accessLevel)}</p>
          </div>
          <button
            type="button"
            onClick={closePanel}
            className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500 shadow-sm transition hover:border-slate-300 hover:text-slate-900 hover:bg-slate-50 active:scale-95"
          >
            Close
          </button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2 text-[10px] font-bold uppercase tracking-widest text-slate-500">
          <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 shadow-sm">Role {session.accessLevel.replace(/_/g, " ")}</span>
          {currentEventId ? <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 shadow-sm">Event {currentEventId}</span> : null}
          {sessionId ? <span className="rounded-full border border-emerald-200 bg-emerald-50 text-emerald-700 px-2.5 py-1 shadow-sm">Session active</span> : null}
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
        {!messages.length ? (
          <section className="rounded-2xl border-2 border-dashed border-slate-200 bg-slate-50 p-5">
            <div className="flex items-start gap-4 mb-2">
              <img src="/namma_sarthi.png" alt="Namma Sarthi" className="h-12 w-12 rounded-full border border-slate-200 object-cover shadow-sm" />
              <p className="text-sm font-medium leading-relaxed text-slate-600">
                <span className="block font-bold text-slate-800 text-base mb-1">Hello, I am Namma Sarthi!</span>
                Ask me about active incidents, similar event memory, recommendations, hotspot risk, or public-safe summaries.
              </p>
            </div>
            <div className="mt-4">
              <SuggestedQuestions items={suggestions} disabled={isHydrating || isStreaming} onSelect={(question) => void submitDraft(question)} />
            </div>
          </section>
        ) : null}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
      </div>

      <footer className="border-t border-slate-100 bg-slate-50/50 px-5 py-4">
        {error ? <p className="mb-3 text-sm font-medium text-rose-600">{error}</p> : null}
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
            rows={2}
            placeholder={currentEventId ? `Ask about ${currentEventId}...` : "Ask about current traffic, hotspots, or response plans..."}
            className="w-full resize-none rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-inner outline-none transition placeholder:text-slate-400 focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
          />
          <div className="flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => void clearConversation()}
              disabled={isStreaming && !messages.length}
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-[10px] font-bold uppercase tracking-widest text-slate-500 shadow-sm transition hover:bg-slate-50 hover:text-slate-900 active:scale-95 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Clear
            </button>
            <button
              type="submit"
              disabled={isHydrating || isStreaming || !draft.trim()}
              className="rounded-full bg-blue-600 px-5 py-2 text-[10px] font-bold uppercase tracking-widest text-white shadow-sm shadow-blue-500/30 transition-all hover:-translate-y-0.5 hover:bg-blue-500 hover:shadow-md active:scale-95 disabled:hover:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isStreaming ? "Streaming..." : "Send"}
            </button>
          </div>
        </form>
      </footer>
    </aside>
  );
}
