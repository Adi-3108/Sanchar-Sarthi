package com.namangulati.sancharsarthi.feature.explorer

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.network.AnalyticsSummaryResponse
import com.namangulati.sancharsarthi.core.network.EventDetailResponse
import com.namangulati.sancharsarthi.core.network.HotspotResponseItem
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ExplorerUiState(
    val summary: AnalyticsSummaryResponse? = null,
    val isSummaryLoading: Boolean = false,
    
    val hotspots: List<HotspotResponseItem> = emptyList(),
    val isHotspotsLoading: Boolean = false,
    val selectedClusterType: String = "",
    
    val eventIdInput: String = "",
    val eventDetail: EventDetailResponse? = null,
    val isEventLoading: Boolean = false,
    val eventLoadError: String? = null
)

class ExplorerViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(ExplorerUiState())
    val uiState: StateFlow<ExplorerUiState> = _uiState.asStateFlow()

    private val api = RetrofitClient.analyticsApi

    init {
        fetchSummary()
        fetchHotspots()
    }

    private fun fetchSummary() {
        viewModelScope.launch {
            _uiState.update { it.copy(isSummaryLoading = true) }
            try {
                val summary = api.getSummary()
                _uiState.update { it.copy(summary = summary, isSummaryLoading = false) }
            } catch (e: Exception) {
                Log.e("ExplorerViewModel", "Error fetching summary", e)
                _uiState.update { it.copy(isSummaryLoading = false) }
            }
        }
    }

    private fun fetchHotspots() {
        viewModelScope.launch {
            _uiState.update { it.copy(isHotspotsLoading = true) }
            try {
                val type = _uiState.value.selectedClusterType.takeIf { it.isNotEmpty() }
                val response = api.getHotspots(type)
                _uiState.update { it.copy(hotspots = response.hotspots, isHotspotsLoading = false) }
            } catch (e: Exception) {
                Log.e("ExplorerViewModel", "Error fetching hotspots", e)
                _uiState.update { it.copy(isHotspotsLoading = false) }
            }
        }
    }

    fun setClusterType(type: String) {
        _uiState.update { it.copy(selectedClusterType = type) }
        fetchHotspots()
    }

    fun updateEventIdInput(id: String) {
        _uiState.update { it.copy(eventIdInput = id) }
    }

    fun fetchEventDossier() {
        val eventId = _uiState.value.eventIdInput.trim()
        if (eventId.isEmpty()) return

        viewModelScope.launch {
            _uiState.update { it.copy(isEventLoading = true, eventLoadError = null, eventDetail = null) }
            try {
                val detail = api.getEventDetail(eventId)
                _uiState.update { it.copy(eventDetail = detail, isEventLoading = false) }
            } catch (e: Exception) {
                Log.e("ExplorerViewModel", "Error fetching event detail", e)
                _uiState.update { it.copy(isEventLoading = false, eventLoadError = "Failed to load event dossier: ${e.message}") }
            }
        }
    }
}
