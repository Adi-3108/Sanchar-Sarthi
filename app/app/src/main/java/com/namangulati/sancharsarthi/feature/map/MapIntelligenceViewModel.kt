package com.namangulati.sancharsarthi.feature.map

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.data.remote.AnalyticsApi
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
        _uiState.update { it.copy(isLoading = true) }
        viewModelScope.launch {
            try {
                val config = mapApi.getMapConfig()
                val hotspotsResponse = analyticsApi.getHotspots()
                
                val hotspots = hotspotsResponse.hotspots
                
                val defaultEvents = if (hotspots.isNotEmpty()) {
                    val uniqueEvents = mutableSetOf<String>()
                    for (h in hotspots) {
                        h.cluster_profile?.member_event_ids?.let { members ->
                            for (e in members) {
                                uniqueEvents.add(e)
                                if (uniqueEvents.size >= 2) break
                            }
                        }
                        if (uniqueEvents.size >= 2) break
                    }
                    uniqueEvents.joinToString(", ")
                } else ""
                
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        mapConfig = config,
                        hotspots = hotspots,
                        eventIdsInput = defaultEvents.ifEmpty { "FKID005760, FKID005762" }
                    )
                }
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false, errorMessage = e.message) }
            }
        }
    }

    fun updateGeocodeQuery(query: String) {
        _uiState.update { it.copy(geocodeQuery = query) }
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
