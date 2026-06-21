package com.namangulati.sancharsarthi.feature.learning

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import com.namangulati.sancharsarthi.core.network.PostEventLearningResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class LearningUiState(
    val eventIdInput: String = "FKID000123",
    val isLoading: Boolean = false,
    val error: String? = null,
    val result: PostEventLearningResponse? = null
)

class LearningViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(LearningUiState())
    val uiState: StateFlow<LearningUiState> = _uiState.asStateFlow()

    private val api = RetrofitClient.analyticsApi

    fun updateEventId(id: String) {
        _uiState.update { it.copy(eventIdInput = id) }
    }

    fun generateReport() {
        val eventId = _uiState.value.eventIdInput.trim()
        if (eventId.isEmpty()) return

        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null, result = null) }
            try {
                val response = api.generatePostEventReport(eventId)
                _uiState.update { it.copy(result = response, isLoading = false) }
            } catch (e: Exception) {
                Log.e("LearningVM", "Error generating report", e)
                _uiState.update { it.copy(isLoading = false, error = e.localizedMessage ?: "Failed to generate report") }
            }
        }
    }
}
