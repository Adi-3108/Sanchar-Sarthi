package com.namangulati.sancharsarthi.data.remote

import kotlinx.serialization.Serializable
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Body

@Serializable
data class OfficerAssignedEventDto(
    val id: String,
    val event_cause_clean: String? = null,
    val priority: String? = null,
    val status: String? = null,
    val corridor: String? = null,
    val police_station: String? = null,
    val zone: String? = null,
    val junction: String? = null,
    val start_datetime: String? = null
)

@Serializable
data class OfficerAssignmentsResponse(
    val officer_id: String? = null,
    val police_station: String? = null,
    val assigned_events: List<OfficerAssignedEventDto> = emptyList(),
    val assigned_corridors: List<String> = emptyList(),
    val assigned_zones: List<String> = emptyList()
)

@Serializable
data class LiveUpdateRequestDto(
    val current_congestion_level: String,
    val field_update: String? = null,
    val road_closure_active: Boolean = false,
    val officer_shortage: Boolean = false,
    val crowd_increase: Boolean = false,
    val rain_waterlogging: Boolean = false,
    val new_nearby_incident: Boolean = false
)

@Serializable
data class LiveUpdateResponseDto(
    val id: String,
    val event_id: String,
    val update_source: String,
    val current_congestion_level: String,
    val field_update: String? = null,
    val road_closure_active: Boolean,
    val officer_shortage: Boolean,
    val crowd_increase: Boolean,
    val rain_waterlogging: Boolean,
    val new_nearby_incident: Boolean,
    val expected_impact_score: Double,
    val current_impact_score: Double,
    val impact_deviation: Double,
    val alert_level: String? = null,
    val adaptive_action: String? = null,
    val honesty_note: String,
    val created_at: String? = null
)

interface OfficerApi {
    @GET("officer/assignments")
    suspend fun getAssignments(): OfficerAssignmentsResponse

    @POST("events/{eventId}/live-update")
    suspend fun submitLiveUpdate(
        @Path("eventId") eventId: String,
        @Body request: LiveUpdateRequestDto
    ): LiveUpdateResponseDto
}
