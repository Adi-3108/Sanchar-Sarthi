package com.namangulati.sancharsarthi.core.session

import com.namangulati.sancharsarthi.core.auth.AuthErrorKind
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SessionBootstrapVerifierTest {
    private val verifier = SessionBootstrapVerifier()

    @Test
    fun publicCitizen_needsNoFirebaseOrBackendProof() {
        val result = verifier.verify(
            requestedAccessLevel = AccessLevel.PublicCitizen,
            firebase = null,
            backend = null,
        )

        assertTrue(result is SessionBootstrapResult.Authorized)
        assertEquals(AccessLevel.PublicCitizen, (result as SessionBootstrapResult.Authorized).session.accessLevel)
    }

    @Test
    fun officerAccess_requiresActiveOfficerProfile() {
        val result = verifier.verify(
            requestedAccessLevel = AccessLevel.PoliceOfficer,
            firebase = verifiedFirebase(),
            backend = BackendSessionProof(backendRole = "police_officer"),
        )

        assertTrue(result is SessionBootstrapResult.Blocked)
        assertEquals(
            AuthErrorKind.OfficerProfileMissing,
            (result as SessionBootstrapResult.Blocked).error.kind,
        )
    }

    @Test
    fun officerAccess_requiresStationCorridorZoneOrEventScope() {
        val result = verifier.verify(
            requestedAccessLevel = AccessLevel.PoliceOfficer,
            firebase = verifiedFirebase(),
            backend = BackendSessionProof(
                backendRole = "police_officer",
                officerId = "OFFICER-1",
            ),
        )

        assertTrue(result is SessionBootstrapResult.Blocked)
        assertEquals(
            AuthErrorKind.OfficerAssignmentAccessDenied,
            (result as SessionBootstrapResult.Blocked).error.kind,
        )
    }

    @Test
    fun citizenBackendRoleCannotUnlockOfficerTools() {
        val result = verifier.verify(
            requestedAccessLevel = AccessLevel.PoliceOfficer,
            firebase = verifiedFirebase(),
            backend = BackendSessionProof(backendRole = "citizen", autoCreatedCitizen = true),
        )

        assertTrue(result is SessionBootstrapResult.Blocked)
        assertEquals(
            AuthErrorKind.InternalRoleMissing,
            (result as SessionBootstrapResult.Blocked).error.kind,
        )
        assertEquals(AccessLevel.Citizen, result.fallbackSession.accessLevel)
    }

    @Test
    fun officerWithBackendScopeIsAuthorized() {
        val result = verifier.verify(
            requestedAccessLevel = AccessLevel.PoliceOfficer,
            firebase = verifiedFirebase(),
            backend = BackendSessionProof(
                backendRole = "police_officer",
                officerId = "OFFICER-1",
                assignedCorridors = listOf("ORR East 1"),
            ),
        )

        assertTrue(result is SessionBootstrapResult.Authorized)
        assertEquals(AccessLevel.PoliceOfficer, (result as SessionBootstrapResult.Authorized).session.accessLevel)
        assertEquals("OFFICER-1", result.session.officerId)
    }

    private fun verifiedFirebase(): FirebaseSessionProof {
        return FirebaseSessionProof(
            uid = "firebase-user-1",
            email = "officer@sancharsarthi.local",
            emailVerified = true,
        )
    }
}
