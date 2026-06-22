package com.namangulati.sancharsarthi.data.remote

import com.namangulati.sancharsarthi.core.network.HealthResponse
import com.namangulati.sancharsarthi.core.network.ModelRunListResponse
import com.namangulati.sancharsarthi.core.network.CorridorRiskTimelineResponse
import com.namangulati.sancharsarthi.core.network.HotspotsResponse
import com.namangulati.sancharsarthi.core.network.MultiEventAnalysisRequest
import com.namangulati.sancharsarthi.core.network.MultiEventAnalysisResponse
import com.namangulati.sancharsarthi.core.network.AnalyticsSummaryResponse
import com.namangulati.sancharsarthi.core.network.EventDetailResponse
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query
import retrofit2.http.Path
import com.namangulati.sancharsarthi.core.network.SimulationRequest
import com.namangulati.sancharsarthi.core.network.SimulationResponse

import com.namangulati.sancharsarthi.core.network.PostEventLearningResponse

interface AnalyticsApi {
    @GET("health")
    suspend fun getHealth(): HealthResponse

    @GET("analytics/model-runs")
    suspend fun getModelRuns(): ModelRunListResponse

    @GET("/api/analytics/corridor-risk-timeline")
    suspend fun getCorridorRiskTimeline(
        @Query("corridor") corridor: String,
        @Query("days") days: Int
    ): CorridorRiskTimelineResponse

    @GET("/api/analytics/hotspots")
    suspend fun getHotspots(
        @Query("cluster_type") clusterType: String? = null
    ): HotspotsResponse

    @GET("/api/analytics/summary")
    suspend fun getSummary(): AnalyticsSummaryResponse

    @GET("/api/events/{id}")
    suspend fun getEventDetail(@Path("id") id: String): EventDetailResponse

    @POST("/api/events/simulate")
    suspend fun runSimulation(@Body request: SimulationRequest): SimulationResponse

    @POST("/api/events/{event_id}/post-event-report")
    suspend fun generatePostEventReport(@Path("event_id") eventId: String): PostEventLearningResponse

    @POST("/api/events/multi-event-analysis")
    suspend fun analyzeMultiEvent(
        @Body request: MultiEventAnalysisRequest
    ): MultiEventAnalysisResponse
}
