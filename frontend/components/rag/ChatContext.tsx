"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { ApiError } from "@/lib/api";
import {
  deleteRagHistory,
  getRagHistory,
  streamRagChat,
  type RagSource,
} from "@/lib/ragApi";

const SESSION_STORAGE_KEY = "sanchar-sarthi.rag.session";

export type RagChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
  sources: RagSource[];
  pending?: boolean;
  error?: boolean;
};

type ChatContextValue = {
  isOpen: boolean;
  isHydrating: boolean;
  isStreaming: boolean;
  error: string | null;
  sessionId: string | null;
  messages: RagChatMessage[];
  openPanel: () => void;
  closePanel: () => void;
  togglePanel: () => void;
  sendQuestion: (question: string, options?: { eventId?: string }) => Promise<void>;
  clearConversation: () => Promise<void>;
};

const ChatContext = createContext<ChatContextValue | null>(null);

function createMessageId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `rag-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function resolveErrorText(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.body) as { error?: { message?: string } };
      return parsed.error?.message || error.body;
    } catch {
      return error.body;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "RAG chat failed.";
}

function hydrateMessages(
  messages: Array<{ role: string; content: string; created_at: string; sources: RagSource[] }>
): RagChatMessage[] {
  return messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) => ({
      id: createMessageId(),
      role: message.role as "user" | "assistant",
      content: message.content,
      createdAt: message.created_at,
      sources: message.role === "assistant" ? message.sources : [],
    }));
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isHydrating, setIsHydrating] = useState(true);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<RagChatMessage[]>([]);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (typeof window === "undefined") {
      setIsHydrating(false);
      return () => undefined;
    }

    const storedSessionId = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!storedSessionId) {
      setIsHydrating(false);
      return () => undefined;
    }

    setSessionId(storedSessionId);
    getRagHistory(storedSessionId)
      .then((history) => {
        if (cancelled) {
          return;
        }
        setSessionId(history.session_id);
        setMessages(hydrateMessages(history.messages));
      })
      .catch(() => {
        if (typeof window !== "undefined") {
          window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
        }
        if (!cancelled) {
          setSessionId(null);
          setMessages([]);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsHydrating(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const clearConversation = useCallback(async () => {
    const activeSessionId = sessionId;
    abortRef.current?.abort();
    abortRef.current = null;
    setIsStreaming(false);
    setError(null);
    setMessages([]);
    setSessionId(null);
    if (typeof window !== "undefined") {
      window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
    }
    if (activeSessionId) {
      try {
        await deleteRagHistory(activeSessionId);
      } catch {
        // Keep the client clean even if the server session already expired.
      }
    }
  }, [sessionId]);

  const sendQuestion = useCallback(
    async (question: string, options?: { eventId?: string }) => {
      const trimmed = question.trim();
      if (!trimmed || isStreaming) {
        return;
      }

      const userMessage: RagChatMessage = {
        id: createMessageId(),
        role: "user",
        content: trimmed,
        createdAt: new Date().toISOString(),
        sources: [],
      };
      const assistantId = createMessageId();

      setIsOpen(true);
      setIsStreaming(true);
      setError(null);
      setMessages((current) => [
        ...current,
        userMessage,
        {
          id: assistantId,
          role: "assistant",
          content: "",
          createdAt: new Date().toISOString(),
          sources: [],
          pending: true,
        },
      ]);

      const controller = new AbortController();
      abortRef.current = controller;

      try {
        await streamRagChat(
          {
            question: trimmed,
            session_id: sessionId ?? undefined,
            event_id: options?.eventId,
          },
          {
            signal: controller.signal,
            onEvent: (event) => {
              if (event.type === "token") {
                setMessages((current) =>
                  current.map((message) =>
                    message.id === assistantId
                      ? { ...message, content: `${message.content}${event.content}` }
                      : message
                  )
                );
                return;
              }

              if (event.type === "done") {
                setSessionId(event.session_id);
                if (typeof window !== "undefined") {
                  window.sessionStorage.setItem(SESSION_STORAGE_KEY, event.session_id);
                }
                setMessages((current) =>
                  current.map((message) =>
                    message.id === assistantId
                      ? {
                          ...message,
                          pending: false,
                          content: message.content || "No grounded answer was returned.",
                          sources: event.sources,
                        }
                      : message
                  )
                );
                return;
              }

              setError(event.message || "RAG chat failed.");
              setMessages((current) =>
                current.map((message) =>
                  message.id === assistantId
                    ? {
                        ...message,
                        pending: false,
                        error: true,
                        content: message.content || event.message || "RAG chat failed.",
                      }
                    : message
                )
              );
            },
          }
        );
      } catch (caughtError) {
        if (!controller.signal.aborted) {
          const message = resolveErrorText(caughtError);
          setError(message);
          setMessages((current) =>
            current.map((item) =>
              item.id === assistantId
                ? {
                    ...item,
                    pending: false,
                    error: true,
                    content: item.content || message,
                  }
                : item
            )
          );
        }
      } finally {
        if (abortRef.current === controller) {
          abortRef.current = null;
        }
        setIsStreaming(false);
      }
    },
    [isStreaming, sessionId]
  );

  const value = useMemo<ChatContextValue>(
    () => ({
      isOpen,
      isHydrating,
      isStreaming,
      error,
      sessionId,
      messages,
      openPanel: () => setIsOpen(true),
      closePanel: () => setIsOpen(false),
      togglePanel: () => setIsOpen((current) => !current),
      sendQuestion,
      clearConversation,
    }),
    [clearConversation, error, isHydrating, isOpen, isStreaming, messages, sendQuestion, sessionId]
  );

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat(): ChatContextValue {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used inside ChatProvider.");
  }
  return context;
}
