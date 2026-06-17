export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  ""
);

export type HealthResponse = {
  status: "ok";
  service: string;
  environment: string;
  checked_at: string;
  database: string;
  models: {
    priority: string;
    road_closure: string;
    resolution_time: string;
  };
  auth: {
    firebase: "configured" | "not_configured";
  };
};

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly body: string
  ) {
    super(message);
  }
}

async function readResponseBody(response: Response): Promise<string> {
  const text = await response.text();
  return text || response.statusText;
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });

  if (!response.ok) {
    const body = await readResponseBody(response);
    throw new ApiError(`API request failed with status ${response.status}`, response.status, body);
  }

  return (await response.json()) as T;
}
