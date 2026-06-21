package com.namangulati.sancharsarthi.feature.insights

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.network.HealthResponse
import com.namangulati.sancharsarthi.core.network.ModelRunResponse
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ModelInsightsUiState(
    val isLoading: Boolean = true,
    val error: String? = null,
    val health: HealthResponse? = null,
    val modelRuns: List<ModelRunResponse> = emptyList()
)

class ModelInsightsViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(ModelInsightsUiState())
    val uiState: StateFlow<ModelInsightsUiState> = _uiState.asStateFlow()

    init {
        fetchInsights()
    }

    fun fetchInsights() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            try {
                // Run fetches in parallel or sequentially. We'll do sequentially for simplicity, but both could be async
                val healthResult = RetrofitClient.analyticsApi.getHealth()
                val runsResult = try {
                    RetrofitClient.analyticsApi.getModelRuns().model_runs
                } catch (e: Exception) {
                    // It's possible model runs fail if auth is not perfectly set up or endpoint isn't available
                    // We'll treat it as empty list if it fails, or propagate the error. Let's propagate.
                    throw e
                }

                _uiState.update { 
                    it.copy(
                        isLoading = false,
                        health = healthResult,
                        modelRuns = runsResult
                    ) 
                }
            } catch (e: Exception) {
                _uiState.update { 
                    it.copy(
                        isLoading = false,
                        error = e.localizedMessage ?: "Failed to load model insights"
                    ) 
                }
            }
        }
    }
}
