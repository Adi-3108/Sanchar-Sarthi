package com.namangulati.sancharsarthi.feature.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.data.remote.AnalyticsApi
import com.namangulati.sancharsarthi.core.network.HotspotClusterProfile
import com.namangulati.sancharsarthi.core.network.HotspotResponseItem
import com.namangulati.sancharsarthi.data.remote.MapApi
import com.namangulati.sancharsarthi.core.network.MapConfigResponse
import com.namangulati.sancharsarthi.core.network.MapGeocodeCandidate
import com.namangulati.sancharsarthi.core.network.MapGeocodeRequest
import com.namangulati.sancharsarthi.core.network.MapRouteRequest
import com.namangulati.sancharsarthi.core.network.MapRouteResponse
import com.namangulati.sancharsarthi.core.network.MultiEventAnalysisRequest
import com.namangulati.sancharsarthi.core.network.MultiEventAnalysisResponse
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class MapIntelligenceUiState(
    val isLoading: Boolean = false,
    val mapConfig: MapConfigResponse? = null,
    val hotspots: List<HotspotResponseItem> = emptyList(),
    val routeData: MapRouteResponse? = null,
    val isRouting: Boolean = false,
    
    val geocodeQuery: String = "MG Road, Bengaluru",
    val geocodeCandidates: List<MapGeocodeCandidate> = emptyList(),
    val isGeocoding: Boolean = false,
    
    val eventIdsInput: String = "",
    val availableOfficersInput: String = "18",
    val multiEventAnalysis: MultiEventAnalysisResponse? = null,
    val isAnalyzing: Boolean = false,
    
    val errorMessage: String? = null
)

class MapIntelligenceViewModel(
    private val mapApi: MapApi = RetrofitClient.mapApi,
    private val analyticsApi: AnalyticsApi = RetrofitClient.analyticsApi
) : ViewModel() {

    private val _uiState = MutableStateFlow(MapIntelligenceUiState())
    val uiState: StateFlow<MapIntelligenceUiState> = _uiState.asStateFlow()

    init {
        loadInitialData()
    }

    private fun loadInitialData() {
        _uiState.update { it.copy(isLoading = true, errorMessage = null) }
        viewModelScope.launch {
            val config = try {
                mapApi.getMapConfig()
            } catch (_: Exception) {
                null
            }

            var hotspotError: String? = null
            val analyticsHotspots = try {
                analyticsApi.getHotspots().hotspots
            } catch (e: Exception) {
                hotspotError = "Analytics hotspots: ${e.message}"
                emptyList()
            }

            val hotspots = if (analyticsHotspots.isNotEmpty()) {
                analyticsHotspots
            } else {
                val fallback = loadFoundationHotspotFallback()
                if (fallback.isEmpty() && hotspotError != null) {
                    // Both sources failed — keep the error visible
                } else {
                    hotspotError = null // fallback succeeded, clear error
                }
                fallback
            }
            val defaultEvents = buildDefaultEventIds(hotspots)

            _uiState.update {
                it.copy(
                    isLoading = false,
                    mapConfig = config,
                    hotspots = hotspots,
                    eventIdsInput = defaultEvents.ifEmpty { "FKID005760, FKID005762" },
                    errorMessage = hotspotError
                )
            }
        }
    }

    private suspend fun loadFoundationHotspotFallback(): List<HotspotResponseItem> {
        return try {
            RetrofitClient.foundationApi.getIncidents().hotspots.map { hotspot ->
                HotspotResponseItem(
                    location_cluster_id = hotspot.label.ifBlank { hotspot.hotspot_id },
                    centroid_latitude = hotspot.latitude,
                    centroid_longitude = hotspot.longitude,
                    cluster_risk_score = riskScoreForSeverity(hotspot.severity),
                    cluster_event_count = hotspot.incident_count,
                    cluster_top_event_cause = hotspot.severity,
                    cluster_profile = HotspotClusterProfile(
                        hotspot_category = hotspot.severity,
                        member_event_ids = hotspot.active_incident_ids
                    )
                )
            }
        } catch (_: Exception) {
            emptyList()
        }
    }

    private fun buildDefaultEventIds(hotspots: List<HotspotResponseItem>): String {
        val uniqueEvents = mutableSetOf<String>()
        for (hotspot in hotspots) {
            hotspot.cluster_profile.member_event_ids.forEach { eventId ->
                uniqueEvents.add(eventId)
                if (uniqueEvents.size >= 2) return uniqueEvents.joinToString(", ")
            }
        }
        return uniqueEvents.joinToString(", ")
    }

    private fun riskScoreForSeverity(severity: String): Double {
        return when (severity.lowercase()) {
            "critical", "high" -> 75.0
            "medium" -> 45.0
            "low" -> 20.0
            else -> 30.0
        }
    }

    fun updateGeocodeQuery(query: String) {
        _uiState.update { it.copy(geocodeQuery = query) }
    }

    fun reload() {
        loadInitialData()
    }

    fun searchAddress() {
        if (_uiState.value.geocodeQuery.length < 3) return
        _uiState.update { it.copy(isGeocoding = true) }
        viewModelScope.launch {
            try {
                val response = mapApi.geocodeMapAddress(
                    MapGeocodeRequest(query = _uiState.value.geocodeQuery, purpose = "map_intelligence_search")
                )
                _uiState.update { it.copy(isGeocoding = false, geocodeCandidates = response.candidates) }
            } catch (e: Exception) {
                _uiState.update { it.copy(isGeocoding = false, errorMessage = e.message) }
            }
        }
    }

    fun refreshDemoRoute() {
        _uiState.update { it.copy(isRouting = true) }
        viewModelScope.launch {
            try {
                val response = mapApi.getMapRoute(
                    MapRouteRequest(
                        origin = listOf(77.5946, 12.9716),
                        destination = listOf(77.6850, 12.9308),
                        mode = "driving",
                        purpose = "diversion_plan"
                    )
                )
                _uiState.update { it.copy(isRouting = false, routeData = response) }
            } catch (e: Exception) {
                _uiState.update { it.copy(isRouting = false, errorMessage = e.message) }
            }
        }
    }

    fun updateEventIds(ids: String) {
        _uiState.update { it.copy(eventIdsInput = ids) }
    }

    fun updateOfficers(officers: String) {
        _uiState.update { it.copy(availableOfficersInput = officers) }
    }

    fun runMultiEventAnalysis() {
        val eventIds = _uiState.value.eventIdsInput.split(",").map { it.trim() }.filter { it.isNotEmpty() }
        if (eventIds.size < 2) return
        val officers = _uiState.value.availableOfficersInput.toIntOrNull() ?: 18
        
        _uiState.update { it.copy(isAnalyzing = true) }
        viewModelScope.launch {
            try {
                val response = analyticsApi.analyzeMultiEvent(
                    MultiEventAnalysisRequest(event_ids = eventIds, available_officers = officers)
                )
                _uiState.update { it.copy(isAnalyzing = false, multiEventAnalysis = response) }
            } catch (e: Exception) {
                _uiState.update { it.copy(isAnalyzing = false, errorMessage = e.message) }
            }
        }
    }
}
