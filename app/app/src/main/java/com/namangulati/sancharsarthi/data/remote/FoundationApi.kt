package com.namangulati.sancharsarthi.data.remote

import com.namangulati.sancharsarthi.core.report.FoundationBrowseResponse
import retrofit2.http.GET

interface FoundationApi {
    @GET("foundation/incidents")
    suspend fun getIncidents(): FoundationBrowseResponse

    @retrofit2.http.POST("foundation/incidents/{incidentId}/vote")
    suspend fun voteIncident(
        @retrofit2.http.Path("incidentId") incidentId: String,
        @retrofit2.http.Body request: Map<String, String>
    ): com.namangulati.sancharsarthi.core.report.IncidentResponse
}
