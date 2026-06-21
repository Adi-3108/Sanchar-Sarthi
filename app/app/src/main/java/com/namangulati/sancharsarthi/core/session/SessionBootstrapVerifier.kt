package com.namangulati.sancharsarthi.core.session

import com.namangulati.sancharsarthi.core.auth.AuthErrorCatalog
import com.namangulati.sancharsarthi.core.auth.AuthErrorKind
import com.namangulati.sancharsarthi.core.auth.AuthErrorState

data class FirebaseSessionProof(
    val uid: String?,
    val email: String?,
    val emailVerified: Boolean,
    val tokenExpired: Boolean = false,
)

data class BackendSessionProof(
    val backendRole: String?,
    val officerId: String? = null,
    val policeStation: String? = null,
    val assignedCorridors: List<String> = emptyList(),
    val assignedZones: List<String> = emptyList(),
    val assignedEventIds: List<String> = emptyList(),
    val backendReachable: Boolean = true,
    val autoCreatedCitizen: Boolean = false,
)

sealed class SessionBootstrapResult {
    data class Authorized(
        val session: AppSession,
        val landingLabel: String,
        val notes: List<String>,
    ) : SessionBootstrapResult()

    data class Blocked(
        val error: AuthErrorState,
        val fallbackSession: AppSession,
    ) : SessionBootstrapResult()
}

class SessionBootstrapVerifier {
    fun verify(
        requestedAccessLevel: AccessLevel,
        firebase: FirebaseSessionProof?,
        backend: BackendSessionProof?,
    ): SessionBootstrapResult {
        if (requestedAccessLevel == AccessLevel.PublicCitizen) {
            return authorized(
                session = AppSession(accessLevel = AccessLevel.PublicCitizen),
                landingLabel = AccessLevel.PublicCitizen.landingLabel,
                notes = listOf("Guest public reporting needs no Firebase token."),
            )
        }

        val firebaseProof = firebase ?: return blocked(AuthErrorKind.FirebaseSignInFailed)
        if (firebaseProof.uid.isNullOrBlank()) {
            return blocked(AuthErrorKind.FirebaseSignInFailed)
        }
        if (!firebaseProof.emailVerified) {
            return blocked(AuthErrorKind.EmailNotVerified)
        }
        if (firebaseProof.tokenExpired) {
            return blocked(AuthErrorKind.FirebaseTokenExpired)
        }

        val backendProof = backend ?: return blocked(AuthErrorKind.BackendUnavailable)
        if (!backendProof.backendReachable) {
            return blocked(AuthErrorKind.BackendUnavailable)
        }

        val backendAccessLevel = RoleAliasNormalizer.normalize(backendProof.backendRole)
        val backendSession = AppSession(
            firebaseUid = firebaseProof.uid,
            email = firebaseProof.email,
            accessLevel = backendAccessLevel ?: AccessLevel.Citizen,
            backendRole = backendProof.backendRole,
            officerId = backendProof.officerId,
            policeStation = backendProof.policeStation,
            assignedCorridors = backendProof.assignedCorridors,
            assignedZones = backendProof.assignedZones,
            assignedEventIds = backendProof.assignedEventIds,
        )

        if (backendProof.autoCreatedCitizen || backendAccessLevel == AccessLevel.Citizen) {
            return when (requestedAccessLevel) {
                AccessLevel.Citizen -> authorized(
                    session = backendSession.copy(accessLevel = AccessLevel.Citizen),
                    landingLabel = AccessLevel.Citizen.landingLabel,
                    notes = listOf(AuthErrorCatalog.stateFor(AuthErrorKind.BackendAutoCreatedCitizen).userMessage),
                )
                else -> blocked(AuthErrorKind.InternalRoleMissing, backendSession.copy(accessLevel = AccessLevel.Citizen))
            }
        }

        if (backendAccessLevel != requestedAccessLevel) {
            return blocked(AuthErrorKind.InternalRoleMissing, backendSession)
        }

        if (requestedAccessLevel == AccessLevel.PoliceOfficer) {
            if (backendProof.officerId.isNullOrBlank()) {
                return blocked(AuthErrorKind.OfficerProfileMissing, backendSession)
            }
            if (!backendProof.hasOfficerScope()) {
                return blocked(AuthErrorKind.OfficerAssignmentAccessDenied, backendSession)
            }
        }

        return authorized(
            session = backendSession.copy(accessLevel = requestedAccessLevel),
            landingLabel = requestedAccessLevel.landingLabel,
            notes = listOf("Backend-confirmed role and scope are active for this mobile session."),
        )
    }

    private fun authorized(
        session: AppSession,
        landingLabel: String,
        notes: List<String>,
    ): SessionBootstrapResult.Authorized {
        return SessionBootstrapResult.Authorized(
            session = session,
            landingLabel = landingLabel,
            notes = notes,
        )
    }

    private fun blocked(
        kind: AuthErrorKind,
        fallbackSession: AppSession = AppSession(accessLevel = AccessLevel.PublicCitizen),
    ): SessionBootstrapResult.Blocked {
        return SessionBootstrapResult.Blocked(
            error = AuthErrorCatalog.stateFor(kind),
            fallbackSession = fallbackSession,
        )
    }

    private fun BackendSessionProof.hasOfficerScope(): Boolean {
        return !officerId.isNullOrBlank() &&
            (
                !policeStation.isNullOrBlank() ||
                    assignedCorridors.isNotEmpty() ||
                    assignedZones.isNotEmpty() ||
                    assignedEventIds.isNotEmpty()
                )
    }
}
