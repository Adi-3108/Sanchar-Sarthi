package com.namangulati.sancharsarthi.feature.officer

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import com.namangulati.sancharsarthi.data.remote.LiveUpdateRequestDto
import com.namangulati.sancharsarthi.data.remote.LiveUpdateResponseDto
import com.namangulati.sancharsarthi.data.remote.OfficerAssignmentsResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class OfficerWorkspaceViewModel : ViewModel() {
    private val _assignments = MutableStateFlow<OfficerAssignmentsResponse?>(null)
    val assignments: StateFlow<OfficerAssignmentsResponse?> = _assignments.asStateFlow()

    private val _isLoading = MutableStateFlow(true)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage: StateFlow<String?> = _errorMessage.asStateFlow()

    private val _submitResult = MutableStateFlow<LiveUpdateResponseDto?>(null)
    val submitResult: StateFlow<LiveUpdateResponseDto?> = _submitResult.asStateFlow()

    private val _submitError = MutableStateFlow<String?>(null)
    val submitError: StateFlow<String?> = _submitError.asStateFlow()

    private val _isSubmitting = MutableStateFlow(false)
    val isSubmitting: StateFlow<Boolean> = _isSubmitting.asStateFlow()

    init {
        fetchAssignments()
    }

    private fun fetchAssignments() {
        viewModelScope.launch {
            try {
                _isLoading.value = true
                _errorMessage.value = null
                _assignments.value = RetrofitClient.officerApi.getAssignments()
            } catch (e: Exception) {
                _errorMessage.value = e.localizedMessage
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun submitLiveUpdate(eventId: String, request: LiveUpdateRequestDto) {
        viewModelScope.launch {
            try {
                _isSubmitting.value = true
                _submitError.value = null
                _submitResult.value = null
                _submitResult.value = RetrofitClient.officerApi.submitLiveUpdate(
                    eventId = eventId,
                    request = request
                )
            } catch (e: Exception) {
                _submitError.value = e.localizedMessage ?: "Unknown error occurred"
            } finally {
                _isSubmitting.value = false
            }
        }
    }
}
