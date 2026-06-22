from __future__ import annotations

from pydantic import BaseModel, Field


class WeatherAdjustmentResponse(BaseModel):
    weather_condition: str
    weather_factor: float
    rain_mm: float
    visibility_m: float | None = None
    low_visibility: bool = False
    waterlogging_risk: str
    reason_codes: list[str] = Field(default_factory=list)
    source: str
    provider: str | None = None
    provider_status: str
    note: str


class ActionConfidenceLedgerItemResponse(BaseModel):
    input: str
    confidence: float
    note: str | None = None
    source: str | None = None


class RecommendationRiskSummaryResponse(BaseModel):
    impact_score: float
    impact_category: str
    road_closure_probability: float
    predicted_priority: str | None = None
    estimated_clearance_minutes: float | None = None
    estimated_radius_km: float
    baseline_risk_score: float | None = None
    additional_event_delta: float | None = None
    honesty_note: str


class RecommendationManpowerResponse(BaseModel):
    recommended_total_officers: int
    deployment_style: str
    reserve_officers: int
    sector_count: int
    available_officers: int | None = None
    officer_gap: int
    feasibility_status: str
    primary_positions: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    note: str


class RecommendationBarricadeResponse(BaseModel):
    barricade_level: str
    estimated_units: int
    coverage_radius_km: float
    placement_priority: list[str] = Field(default_factory=list)
    reason_codes: list[str] = Field(default_factory=list)
    note: str
    field_note: str | None = None


class RecommendationDiversionResponse(BaseModel):
    strategy: str
    corridor_to_protect: str | None = None
    diversion_scope: str
    upstream_focus_points: list[str] = Field(default_factory=list)
    heavy_vehicle_advisory: str
    reason_codes: list[str] = Field(default_factory=list)
    note: str
    field_note: str | None = None


class RecommendationEmergencyCorridorResponse(BaseModel):
    priority: str
    lane_policy: str
    protected_corridor: str | None = None
    activation_trigger: str
    authentication_note: str
    reason_codes: list[str] = Field(default_factory=list)


class RecommendationLogisticsImpactResponse(BaseModel):
    impact_level: str
    delivery_risk_window_minutes: int
    affected_radius_km: float
    dispatch_recommendation: str
    warehouse_note: str
    reason_codes: list[str] = Field(default_factory=list)


class RecommendationPlanResponse(BaseModel):
    event_id: str
    risk_summary: RecommendationRiskSummaryResponse
    weather_risk: WeatherAdjustmentResponse
    manpower: RecommendationManpowerResponse
    barricades: RecommendationBarricadeResponse
    diversions: RecommendationDiversionResponse
    emergency_corridor: RecommendationEmergencyCorridorResponse | None = None
    flipkart_logistics_impact: RecommendationLogisticsImpactResponse | None = None
    action_confidence_ledger: list[ActionConfidenceLedgerItemResponse] = Field(default_factory=list)
    recommended_action_summary: str


class EventPlanRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=64)
    available_officers: int | None = Field(default=None, ge=0)
    include_logistics_impact: bool = True
    include_emergency_corridor: bool = True
    weather_condition: str | None = Field(default=None, pattern="^(clear|cloudy|light_rain|rain|heavy_rain)$")
    rain_mm: float | None = Field(default=None, ge=0, le=500)
    visibility_m: float | None = Field(default=None, ge=0, le=20000)
    use_live_weather: bool = True
