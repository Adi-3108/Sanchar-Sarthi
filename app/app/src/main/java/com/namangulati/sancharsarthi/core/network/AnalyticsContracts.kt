package com.namangulati.sancharsarthi.core.network

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonObject

@Serializable
data class ModelRunListResponse(
    val model_runs: List<ModelRunResponse>
)

@Serializable
data class ModelRunResponse(
    val id: String,
    val model_name: String,
    val model_version: String,
    val training_rows: Int,
    val test_rows: Int,
    val artifact_available: Boolean,
    val metrics_json: MetricsJson,
    val created_at: String
)

@Serializable
data class MetricsJson(
    val status: String? = null,
    // priority model
    val f1: Double? = null,
    val recall_high: Double? = null,
    val positive_rows: Int? = null,
    val positive_rate: Double? = null,
    // road closure
    val pr_auc: Double? = null,
    val recall_true: Double? = null,
    // resolution time
    val mae_minutes: Double? = null,
    val r2_score: Double? = null,
    val qualifying_rows: Int? = null,
    val data_filter: String? = null
)

@Serializable
data class HealthResponse(
    val status: String,
    val database: String,
    val models: ModelsHealth,
    val auth: AuthHealth
)

@Serializable
data class ModelsHealth(
    val priority: String,
    val road_closure: String,
    val resolution_time: String
)

@Serializable
data class AuthHealth(
    val firebase: String
)

@Serializable
data class HourlyRiskPoint(
    val timestamp: String,
    val hour: Int,
    val day_of_week: Int,
    val risk_score: Double,
    val event_count: Int
)

@Serializable
data class CorridorRiskTimelineResponse(
    val corridor: String,
    val days_analyzed: Int,
    val hourly_risk_scores: List<HourlyRiskPoint>,
    val peak_risk_hours: List<Int>,
    val average_risk_score: Double
)

@Serializable
data class HotspotClusterProfile(
    val hotspot_category: String? = null,
    val member_event_ids: List<String> = emptyList(),
    val historical_resolution_avg_mins: Double? = null
)

@Serializable
data class HotspotResponseItem(
    val location_cluster_id: String,
    val centroid_latitude: Double,
    val centroid_longitude: Double,
    val cluster_risk_score: Double,
    val cluster_event_count: Int,
    val cluster_top_event_cause: String? = null,
    val cluster_profile: HotspotClusterProfile
)

@Serializable
data class HotspotsMetadata(
    val total_active_clusters: Int? = null,
    val computation_timestamp: String? = null
)

@Serializable
data class HotspotsResponse(
    val hotspots: List<HotspotResponseItem>,
    val metadata: HotspotsMetadata? = null
)

@Serializable
data class MultiEventAnalysisRequest(
    val event_ids: List<String>,
    val available_officers: Int
)

@Serializable
data class OfficerAllocation(
    val event_id: String,
    val recommended_officers: Int,
    val rationale: String
)

@Serializable
data class MultiEventAnalysisResponse(
    val job_id: String,
    val events_analyzed: List<String>,
    val status: String,
    val officer_allocation: List<OfficerAllocation>,
    val map_overlay: JsonObject? = null
)

@Serializable
data class AnalyticsSummaryResponse(
    val total_events: Int,
    val planned_events: Int,
    val unplanned_events: Int,
    val hotspot_count: Int
)

@Serializable
data class EventRecordResponse(
    val id: String? = null,
    val event_type: String? = null,
    val event_cause_clean: String? = null,
    val priority: String? = null,
    val status: String? = null,
    val corridor: String? = null,
    val police_station: String? = null,
    val zone: String? = null,
    val junction: String? = null,
    val requires_road_closure: Boolean = false,
    val start_datetime: String? = null,
    val end_datetime: String? = null,
    val description_language: String? = null,
    val description_normalization_method: String? = null,
    val veh_type: String? = null
)

@Serializable
data class EventFeatureResponse(
    val event_hour: Int? = null,
    val event_day: Int? = null,
    val event_month: Int? = null,
    val event_weekday: Int? = null,
    val is_weekend: Boolean = false,
    val is_peak_hour: Boolean = false,
    val is_night_event: Boolean = false,
    val event_duration_minutes: Double? = null,
    val closure_duration_minutes: Double? = null,
    val resolution_duration_minutes: Double? = null,
    val duration_source: String? = null,
    val location_cluster_id: String? = null,
    val historical_corridor_risk: Double? = null,
    val historical_police_station_risk: Double? = null,
    val historical_cluster_risk: Double? = null,
    val historical_cause_closure_rate: Double? = null,
    val historical_corridor_closure_rate: Double? = null,
    val historical_police_station_closure_rate: Double? = null,
    val historical_cluster_closure_rate: Double? = null
)

@Serializable
data class EventDnaResponse(
    val event_id: String? = null,
    val dna_summary: String? = null,
    val time_context: String? = null,
    val location_context: String? = null,
    val cause_context: String? = null,
    val weather_context: String? = null,
    val multi_event_context: String? = null,
    val historical_pattern: String? = null,
    val risk_indicators_json: JsonObject? = null,
    val similar_event_ids_json: List<String>? = null
)

@Serializable
data class EventPredictionResponse(
    val event_id: String? = null,
    val model_run_id: String? = null,
    val predicted_priority: String? = null,
    val priority_confidence: Double? = null,
    val road_closure_probability: Double? = null,
    val predicted_road_closure: Boolean? = null,
    val estimated_clearance_minutes: Double? = null,
    val clearance_prediction_method: String? = null,
    val clearance_confidence: Double? = null,
    val clearance_confidence_note: String? = null,
    val historical_clearance_range_min: Double? = null,
    val historical_clearance_range_max: Double? = null,
    val estimated_impact_score: Double? = null,
    val impact_category: String? = null,
    val impact_radius_km: Double? = null,
    val vehicle_impact_factor: Double? = null,
    val vehicle_impact_note: String? = null,
    val baseline_risk_score: Double? = null,
    val additional_event_delta: Double? = null,
    val weather_adjustment_json: JsonObject? = null,
    val multi_event_conflict_json: JsonObject? = null,
    val prediction_explanation_json: JsonObject? = null,
    val model_version: String? = null
)

@Serializable
data class RecommendationRiskSummaryResponse(
    val impact_score: Double? = null,
    val impact_category: String? = null,
    val road_closure_probability: Double? = null,
    val predicted_priority: String? = null,
    val estimated_clearance_minutes: Double? = null,
    val estimated_radius_km: Double? = null,
    val baseline_risk_score: Double? = null,
    val additional_event_delta: Double? = null,
    val honesty_note: String? = null
)

@Serializable
data class RecommendationManpowerResponse(
    val recommended_total_officers: Int? = null,
    val deployment_style: String? = null,
    val reserve_officers: Int? = null,
    val sector_count: Int? = null,
    val available_officers: Int? = null,
    val officer_gap: Int? = null,
    val feasibility_status: String? = null,
    val primary_positions: List<String>? = null,
    val reason_codes: List<String>? = null,
    val note: String? = null
)

@Serializable
data class RecommendationPlanResponse(
    val event_id: String? = null,
    val risk_summary: RecommendationRiskSummaryResponse? = null,
    val manpower: RecommendationManpowerResponse? = null,
    val recommended_action_summary: String? = null
)

@Serializable
data class SimilarEventResponse(
    val event_id: String? = null,
    val similarity: Double? = null,
    val matched_signals: List<String> = emptyList(),
    val event_cause_clean: String? = null,
    val corridor: String? = null,
    val police_station: String? = null,
    val priority: String? = null,
    val event_type: String? = null,
    val requires_road_closure: Boolean? = null,
    val hotspot_cluster_id: String? = null,
    val hotspot_risk_score: Double? = null,
    val historical_corridor_closure_rate: Double? = null,
    val historical_cluster_closure_rate: Double? = null
)

@Serializable
data class EventDetailResponse(
    val event: EventRecordResponse,
    val features: EventFeatureResponse? = null,
    val event_dna: EventDnaResponse? = null,
    val prediction: EventPredictionResponse? = null,
    val recommendation: RecommendationPlanResponse? = null,
    val similar_events: List<SimilarEventResponse>? = emptyList(),
    val citizen_reports: List<JsonObject>? = emptyList(),
    val live_updates: List<JsonObject>? = emptyList()
)
@Serializable
data class SimulationRequest(
    val event_type: String,
    val event_cause: String,
    val latitude: Double,
    val longitude: Double,
    val corridor: String,
    val police_station: String,
    val zone: String,
    val junction: String,
    val start_datetime: String,
    val expected_duration_minutes: Int,
    val expected_crowd_size: Int,
    val weather_condition: String,
    val rain_mm: Double,
    val visibility_m: Double,
    val use_live_weather: Boolean,
    val available_officers: Int,
    val description: String,
    val veh_type: String
)

@Serializable
data class SimulationSimilarEventSummary(
    val match_count: Int? = null,
    val top_match_event_id: String? = null,
    val average_similarity: Double? = null,
    val highest_similarity: Double? = null,
    val top_matched_signals: List<String>? = emptyList()
)

@Serializable
data class SimulationCounterfactual(
    val baseline_risk_score: Double? = null,
    val event_impact_score: Double? = null,
    val additional_event_delta: Double? = null,
    val honesty_note: String? = null
)

@Serializable
data class SimulationWeatherAdjustment(
    val weather_condition: String? = null,
    val weather_factor: Double? = null,
    val rain_mm: Double? = null,
    val visibility_m: Double? = null,
    val low_visibility: Boolean? = null,
    val waterlogging_risk: String? = null,
    val reason_codes: List<String>? = emptyList(),
    val source: String? = null,
    val provider: String? = null,
    val provider_status: String? = null,
    val note: String? = null
)

@Serializable
data class SimulationBarricades(
    val barricade_level: String? = null,
    val estimated_units: Int? = null,
    val coverage_radius_km: Double? = null,
    val placement_priority: List<String>? = emptyList(),
    val reason_codes: List<String>? = emptyList(),
    val note: String? = null,
    val field_note: String? = null
)

@Serializable
data class SimulationDiversions(
    val strategy: String? = null,
    val corridor_to_protect: String? = null,
    val diversion_scope: String? = null,
    val upstream_focus_points: List<String>? = emptyList(),
    val heavy_vehicle_advisory: String? = null,
    val reason_codes: List<String>? = emptyList(),
    val note: String? = null,
    val field_note: String? = null
)

@Serializable
data class SimulationEmergencyCorridor(
    val priority: String? = null,
    val lane_policy: String? = null,
    val protected_corridor: String? = null,
    val activation_trigger: String? = null,
    val authentication_note: String? = null,
    val reason_codes: List<String>? = emptyList()
)

@Serializable
data class SimulationLogisticsImpact(
    val impact_level: String? = null,
    val delivery_risk_window_minutes: Int? = null,
    val affected_radius_km: Double? = null,
    val dispatch_recommendation: String? = null,
    val warehouse_note: String? = null,
    val reason_codes: List<String>? = emptyList()
)

@Serializable
data class SimulationConfidenceLedger(
    val input: String? = null,
    val confidence: Double? = null,
    val note: String? = null,
    val source: String? = null
)

@Serializable
data class SimulationRecommendations(
    val event_id: String? = null,
    val risk_summary: RecommendationRiskSummaryResponse? = null,
    val weather_risk: SimulationWeatherAdjustment? = null,
    val manpower: RecommendationManpowerResponse? = null,
    val barricades: SimulationBarricades? = null,
    val diversions: SimulationDiversions? = null,
    val emergency_corridor: SimulationEmergencyCorridor? = null,
    val flipkart_logistics_impact: SimulationLogisticsImpact? = null,
    val action_confidence_ledger: List<SimulationConfidenceLedger>? = emptyList(),
    val recommended_action_summary: String? = null
)

@Serializable
data class SimulationResponse(
    val event_dna: EventDnaResponse? = null,
    val similar_event_summary: SimulationSimilarEventSummary? = null,
    val predicted_priority: String? = null,
    val priority_confidence: Double? = null,
    val road_closure_probability: Double? = null,
    val predicted_road_closure: Boolean? = null,
    val estimated_clearance_minutes: Double? = null,
    val clearance_prediction_method: String? = null,
    val clearance_confidence: Double? = null,
    val clearance_confidence_note: String? = null,
    val historical_clearance_range_min: Double? = null,
    val historical_clearance_range_max: Double? = null,
    val estimated_impact_score: Double? = null,
    val impact_category: String? = null,
    val impact_radius_km: Double? = null,
    val vehicle_impact_factor: Double? = null,
    val vehicle_impact_note: String? = null,
    val counterfactual: SimulationCounterfactual? = null,
    val weather_adjustment: SimulationWeatherAdjustment? = null,
    val recommendations: SimulationRecommendations? = null,
    val map_overlays: JsonObject? = null,
    val prediction_explanation_json: JsonObject? = null
)

@Serializable
data class PostEventLearningResponse(
    val event_id: String? = null,
    val predicted_impact_score: Double? = null,
    val simulated_actual_impact_score: Double? = null,
    val impact_deviation: Double? = null,
    val final_status: String? = null,
    val event_summary: String? = null,
    val prediction_summary: String? = null,
    val recommendation_summary: String? = null,
    val citizen_report_summary: String? = null,
    val live_escalation_summary: String? = null,
    val lessons_learned: String? = null,
    val future_recommendations: String? = null,
    val report_json: kotlinx.serialization.json.JsonObject? = null,
    val created_at: String? = null
)
