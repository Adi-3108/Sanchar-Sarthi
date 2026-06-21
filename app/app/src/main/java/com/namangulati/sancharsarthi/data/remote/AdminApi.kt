package com.namangulati.sancharsarthi.data.remote

import com.namangulati.sancharsarthi.core.network.*
import com.namangulati.sancharsarthi.core.report.IncidentResponse
import com.namangulati.sancharsarthi.core.report.StationResponse
import retrofit2.http.*

interface AdminApi {
    @GET("foundation/admin/overview")
    suspend fun getOverview(): FoundationAdminOverviewResponse

    @POST("admin/officers")
    suspend fun createOfficer(@Body request: CreateOfficerRequest): CreateOfficerResponse

    @POST("admin/control-room-users")
    suspend fun createControlRoomUser(@Body request: CreateControlRoomRequest): CreateControlRoomResponse

    @PATCH("foundation/admin/incidents/{incidentId}")
    suspend fun updateIncident(
        @Path("incidentId") incidentId: String,
        @Body request: FoundationIncidentAdminUpdateRequest
    ): IncidentResponse

    @DELETE("foundation/admin/incidents/{incidentId}")
    suspend fun deleteIncident(@Path("incidentId") incidentId: String): DeleteIncidentResponse

    @POST("foundation/admin/incidents/{incidentId}/escalate")
    suspend fun escalateIncident(@Path("incidentId") incidentId: String): EscalateIncidentResponse

    @PATCH("foundation/admin/stations/{stationId}")
    suspend fun updateStation(
        @Path("stationId") stationId: String,
        @Body request: FoundationStationAdminUpdateRequest
    ): StationResponse

    @PATCH("foundation/admin/users/{userId}")
    suspend fun updateUser(
        @Path("userId") userId: String,
        @Body request: FoundationUserAdminUpdateRequest
    ): FoundationAdminUser

    @DELETE("foundation/admin/votes/{voteId}")
    suspend fun deleteVote(@Path("voteId") voteId: String): DeleteVoteResponse
}
