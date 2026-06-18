import { firebaseAuth } from "@/lib/firebase";

export const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  ""
);

export type ModelArtifactStatus = "not_loaded" | "dependency_missing" | "loaded";

export type HealthResponse = {
  status: "ok";
  service: string;
  environment: string;
  checked_at: string;
  database: string;
  database_detail?: string | null;
  models: {
    priority: ModelArtifactStatus;
    road_closure: ModelArtifactStatus;
    resolution_time: ModelArtifactStatus;
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

export type WeatherAdjustmentResponse = {
  weather_condition: string;
  weather_factor: number;
  rain_mm: number;
  visibility_m?: number | null;
  low_visibility: boolean;
  waterlogging_risk: string;
  reason_codes: string[];
  source: string;
  provider?: string | null;
  provider_status: string;
  note: string;
};

export type ActionConfidenceLedgerItemResponse = {
  input: string;
  confidence: number;
  note?: string | null;
  source?: string | null;
};

export type RecommendationRiskSummaryResponse = {
  impact_score: number;
  impact_category: string;
  road_closure_probability: number;
  predicted_priority?: string | null;
  estimated_clearance_minutes?: number | null;
  estimated_radius_km: number;
  baseline_risk_score?: number | null;
  additional_event_delta?: number | null;
  honesty_note: string;
};

export type RecommendationManpowerResponse = {
  recommended_total_officers: number;
  deployment_style: string;
  reserve_officers: number;
  sector_count: number;
  available_officers?: number | null;
  officer_gap: number;
  feasibility_status: string;
  primary_positions: string[];
  reason_codes: string[];
  note: string;
};

export type RecommendationBarricadeResponse = {
  barricade_level: string;
  estimated_units: number;
  coverage_radius_km: number;
  placement_priority: string[];
  reason_codes: string[];
  note: string;
  field_note?: string | null;
};

export type RecommendationDiversionResponse = {
  strategy: string;
  corridor_to_protect?: string | null;
  diversion_scope: string;
  upstream_focus_points: string[];
  heavy_vehicle_advisory: string;
  reason_codes: string[];
  note: string;
  field_note?: string | null;
};

export type RecommendationEmergencyCorridorResponse = {
  priority: string;
  lane_policy: string;
  protected_corridor?: string | null;
  activation_trigger: string;
  authentication_note: string;
  reason_codes: string[];
};

export type RecommendationLogisticsImpactResponse = {
  impact_level: string;
  delivery_risk_window_minutes: number;
  affected_radius_km: number;
  dispatch_recommendation: string;
  warehouse_note: string;
  reason_codes: string[];
};

export type RecommendationPlanResponse = {
  event_id: string;
  risk_summary: RecommendationRiskSummaryResponse;
  weather_risk: WeatherAdjustmentResponse;
  manpower: RecommendationManpowerResponse;
  barricades: RecommendationBarricadeResponse;
  diversions: RecommendationDiversionResponse;
  emergency_corridor?: RecommendationEmergencyCorridorResponse | null;
  flipkart_logistics_impact?: RecommendationLogisticsImpactResponse | null;
  action_confidence_ledger: ActionConfidenceLedgerItemResponse[];
  recommended_action_summary: string;
};

export type EventPredictionResponse = {
  event_id: string;
  model_run_id?: string | null;
  predicted_priority?: string | null;
  priority_confidence?: number | null;
  road_closure_probability?: number | null;
  predicted_road_closure?: boolean | null;
  estimated_clearance_minutes?: number | null;
  clearance_prediction_method?: string | null;
  clearance_confidence?: number | null;
  clearance_confidence_note?: string | null;
  historical_clearance_range_min?: number | null;
  historical_clearance_range_max?: number | null;
  estimated_impact_score?: number | null;
  impact_category?: string | null;
  impact_radius_km?: number | null;
  vehicle_impact_factor?: number | null;
  vehicle_impact_note?: string | null;
  baseline_risk_score?: number | null;
  additional_event_delta?: number | null;
  weather_adjustment_json?: WeatherAdjustmentResponse | null;
  multi_event_conflict_json?: Record<string, unknown> | null;
  prediction_explanation_json: Record<string, unknown>;
  model_version?: string | null;
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
  prediction?: EventPredictionResponse | null;
  recommendation?: RecommendationPlanResponse | null;
  similar_events: SimilarEventResponse[];
  citizen_reports: Array<Record<string, unknown>>;
  live_updates: LiveEventUpdateRecordResponse[];
  map_overlays: Record<string, unknown>;
};

export type SimilarEventSummaryResponse = {
  match_count: number;
  top_match_event_id?: string | null;
  average_similarity?: number | null;
  highest_similarity?: number | null;
  top_matched_signals: string[];
};

export type CounterfactualResponse = {
  baseline_risk_score?: number | null;
  event_impact_score?: number | null;
  additional_event_delta?: number | null;
  honesty_note: string;
};

export type EventSimulationRequest = {
  event_type: "planned" | "unplanned";
  event_cause: string;
  latitude: number;
  longitude: number;
  corridor?: string;
  police_station?: string;
  zone?: string;
  junction?: string;
  start_datetime: string;
  expected_duration_minutes?: number;
  expected_crowd_size?: number;
  weather_condition?: "clear" | "cloudy" | "light_rain" | "rain" | "heavy_rain";
  rain_mm?: number;
  visibility_m?: number;
  use_live_weather?: boolean;
  available_officers?: number;
  description?: string;
  veh_type?: string;
};

export type EventSimulationResponse = {
  event_dna: EventDnaResponse;
  similar_event_summary: SimilarEventSummaryResponse;
  predicted_priority?: string | null;
  priority_confidence?: number | null;
  road_closure_probability?: number | null;
  predicted_road_closure?: boolean | null;
  estimated_clearance_minutes?: number | null;
  clearance_prediction_method?: string | null;
  clearance_confidence?: number | null;
  clearance_confidence_note?: string | null;
  historical_clearance_range_min?: number | null;
  historical_clearance_range_max?: number | null;
  estimated_impact_score?: number | null;
  impact_category?: string | null;
  impact_radius_km?: number | null;
  vehicle_impact_factor?: number | null;
  vehicle_impact_note?: string | null;
  counterfactual: CounterfactualResponse;
  weather_adjustment: WeatherAdjustmentResponse;
  recommendations: RecommendationPlanResponse;
  map_overlays: Record<string, unknown>;
  prediction_explanation_json: Record<string, unknown>;
};

export type EventPlanRequest = {
  event_id: string;
  available_officers?: number;
  include_logistics_impact?: boolean;
  include_emergency_corridor?: boolean;
  weather_condition?: "clear" | "cloudy" | "light_rain" | "rain" | "heavy_rain";
  rain_mm?: number;
  visibility_m?: number;
  use_live_weather?: boolean;
};

export type CitizenReportSource = "citizen" | "field_officer" | "control_room" | "demo";

export type CitizenReportCreateRequest = {
  report_source: CitizenReportSource;
  report_type: string;
  latitude: number;
  longitude: number;
  severity?: string | null;
  description: string;
  language?: string;
  event_id?: string | null;
};

export type CitizenReportResponse = {
  status: string;
  matched_event_id?: string | null;
  source_language?: string | null;
  translation_status: string;
  translated_description?: string | null;
  location_match_confidence?: number | null;
  report_confidence: number;
  impact_score_change: number;
  new_alert_level: string;
  recommended_action: string;
};

export type LiveEventUpdateRecordResponse = {
  id: string;
  event_id: string;
  update_source: string;
  current_congestion_level: string;
  field_update?: string | null;
  road_closure_active: boolean;
  officer_shortage: boolean;
  crowd_increase: boolean;
  rain_waterlogging: boolean;
  new_nearby_incident: boolean;
  expected_impact_score: number;
  current_impact_score: number;
  impact_deviation: number;
  alert_level?: string | null;
  adaptive_action?: string | null;
  created_at?: string | null;
};

export type LiveUpdateRequest = {
  current_congestion_level: "Info" | "Watch" | "Stable" | "Warning" | "Critical";
  field_update?: string;
  road_closure_active?: boolean;
  officer_shortage?: boolean;
  crowd_increase?: boolean;
  rain_waterlogging?: boolean;
  new_nearby_incident?: boolean;
};

export type LiveUpdateResponse = LiveEventUpdateRecordResponse & {
  honesty_note: string;
};

export type ModelRunResponse = {
  id: string;
  model_name: string;
  model_version: string;
  target_variable: string;
  training_rows: number;
  test_rows: number;
  metrics_json: Record<string, unknown>;
  feature_list_json: string[];
  artifact_path?: string | null;
  artifact_available: boolean;
  artifact_status: ModelArtifactStatus;
  created_at: string;
};

export type ModelRunListResponse = {
  model_runs: ModelRunResponse[];
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

async function buildRequestHeaders(initHeaders?: HeadersInit): Promise<Headers> {
  const headers = new Headers(initHeaders);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!headers.has("Authorization") && firebaseAuth?.currentUser) {
    try {
      const token = await firebaseAuth.currentUser.getIdToken();
      headers.set("Authorization", `Bearer ${token}`);
    } catch {
      // Leave the request unauthenticated so protected endpoints return a clear backend error.
    }
  }
  return headers;
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
    headers: await buildRequestHeaders(init?.headers)
  });

  if (!response.ok) {
    const body = await readResponseBody(response);
    throw new ApiError(`API request failed with status ${response.status}`, response.status, body);
  }

  return (await response.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    method: "POST",
    cache: "no-store",
    headers: await buildRequestHeaders(init?.headers),
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const bodyText = await readResponseBody(response);
    throw new ApiError(`API request failed with status ${response.status}`, response.status, bodyText);
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

export function getModelRuns(init?: RequestInit): Promise<ModelRunListResponse> {
  return apiGet<ModelRunListResponse>("/api/analytics/model-runs", init);
}

export function simulateEvent(
  payload: EventSimulationRequest,
  init?: RequestInit
): Promise<EventSimulationResponse> {
  return apiPost<EventSimulationResponse>("/api/events/simulate", payload, init);
}

export function generateEventPlan(
  payload: EventPlanRequest,
  init?: RequestInit
): Promise<RecommendationPlanResponse> {
  return apiPost<RecommendationPlanResponse>("/api/recommendations/event-plan", payload, init);
}

export function submitCongestionReport(
  payload: CitizenReportCreateRequest,
  init?: RequestInit
): Promise<CitizenReportResponse> {
  return apiPost<CitizenReportResponse>("/api/reports/congestion", payload, init);
}

export function submitLiveUpdate(
  eventId: string,
  payload: LiveUpdateRequest,
  init?: RequestInit
): Promise<LiveUpdateResponse> {
  return apiPost<LiveUpdateResponse>(`/api/events/${encodeURIComponent(eventId)}/live-update`, payload, init);
}
