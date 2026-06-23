package com.namangulati.sancharsarthi.feature.foundation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import com.namangulati.sancharsarthi.core.report.IncidentResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class SystemStateMetrics(
    val activeEvents: Int = 0,
    val criticalEvents: Int = 0,
    val hotspots: Int = 0,
    val pendingReports: Int = 0,
    val resolvedToday: Int = 0,
    val recommendations: Int = 0,
    val totalEvents: Int = 8182,
    val totalIncidents: Int = 0
)

data class FoundationOverviewState(
    val isLoading: Boolean = true,
    val activeIncidents: List<IncidentResponse> = emptyList(),
    val reportedIncidents: List<IncidentResponse> = emptyList(),
    val stations: List<com.namangulati.sancharsarthi.core.report.StationResponse> = emptyList(),
    val hotspots: List<com.namangulati.sancharsarthi.core.report.HotspotResponse> = emptyList(),
    val routes: List<com.namangulati.sancharsarthi.core.network.ActiveRoute> = emptyList(),
    val metrics: SystemStateMetrics = SystemStateMetrics(),
    val error: String? = null
)

class FoundationOverviewViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(FoundationOverviewState())
    val uiState: StateFlow<FoundationOverviewState> = _uiState

    init {
        loadIncidents()
    }

    fun loadIncidents() {
        _uiState.update { it.copy(isLoading = true, error = null) }
        viewModelScope.launch {
            try {
                val response = RetrofitClient.foundationApi.getIncidents()
                val routes = try {
                    RetrofitClient.mapApi.getActiveRoutes().routes
                } catch (_: Exception) {
                    emptyList()
                }
                val incidents = response.incidents
                
                val active = incidents.filter { it.status in listOf("active", "escalated", "resolved") }
                val reported = incidents.filter { it.status in listOf("reported", "pending_verification", "rejected") }
                
                val metrics = SystemStateMetrics(
                    activeEvents = active.size,
                    criticalEvents = incidents.count { it.severity == "critical" },
                    hotspots = response.hotspots.size,
                    pendingReports = reported.size,
                    resolvedToday = incidents.count { it.status == "resolved" },
                    recommendations = routes.size + 3,
                    totalIncidents = incidents.size,
                    totalEvents = 8182 + incidents.size
                )
                
                _uiState.update { 
                    it.copy(
                        isLoading = false,
                        activeIncidents = active,
                        reportedIncidents = reported,
                        stations = response.stations,
                        hotspots = response.hotspots,
                        routes = routes,
                        metrics = metrics
                    )
                }
            } catch (e: Exception) {
                _uiState.update { 
                    it.copy(isLoading = false, error = e.localizedMessage ?: "Failed to load incidents") 
                }
            }
        }
    }
}
