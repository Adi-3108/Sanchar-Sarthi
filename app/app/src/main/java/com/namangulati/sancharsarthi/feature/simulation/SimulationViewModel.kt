package com.namangulati.sancharsarthi.feature.simulation

import android.util.Log
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import com.namangulati.sancharsarthi.core.network.SimulationRequest
import com.namangulati.sancharsarthi.core.network.SimulationResponse
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class SimulationUiState(
    val eventType: String = "planned",
    val eventCause: String = "sports_event",
    val latitude: String = "12.9716",
    val longitude: String = "77.5946",
    val corridor: String = "Central Spine",
    val policeStation: String = "Ashok Nagar",
    val junction: String = "MG Road",
    val startDatetime: String = "22-06-2026 12:30",
    val durationMinutes: String = "90",
    val crowdSize: String = "2500",
    val availableOfficers: String = "12",
    val weatherCondition: String = "clear",
    val rainMm: String = "0",
    val visibilityM: String = "5000",
    val useLiveWeather: Boolean = true,
    val description: String = "Planned crowd movement with expected parking spillover near the junction.",
    val vehType: String = "car",

    val isLoading: Boolean = false,
    val error: String? = null,
    val result: SimulationResponse? = null
)

class SimulationViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(SimulationUiState())
    val uiState: StateFlow<SimulationUiState> = _uiState.asStateFlow()

    private val api = RetrofitClient.analyticsApi

    fun updateField(field: String, value: String) {
        _uiState.update { state ->
            when (field) {
                "eventType" -> state.copy(eventType = value)
                "eventCause" -> state.copy(eventCause = value)
                "latitude" -> state.copy(latitude = value)
                "longitude" -> state.copy(longitude = value)
                "corridor" -> state.copy(corridor = value)
                "policeStation" -> state.copy(policeStation = value)
                "junction" -> state.copy(junction = value)
                "startDatetime" -> state.copy(startDatetime = value)
                "durationMinutes" -> state.copy(durationMinutes = value)
                "crowdSize" -> state.copy(crowdSize = value)
                "availableOfficers" -> state.copy(availableOfficers = value)
                "weatherCondition" -> state.copy(weatherCondition = value)
                "rainMm" -> state.copy(rainMm = value)
                "visibilityM" -> state.copy(visibilityM = value)
                "description" -> state.copy(description = value)
                "vehType" -> state.copy(vehType = value)
                else -> state
            }
        }
    }

    fun updateLiveWeather(use: Boolean) {
        _uiState.update { it.copy(useLiveWeather = use) }
    }

    fun runSimulation() {
        viewModelScope.launch {
            val state = _uiState.value
            _uiState.update { it.copy(isLoading = true, error = null, result = null) }

            try {
                val request = SimulationRequest(
                    event_type = state.eventType,
                    event_cause = state.eventCause,
                    latitude = state.latitude.toDoubleOrNull() ?: 12.9716,
                    longitude = state.longitude.toDoubleOrNull() ?: 77.5946,
                    corridor = state.corridor,
                    police_station = state.policeStation,
                    zone = "unknown zone",
                    junction = state.junction,
                    start_datetime = "2026-06-22T07:00:00Z", // Mocked format for now
                    expected_duration_minutes = state.durationMinutes.toIntOrNull() ?: 90,
                    expected_crowd_size = state.crowdSize.toIntOrNull() ?: 2500,
                    weather_condition = state.weatherCondition,
                    rain_mm = state.rainMm.toDoubleOrNull() ?: 0.0,
                    visibility_m = state.visibilityM.toDoubleOrNull() ?: 5000.0,
                    use_live_weather = state.useLiveWeather,
                    available_officers = state.availableOfficers.toIntOrNull() ?: 12,
                    description = state.description,
                    veh_type = state.vehType
                )

                val response = api.runSimulation(request)
                _uiState.update { it.copy(result = response, isLoading = false) }
            } catch (e: Exception) {
                Log.e("SimulationVM", "Error running simulation", e)
                _uiState.update { it.copy(isLoading = false, error = e.localizedMessage ?: "Simulation failed") }
            }
        }
    }
}
