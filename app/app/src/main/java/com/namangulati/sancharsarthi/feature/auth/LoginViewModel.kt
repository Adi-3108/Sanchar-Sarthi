package com.namangulati.sancharsarthi.feature.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.namangulati.sancharsarthi.core.auth.FirebaseAuthManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class LoginViewModel(
    private val firebaseAuthManager: FirebaseAuthManager = FirebaseAuthManager()
) : ViewModel() {
    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState

    fun updateEmail(email: String) {
        _uiState.update { it.copy(email = email, error = null) }
    }

    fun updatePassword(password: String) {
        _uiState.update { it.copy(password = password, error = null) }
    }

    fun toggleMode() {
        _uiState.update { it.copy(isSignUp = !it.isSignUp, error = null, isUnverified = false, resendSuccess = false) }
    }

    fun updateRole(role: com.namangulati.sancharsarthi.core.session.AccessLevel) {
        _uiState.update { it.copy(selectedRole = role) }
    }

    fun resendVerification() {
        val email = _uiState.value.email
        val password = _uiState.value.password
        _uiState.update { it.copy(loading = true, error = null) }
        viewModelScope.launch {
            try {
                firebaseAuthManager.resendVerificationEmail(email, password)
                _uiState.update { it.copy(loading = false, resendSuccess = true, error = "A new verification link has been sent to your email. Please check your inbox.") }
            } catch (e: Exception) {
                _uiState.update { it.copy(loading = false, error = e.localizedMessage ?: "Failed to resend email") }
            }
        }
    }

    fun submit(onSuccess: (com.namangulati.sancharsarthi.core.session.AccessLevel) -> Unit) {
        val email = _uiState.value.email
        val password = _uiState.value.password
        if (email.isBlank() || password.isBlank()) {
            _uiState.update { it.copy(error = "Email and password cannot be empty") }
            return
        }
        _uiState.update { it.copy(loading = true, error = null, isUnverified = false, resendSuccess = false) }
        
        viewModelScope.launch {
            try {
                if (_uiState.value.isSignUp) {
                    firebaseAuthManager.register(email, password)
                    _uiState.update { it.copy(
                        loading = false, 
                        isSignUp = false, 
                        isUnverified = true, 
                        error = "Account created! A verification link has been sent to your email. Please verify before signing in."
                    ) }
                    return@launch
                }

                firebaseAuthManager.login(email, password)
                
                // Fetch actual role from backend
                val meResponse = com.namangulati.sancharsarthi.core.network.RetrofitClient.authApi.getMe()
                val role = parseRole(meResponse.role)
                
                _uiState.update { it.copy(loading = false, selectedRole = role) }
                onSuccess(role)
            } catch (e: Exception) {
                if (e.message == "UNVERIFIED_EMAIL" || e.localizedMessage?.contains("UNVERIFIED_EMAIL") == true) {
                    _uiState.update { it.copy(loading = false, isUnverified = true, error = "Please verify your email address before signing in.") }
                } else {
                    _uiState.update { it.copy(loading = false, error = e.localizedMessage ?: "Authentication failed") }
                }
            }
        }
    }

    fun checkExistingSession(onResult: (com.namangulati.sancharsarthi.core.session.AccessLevel?) -> Unit) {
        viewModelScope.launch {
            val token = firebaseAuthManager.currentToken()
            if (token == null) {
                onResult(null)
                return@launch
            }
            _uiState.update { it.copy(loading = true) }
            try {
                val meResponse = com.namangulati.sancharsarthi.core.network.RetrofitClient.authApi.getMe()
                val role = parseRole(meResponse.role)
                _uiState.update { it.copy(loading = false, selectedRole = role) }
                onResult(role)
            } catch (e: Exception) {
                // If token is invalid or backend rejects it
                _uiState.update { it.copy(loading = false) }
                onResult(null)
            }
        }
    }

    private fun parseRole(backendRole: String): com.namangulati.sancharsarthi.core.session.AccessLevel {
        return when (backendRole) {
            "admin" -> com.namangulati.sancharsarthi.core.session.AccessLevel.Admin
            "police_officer" -> com.namangulati.sancharsarthi.core.session.AccessLevel.PoliceOfficer
            "control_room", "control_room_officer" -> com.namangulati.sancharsarthi.core.session.AccessLevel.ControlRoom
            "citizen" -> com.namangulati.sancharsarthi.core.session.AccessLevel.Citizen
            else -> com.namangulati.sancharsarthi.core.session.AccessLevel.PublicCitizen
        }
    }

    fun logout() {
        firebaseAuthManager.logout()
    }
}
