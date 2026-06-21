package com.namangulati.sancharsarthi.core.auth

enum class AuthErrorKind(val label: String) {
    FirebaseSignInFailed("Firebase sign-in failed"),
    EmailNotVerified("Email not verified"),
    FirebaseTokenExpired("Firebase token expired"),
    BackendAutoCreatedCitizen("Backend auto-created citizen"),
    OfficerProfileMissing("Officer profile missing"),
    OfficerAssignmentAccessDenied("Officer assignment access denied"),
    InternalRoleMissing("Admin/control-room role missing"),
    BackendUnavailable("Backend unavailable"),
}

data class AuthErrorState(
    val kind: AuthErrorKind,
    val userMessage: String,
    val recoveryHint: String,
    val blocksInternalAccess: Boolean,
)

object AuthErrorCatalog {
    val all: List<AuthErrorState> = listOf(
        AuthErrorState(
            kind = AuthErrorKind.FirebaseSignInFailed,
            userMessage = "Firebase could not sign the user in.",
            recoveryHint = "Let the user retry sign-in without changing their selected role.",
            blocksInternalAccess = true,
        ),
        AuthErrorState(
            kind = AuthErrorKind.EmailNotVerified,
            userMessage = "The Firebase account exists, but email verification is still pending.",
            recoveryHint = "Show resend verification and keep protected backend bootstrap disabled.",
            blocksInternalAccess = true,
        ),
        AuthErrorState(
            kind = AuthErrorKind.FirebaseTokenExpired,
            userMessage = "The Firebase ID token is missing or expired.",
            recoveryHint = "Refresh the ID token before calling protected FastAPI routes.",
            blocksInternalAccess = true,
        ),
        AuthErrorState(
            kind = AuthErrorKind.BackendAutoCreatedCitizen,
            userMessage = "The backend accepted the Firebase user and created a citizen account.",
            recoveryHint = "Route to citizen flows unless the backend later returns an internal role.",
            blocksInternalAccess = false,
        ),
        AuthErrorState(
            kind = AuthErrorKind.OfficerProfileMissing,
            userMessage = "The user is signed in, but no active officer profile was returned.",
            recoveryHint = "Block officer tools and ask an admin/control-room user to link the profile.",
            blocksInternalAccess = true,
        ),
        AuthErrorState(
            kind = AuthErrorKind.OfficerAssignmentAccessDenied,
            userMessage = "The officer profile exists, but no valid station, corridor, zone, or event scope was returned.",
            recoveryHint = "Keep officer tools read-only until backend scope is assigned.",
            blocksInternalAccess = true,
        ),
        AuthErrorState(
            kind = AuthErrorKind.InternalRoleMissing,
            userMessage = "The selected internal role was not confirmed by the backend.",
            recoveryHint = "Show the backend-confirmed landing instead of trusting the UI role hint.",
            blocksInternalAccess = true,
        ),
        AuthErrorState(
            kind = AuthErrorKind.BackendUnavailable,
            userMessage = "FastAPI could not be reached for role verification.",
            recoveryHint = "Keep guest/citizen-safe flows available and retry protected bootstrap later.",
            blocksInternalAccess = true,
        ),
    )

    fun stateFor(kind: AuthErrorKind): AuthErrorState {
        return all.first { it.kind == kind }
    }
}
