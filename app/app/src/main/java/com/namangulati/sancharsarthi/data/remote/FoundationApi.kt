package com.namangulati.sancharsarthi.data.remote

import com.namangulati.sancharsarthi.core.report.FoundationBrowseResponse
import kotlinx.serialization.Serializable
import retrofit2.http.GET

@Serializable
data class UserStatsResponseDto(
    val incidents_reported: Int,
    val incidents_voted: Int,
)

interface FoundationApi {
    @GET("foundation/incidents")
    suspend fun getIncidents(): FoundationBrowseResponse

    @GET("foundation/me/stats")
    suspend fun getUserStats(): UserStatsResponseDto

    @retrofit2.http.POST("foundation/incidents/{incidentId}/vote")
    suspend fun voteIncident(
        @retrofit2.http.Path("incidentId") incidentId: String,
        @retrofit2.http.Body request: Map<String, String>
    ): com.namangulati.sancharsarthi.core.report.IncidentResponse
}
