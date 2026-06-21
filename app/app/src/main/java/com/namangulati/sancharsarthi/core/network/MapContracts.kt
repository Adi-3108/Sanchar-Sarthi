package com.namangulati.sancharsarthi.core.network

import kotlinx.serialization.Serializable

@Serializable
data class MapActiveRoutesResponse(
    val routes: List<ActiveRoute>
)

@Serializable
data class ActiveRoute(
    val incidentId: String,
    val polyline: List<List<Double>>
)

@Serializable
data class MapConfigResponse(
    val activeProvider: String,
    val fallbackProvider: String,
    val fallbackReason: String? = null,
    val mapKeyAvailable: Boolean
)

@Serializable
data class MapGeocodeRequest(
    val query: String,
    val purpose: String
)

@Serializable
data class MapGeocodeCandidate(
    val label: String,
    val coordinate: List<Double>,
    val confidence: String
)

@Serializable
data class MapGeocodeResponse(
    val query: String,
    val provider: String,
    val candidates: List<MapGeocodeCandidate>,
    val honestyNote: String? = null
)

@Serializable
data class MapRouteRequest(
    val origin: List<Double>,
    val destination: List<Double>,
    val mode: String,
    val purpose: String
)

@Serializable
data class MapRouteResponse(
    val provider: String,
    val distanceMeters: Int,
    val durationSeconds: Int,
    val polyline: List<List<Double>>,
    val fallbackReason: String? = null
)
