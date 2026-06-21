package com.namangulati.sancharsarthi.feature.admin

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.network.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class AdminUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val overview: FoundationAdminOverviewResponse? = null,
    val officerForm: CreateOfficerRequest = CreateOfficerRequest(""),
    val controlRoomForm: CreateControlRoomRequest = CreateControlRoomRequest(""),
    val actionLoading: Boolean = false,
    val successMessage: String? = null
)

class AdminViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(AdminUiState())
    val uiState: StateFlow<AdminUiState> = _uiState

    init {
        loadOverview()
    }

    fun loadOverview() {
        viewModelScope.launch {
            _uiState.update { it.copy(loading = true, error = null) }
            try {
                val response = RetrofitClient.adminApi.getOverview()
                _uiState.update { it.copy(loading = false, actionLoading = false, overview = response) }
            } catch (e: Exception) {
                _uiState.update { it.copy(loading = false, actionLoading = false, error = e.localizedMessage ?: "Failed to load overview") }
            }
        }
    }

    fun updateOfficerForm(field: String, value: Any) {
        _uiState.update { state ->
            val current = state.officerForm
            val updated = when (field) {
                "email" -> current.copy(email = value as String)
                "password" -> current.copy(password = value as String)
                "badge_number" -> current.copy(badge_number = value as String)
                "display_name" -> current.copy(display_name = value as String)
                "rank" -> current.copy(rank = value as String)
                "police_station" -> current.copy(police_station = value as String)
                "assigned_corridors" -> current.copy(assigned_corridors = (value as String).split(",").map { it.trim() }.filter { it.isNotEmpty() })
                "assigned_zones" -> current.copy(assigned_zones = (value as String).split(",").map { it.trim() }.filter { it.isNotEmpty() })
                else -> current
            }
            state.copy(officerForm = updated)
        }
    }

    fun updateControlRoomForm(field: String, value: String) {
        _uiState.update { state ->
            val current = state.controlRoomForm
            val updated = when (field) {
                "email" -> current.copy(email = value)
                "password" -> current.copy(password = value)
                "display_name" -> current.copy(display_name = value)
                else -> current
            }
            state.copy(controlRoomForm = updated)
        }
    }

    fun clearSuccessMessage() {
        _uiState.update { it.copy(successMessage = null) }
    }

    fun createOfficer() {
        viewModelScope.launch {
            _uiState.update { it.copy(actionLoading = true, error = null, successMessage = null) }
            try {
                val response = RetrofitClient.adminApi.createOfficer(_uiState.value.officerForm)
                _uiState.update { it.copy(
                    actionLoading = false, 
                    successMessage = "Officer created successfully (ID: ${response.officer_id})",
                    officerForm = CreateOfficerRequest("")
                ) }
            } catch (e: Exception) {
                _uiState.update { it.copy(actionLoading = false, error = e.localizedMessage ?: "Failed to create officer") }
            }
        }
    }

    fun createControlRoomUser() {
        viewModelScope.launch {
            _uiState.update { it.copy(actionLoading = true, error = null, successMessage = null) }
            try {
                val response = RetrofitClient.adminApi.createControlRoomUser(_uiState.value.controlRoomForm)
                _uiState.update { it.copy(
                    actionLoading = false, 
                    successMessage = "Control room user created successfully",
                    controlRoomForm = CreateControlRoomRequest("")
                ) }
            } catch (e: Exception) {
                _uiState.update { it.copy(actionLoading = false, error = e.localizedMessage ?: "Failed to create control room user") }
            }
        }
    }

    fun toggleStation(stationId: String, currentActive: Boolean) {
        viewModelScope.launch {
            _uiState.update { it.copy(actionLoading = true, error = null) }
            try {
                RetrofitClient.adminApi.updateStation(stationId, FoundationStationAdminUpdateRequest(active = !currentActive))
                loadOverview()
            } catch (e: Exception) {
                _uiState.update { it.copy(actionLoading = false, error = e.localizedMessage ?: "Failed to update station") }
            }
        }
    }

    fun toggleUser(userId: String, currentActive: Boolean) {
        viewModelScope.launch {
            _uiState.update { it.copy(actionLoading = true, error = null) }
            try {
                RetrofitClient.adminApi.updateUser(userId, FoundationUserAdminUpdateRequest(is_active = !currentActive))
                loadOverview()
            } catch (e: Exception) {
                _uiState.update { it.copy(actionLoading = false, error = e.localizedMessage ?: "Failed to update user") }
            }
        }
    }

    fun deleteVote(voteId: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(actionLoading = true, error = null) }
            try {
                RetrofitClient.adminApi.deleteVote(voteId)
                loadOverview()
            } catch (e: Exception) {
                _uiState.update { it.copy(actionLoading = false, error = e.localizedMessage ?: "Failed to delete vote") }
            }
        }
    }

    fun deleteIncident(incidentId: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(actionLoading = true, error = null) }
            try {
                RetrofitClient.adminApi.deleteIncident(incidentId)
                loadOverview()
            } catch (e: Exception) {
                _uiState.update { it.copy(actionLoading = false, error = e.localizedMessage ?: "Failed to delete incident") }
            }
        }
    }

    fun escalateIncident(incidentId: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(actionLoading = true, error = null) }
            try {
                RetrofitClient.adminApi.escalateIncident(incidentId)
                loadOverview()
            } catch (e: Exception) {
                _uiState.update { it.copy(actionLoading = false, error = e.localizedMessage ?: "Failed to escalate incident") }
            }
        }
    }

    fun transitionIncidentStatus(incidentId: String, newStatus: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(actionLoading = true, error = null) }
            try {
                RetrofitClient.adminApi.updateIncident(incidentId, FoundationIncidentAdminUpdateRequest(status = newStatus))
                loadOverview()
            } catch (e: Exception) {
                _uiState.update { it.copy(actionLoading = false, error = e.localizedMessage ?: "Failed to update incident status") }
            }
        }
    }
}
