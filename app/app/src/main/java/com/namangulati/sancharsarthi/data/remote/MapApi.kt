package com.namangulati.sancharsarthi.data.remote

import com.namangulati.sancharsarthi.core.network.MapActiveRoutesResponse
import com.namangulati.sancharsarthi.core.network.MapConfigResponse
import com.namangulati.sancharsarthi.core.network.MapGeocodeRequest
import com.namangulati.sancharsarthi.core.network.MapGeocodeResponse
import com.namangulati.sancharsarthi.core.network.MapRouteRequest
import com.namangulati.sancharsarthi.core.network.MapRouteResponse
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

interface MapApi {
    @GET("/api/map/active-routes")
    suspend fun getActiveRoutes(): MapActiveRoutesResponse

    @GET("/api/map/config")
    suspend fun getMapConfig(): MapConfigResponse

    @POST("/api/map/geocode")
    suspend fun geocodeMapAddress(
        @Body request: MapGeocodeRequest
    ): MapGeocodeResponse

    @POST("/api/map/route")
    suspend fun getMapRoute(
        @Body request: MapRouteRequest
    ): MapRouteResponse
}
