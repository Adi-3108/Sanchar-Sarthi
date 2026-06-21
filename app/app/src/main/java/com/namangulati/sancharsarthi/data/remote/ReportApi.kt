package com.namangulati.sancharsarthi.data.remote

import com.namangulati.sancharsarthi.core.report.CitizenReportCreateRequest
import com.namangulati.sancharsarthi.core.report.FoundationIncidentCreateRequest
import kotlinx.serialization.json.JsonObject
import retrofit2.http.Body
import retrofit2.http.POST

interface ReportApi {
    @POST("foundation/incidents/report")
    suspend fun createIncidentReport(@Body payload: FoundationIncidentCreateRequest): JsonObject

    @POST("reports/congestion")
    suspend fun createCongestionReport(@Body payload: CitizenReportCreateRequest): JsonObject
}
