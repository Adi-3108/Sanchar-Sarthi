package com.namangulati.sancharsarthi.feature.citizen

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import com.namangulati.sancharsarthi.core.report.FoundationIncidentCreateRequest
import com.namangulati.sancharsarthi.core.session.ProfileStatsStore
import com.namangulati.sancharsarthi.core.report.IncidentResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class CitizenExperienceViewModel : ViewModel() {
    private val _reportedIncidents = MutableStateFlow<List<IncidentResponse>>(emptyList())
    val reportedIncidents: StateFlow<List<IncidentResponse>> = _reportedIncidents.asStateFlow()

    private val _isIncidentsLoading = MutableStateFlow(true)
    val isIncidentsLoading: StateFlow<Boolean> = _isIncidentsLoading.asStateFlow()

    private val _isSubmitting = MutableStateFlow(false)
    val isSubmitting: StateFlow<Boolean> = _isSubmitting.asStateFlow()

    private val _feedbackMsg = MutableStateFlow("")
    val feedbackMsg: StateFlow<String> = _feedbackMsg.asStateFlow()

    init {
        fetchIncidents()
    }

    fun fetchIncidents() {
        viewModelScope.launch {
            try {
                _isIncidentsLoading.value = true
                val response = RetrofitClient.foundationApi.getIncidents()
                _reportedIncidents.value = response.incidents.filter { it.status in listOf("reported", "pending_verification", "rejected") }
            } catch (e: Exception) {
                // Silently fail or show error
            } finally {
                _isIncidentsLoading.value = false
            }
        }
    }

    fun submitReport(
        request: FoundationIncidentCreateRequest,
        onSuccess: () -> Unit
    ) {
        viewModelScope.launch {
            try {
                _isSubmitting.value = true
                _feedbackMsg.value = ""
                RetrofitClient.reportApi.createIncidentReport(request)
                refreshProfileStats()
                _feedbackMsg.value = "Incident reported successfully!"
                onSuccess()
                fetchIncidents()
            } catch (e: Exception) {
                _feedbackMsg.value = "Failed to submit: ${e.message}"
            } finally {
                _isSubmitting.value = false
            }
        }
    }

    private suspend fun refreshProfileStats() {
        try {
            val stats = RetrofitClient.foundationApi.getUserStats()
            ProfileStatsStore.setStats(
                incidentsReported = stats.incidents_reported,
                incidentsVoted = stats.incidents_voted,
            )
        } catch (_: Exception) {
            // Profile counters are non-blocking; keep the current value on refresh failure.
        }
    }

    fun clearFeedback() {
        _feedbackMsg.value = ""
    }

    fun setFeedback(msg: String) {
        _feedbackMsg.value = msg
    }

    fun voteIncident(incidentId: String, voteVal: String) {
        viewModelScope.launch {
            try {
                RetrofitClient.foundationApi.voteIncident(incidentId, mapOf("vote_value" to voteVal))
                refreshProfileStats()
                fetchIncidents()
            } catch (e: Exception) {
                // Handled
            }
        }
    }
}
