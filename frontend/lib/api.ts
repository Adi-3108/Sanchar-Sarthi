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
  database_detail?: string | null;
  models: {
    priority: string;
    road_closure: string;
    resolution_time: string;
  };
  auth: {
    firebase: "configured" | "not_configured";
  };
};

export type AnalyticsBreakdownItem = {
  label: string;
  count: number;
  share: number;
};

export type AnalyticsSummaryResponse = {
  total_events: number;
  planned_events: number;
  unplanned_events: number;
  high_priority_events: number;
  road_closure_required: number;
  hotspot_count: number;
  top_causes: AnalyticsBreakdownItem[];
  top_corridors: AnalyticsBreakdownItem[];
  top_police_stations: AnalyticsBreakdownItem[];
};

export type HotspotClusterProfile = {
  cluster_type?: "low" | "medium" | "high" | "critical";
  radius_km?: number;
  member_event_ids?: string[];
  event_causes?: Record<string, number>;
  priority_mix?: Record<string, number>;
  top_corridors?: Array<{ label: string; count: number }>;
  top_police_stations?: Array<{ label: string; count: number }>;
  high_priority_rate?: number;
  road_closure_rate?: number;
  peak_hour_rate?: number;
  [key: string]: unknown;
};

export type HotspotResponseItem = {
  location_cluster_id: string;
  centroid_latitude: number;
  centroid_longitude: number;
  cluster_event_count: number;
  cluster_risk_score: number;
  cluster_top_event_cause?: string | null;
  cluster_high_priority_rate?: number | null;
  cluster_road_closure_rate?: number | null;
  cluster_peak_hour_rate?: number | null;
  cluster_type?: "low" | "medium" | "high" | "critical" | null;
  cluster_profile: HotspotClusterProfile;
};

export type HotspotListResponse = {
  hotspots: HotspotResponseItem[];
  geojson: Record<string, unknown>;
  filters_applied: Record<string, unknown>;
};

export type EventFeatureResponse = {
  event_hour?: number | null;
  event_day?: number | null;
  event_month?: number | null;
  event_weekday?: number | null;
  is_weekend: boolean;
  is_peak_hour: boolean;
  is_night_event: boolean;
  event_duration_minutes?: number | null;
  closure_duration_minutes?: number | null;
  resolution_duration_minutes?: number | null;
  duration_source?: string | null;
  location_cluster_id?: string | null;
  historical_corridor_risk?: number | null;
  historical_police_station_risk?: number | null;
  historical_cluster_risk?: number | null;
  historical_cause_closure_rate?: number | null;
  historical_corridor_closure_rate?: number | null;
  historical_police_station_closure_rate?: number | null;
  historical_cluster_closure_rate?: number | null;
};

export type EventDnaResponse = {
  event_id: string;
  dna_summary: string;
  time_context: string;
  location_context: string;
  cause_context: string;
  weather_context?: string | null;
  multi_event_context?: string | null;
  historical_pattern: string;
  risk_indicators_json: Record<string, unknown>;
  similar_event_ids_json: string[];
};

export type SimilarEventResponse = {
  event_id: string;
  similarity: number;
  matched_signals: string[];
  event_cause_clean?: string | null;
  corridor?: string | null;
  police_station?: string | null;
  priority?: string | null;
  event_type?: string | null;
  requires_road_closure: boolean;
  hotspot_cluster_id?: string | null;
  hotspot_risk_score?: number | null;
  historical_corridor_closure_rate?: number | null;
  historical_cluster_closure_rate?: number | null;
};

export type EventDetailResponse = {
  event: {
    id: string;
    event_type?: string | null;
    event_cause_clean?: string | null;
    priority?: string | null;
    status?: string | null;
    corridor?: string | null;
    police_station?: string | null;
    zone?: string | null;
    junction?: string | null;
    requires_road_closure: boolean;
    start_datetime: string;
    end_datetime?: string | null;
    description_language: string;
    description_normalization_method?: string | null;
    veh_type?: string | null;
  };
  features?: EventFeatureResponse | null;
  event_dna?: EventDnaResponse | null;
  prediction?: Record<string, unknown> | null;
  recommendation?: Record<string, unknown> | null;
  similar_events: SimilarEventResponse[];
  citizen_reports: Array<Record<string, unknown>>;
  live_updates: Array<Record<string, unknown>>;
  map_overlays: Record<string, unknown>;
};

export type HotspotQuery = {
  eventCause?: string;
  priority?: string;
  requiresRoadClosure?: boolean;
  clusterType?: "low" | "medium" | "high" | "critical";
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

function buildQueryString(params: Record<string, string | number | boolean | undefined>): string {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined) {
      return;
    }
    searchParams.set(key, String(value));
  });
  const query = searchParams.toString();
  return query ? `?${query}` : "";
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

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>("/api/health");
}

export function getSummary(init?: RequestInit): Promise<AnalyticsSummaryResponse> {
  return apiGet<AnalyticsSummaryResponse>("/api/analytics/summary", init);
}

export function getHotspots(query: HotspotQuery = {}, init?: RequestInit): Promise<HotspotListResponse> {
  const search = buildQueryString({
    event_cause: query.eventCause,
    priority: query.priority,
    requires_road_closure: query.requiresRoadClosure,
    cluster_type: query.clusterType
  });
  return apiGet<HotspotListResponse>(`/api/analytics/hotspots${search}`, init);
}

export function getEventDetail(eventId: string, init?: RequestInit): Promise<EventDetailResponse> {
  return apiGet<EventDetailResponse>(`/api/events/${encodeURIComponent(eventId)}`, init);
}
