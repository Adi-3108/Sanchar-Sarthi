package com.namangulati.sancharsarthi.core.network

import com.namangulati.sancharsarthi.core.report.HotspotResponse
import com.namangulati.sancharsarthi.core.report.IncidentResponse
import com.namangulati.sancharsarthi.core.report.StationResponse
import kotlinx.serialization.Serializable

@Serializable
data class CreateOfficerRequest(
    val email: String,
    val password: String? = null,
    val badge_number: String? = null,
    val display_name: String? = null,
    val rank: String? = null,
    val police_station: String? = null,
    val assigned_corridors: List<String> = emptyList(),
    val assigned_zones: List<String> = emptyList()
)

@Serializable
data class CreateOfficerResponse(
    val status: String,
    val officer_id: String,
    val role: String,
    val active: Boolean
)

@Serializable
data class CreateControlRoomRequest(
    val email: String,
    val password: String? = null,
    val display_name: String? = null
)

@Serializable
data class CreateControlRoomResponse(
    val status: String,
    val firebase_uid: String,
    val role: String,
    val active: Boolean
)

@Serializable
data class FoundationAdminSummary(
    val incident_count: Int,
    val station_count: Int,
    val vote_count: Int,
    val prediction_count: Int,
    val user_count: Int,
    val audit_log_count: Int,
    val status_counts: Map<String, Int>
)

@Serializable
data class FoundationAdminUser(
    val id: String,
    val display_name: String? = null,
    val role: String,
    val auth_provider_uid: String,
    val is_active: Boolean,
    val created_at: String
)

@Serializable
data class FoundationVote(
    val id: String,
    val incident_id: String,
    val voter_user_id: String,
    val vote_value: String,
    val created_at: String
)

@Serializable
data class FoundationAuditLog(
    val id: String,
    val actor_role: String,
    val action: String,
    val resource_type: String,
    val resource_id: String? = null,
    val created_at: String
)

@Serializable
data class FoundationAdminOverviewResponse(
    val summary: FoundationAdminSummary,
    val incidents: List<IncidentResponse>,
    val stations: List<StationResponse>,
    val users: List<FoundationAdminUser>,
    val votes: List<FoundationVote>,
    val logs: List<FoundationAuditLog>,
    val hotspots: List<HotspotResponse>,
    val statuses: List<String>
)

@Serializable
data class FoundationIncidentAdminUpdateRequest(
    val title: String? = null,
    val description: String? = null,
    val status: String? = null,
    val severity: String? = null,
    val location_name: String? = null,
    val locality: String? = null,
    val ward: String? = null,
    val police_force_required: Int? = null,
    val barricades_required: Int? = null,
    val route_impact_summary: String? = null,
    val resolution_notes: String? = null,
    val visible_to_public: Boolean? = null,
    val station_alerted: Boolean? = null
)

@Serializable
data class FoundationStationAdminUpdateRequest(
    val name: String? = null,
    val locality: String? = null,
    val contact_number: String? = null,
    val active: Boolean? = null
)

@Serializable
data class FoundationUserAdminUpdateRequest(
    val display_name: String? = null,
    val role: String? = null,
    val is_active: Boolean? = null
)

@Serializable
data class DeleteIncidentResponse(
    val status: String,
    val incident_id: String
)

@Serializable
data class EscalateIncidentResponse(
    val status: String,
    val incident_id: String,
    val event_id: String,
    val message: String
)

@Serializable
data class DeleteVoteResponse(
    val status: String,
    val vote_id: String
)
