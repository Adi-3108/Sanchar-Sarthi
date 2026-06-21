package com.namangulati.sancharsarthi.core.report

import kotlinx.serialization.Serializable

@Serializable
data class FoundationBrowseResponse(
    val incidents: List<IncidentResponse>,
    val stations: List<StationResponse> = emptyList(),
    val hotspots: List<HotspotResponse> = emptyList(),
    val statuses: List<String> = emptyList()
)

@Serializable
data class IncidentResponse(
    val id: String,
    val incident_type: String,
    val title: String,
    val description: String? = null,
    val status: String,
    val severity: String,
    val location_name: String,
    val true_vote_count: Int,
    val false_vote_count: Int,
    val confidence_score: Double,
    val created_at: String,
    val latitude: Double = 0.0,
    val longitude: Double = 0.0,
    val assigned_station_name: String? = null,
    val police_force_required: Int? = null,
    val barricades_required: Int? = null,
    val route_impact_summary: String? = null
)

@Serializable
data class StationResponse(
    val id: String,
    val station_code: String,
    val name: String,
    val locality: String,
    val latitude: Double,
    val longitude: Double,
    val contact_number: String? = null,
    val active: Boolean
)

@Serializable
data class HotspotResponse(
    val hotspot_id: String,
    val label: String,
    val incident_count: Int,
    val severity: String,
    val latitude: Double,
    val longitude: Double,
    val active_incident_ids: List<String> = emptyList()
)
