import { API_BASE_URL, ApiError, apiDelete, apiGet, apiPost } from "@/lib/api";
import { authHeaders } from "@/lib/authHeaders";

export type RagSource = {
  chunk_type: string;
  source_id: string;
  similarity: number;
};

export type RagHistoryMessage = {
  role: string;
  content: string;
  created_at: string;
  sources: RagSource[];
};

export type RagHistoryResponse = {
  session_id: string;
  role: string;
  expires_at: string;
  messages: RagHistoryMessage[];
};

export type RagIndexStatusResponse = {
  enabled: boolean;
  llm_provider: string;
  embedding_provider: string;
  chunk_count: number;
  by_visibility: Record<string, number>;
  by_type: Record<string, number>;
  latest_updated_at?: string | null;
};

export type RagIndexRefreshResponse = {
  status: string;
  records_indexed: number;
  chunks_upserted: number;
  chunk_types: Record<string, number>;
  event_id?: string | null;
};

export type RagChatPayload = {
  question: string;
  session_id?: string;
  event_id?: string;
};

export type RagTokenEvent = {
  type: "token";
  content: string;
};

export type RagDoneEvent = {
  type: "done";
  session_id: string;
  sources: RagSource[];
};

export type RagErrorEvent = {
  type: "error";
  message: string;
};

export type RagStreamEvent = RagTokenEvent | RagDoneEvent | RagErrorEvent;

function parseEventBlock(block: string): RagStreamEvent | null {
  const dataLines = block
    .split(/\r?\n/)
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).trim());

  if (!dataLines.length) {
    return null;
  }

  return JSON.parse(dataLines.join("\n")) as RagStreamEvent;
}

async function readApiBody(response: Response): Promise<string> {
  const text = await response.text();
  return text || response.statusText;
}

export async function streamRagChat(
  payload: RagChatPayload,
  options: {
    signal?: AbortSignal;
    onEvent: (event: RagStreamEvent) => void;
  }
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/rag/chat`, {
    method: "POST",
    cache: "no-store",
    headers: await authHeaders(),
    body: JSON.stringify(payload),
    signal: options.signal,
  });

  if (!response.ok) {
    const body = await readApiBody(response);
    throw new ApiError(`RAG chat failed with status ${response.status}`, response.status, body);
  }

  if (!response.body) {
    throw new Error("Streaming response body is not available.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });

    let boundaryIndex = buffer.indexOf("\n\n");
    while (boundaryIndex !== -1) {
      const block = buffer.slice(0, boundaryIndex).trim();
      buffer = buffer.slice(boundaryIndex + 2);
      if (block) {
        const event = parseEventBlock(block);
        if (event) {
          options.onEvent(event);
        }
      }
      boundaryIndex = buffer.indexOf("\n\n");
    }

    if (done) {
      const trailing = buffer.trim();
      if (trailing) {
        const event = parseEventBlock(trailing);
        if (event) {
          options.onEvent(event);
        }
      }
      break;
    }
  }
}

export function getRagHistory(sessionId: string): Promise<RagHistoryResponse> {
  return apiGet<RagHistoryResponse>(`/api/rag/history/${encodeURIComponent(sessionId)}`);
}

export function deleteRagHistory(sessionId: string): Promise<{ status: string; session_id: string }> {
  return apiDelete<{ status: string; session_id: string }>(`/api/rag/history/${encodeURIComponent(sessionId)}`);
}

export function getRagIndexStatus(): Promise<RagIndexStatusResponse> {
  return apiGet<RagIndexStatusResponse>("/api/rag/index/status");
}

export function rebuildRagIndex(): Promise<RagIndexRefreshResponse> {
  return apiPost<RagIndexRefreshResponse>("/api/rag/index/rebuild", {});
}

export function rebuildRagEventIndex(eventId: string): Promise<RagIndexRefreshResponse> {
  return apiPost<RagIndexRefreshResponse>(`/api/rag/index/event/${encodeURIComponent(eventId)}`, {});
}
