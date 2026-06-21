package com.namangulati.sancharsarthi.feature.foundation

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.namangulati.sancharsarthi.core.session.AccessLevel
import com.namangulati.sancharsarthi.core.session.BackendSessionProof
import com.namangulati.sancharsarthi.core.session.FirebaseSessionProof
import com.namangulati.sancharsarthi.core.session.SessionBootstrapResult
import com.namangulati.sancharsarthi.core.session.SessionBootstrapVerifier
import com.namangulati.sancharsarthi.data.local.PlatformBlueprintLocalDataSource
import com.namangulati.sancharsarthi.data.repository.DefaultPlatformBlueprintRepository
import com.namangulati.sancharsarthi.domain.model.MobileArea
import com.namangulati.sancharsarthi.domain.model.PlatformBlueprint
import com.namangulati.sancharsarthi.domain.usecase.GetPlatformBlueprintUseCase
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update

data class PlatformFoundationUiState(
    val blueprint: PlatformBlueprint,
    val selectedAccessLevel: AccessLevel,
    val recommendedLanding: String,
    val recommendedAreas: List<MobileArea>,
    val backendAuthorityNote: String,
    val sessionBootstrapResult: SessionBootstrapResult,
)

class PlatformFoundationViewModel(
    private val getPlatformBlueprint: GetPlatformBlueprintUseCase,
) : ViewModel() {
    private val blueprint = getPlatformBlueprint()
    private val sessionBootstrapVerifier = SessionBootstrapVerifier()

    private val _uiState = MutableStateFlow(buildState(AccessLevel.PublicCitizen))
    val uiState: StateFlow<PlatformFoundationUiState> = _uiState

    fun setAccessLevel(accessLevel: AccessLevel) {
        _uiState.update {
            buildState(accessLevel)
        }
    }

    private fun buildState(accessLevel: AccessLevel): PlatformFoundationUiState {
        val recommendedAreas = blueprint.mobileAreas.filter { area ->
            accessLevel in area.supportedAccessLevels
        }
        return PlatformFoundationUiState(
            blueprint = blueprint,
            selectedAccessLevel = accessLevel,
            recommendedLanding = accessLevel.landingLabel,
            recommendedAreas = recommendedAreas,
            backendAuthorityNote = blueprint.authAuthority.finalAuthority,
            sessionBootstrapResult = buildPreviewSession(accessLevel),
        )
    }

    private fun buildPreviewSession(accessLevel: AccessLevel): SessionBootstrapResult {
        val firebase = if (accessLevel == AccessLevel.PublicCitizen) {
            null
        } else {
            FirebaseSessionProof(
                uid = "demo-firebase-uid",
                email = "demo@sancharsarthi.local",
                emailVerified = true,
            )
        }

        val backend = when (accessLevel) {
            AccessLevel.PublicCitizen -> null
            AccessLevel.Citizen -> BackendSessionProof(
                backendRole = "citizen",
                autoCreatedCitizen = true,
            )
            AccessLevel.PoliceOfficer -> BackendSessionProof(
                backendRole = "police_officer",
                officerId = "OFFICER-DEMO-001",
                policeStation = "HSR Layout",
                assignedCorridors = listOf("ORR East 1"),
                assignedZones = listOf("East"),
                assignedEventIds = listOf("EVT-DEMO-001"),
            )
            AccessLevel.ControlRoom -> BackendSessionProof(
                backendRole = "control_room",
            )
            AccessLevel.Admin -> BackendSessionProof(
                backendRole = "admin",
            )
        }

        return sessionBootstrapVerifier.verify(
            requestedAccessLevel = accessLevel,
            firebase = firebase,
            backend = backend,
        )
    }

    companion object {
        val Factory: ViewModelProvider.Factory = viewModelFactory {
            initializer {
                PlatformFoundationViewModel(
                    getPlatformBlueprint = GetPlatformBlueprintUseCase(
                        repository = DefaultPlatformBlueprintRepository(
                            localDataSource = PlatformBlueprintLocalDataSource(),
                        ),
                    ),
                )
            }
        }
    }
}
