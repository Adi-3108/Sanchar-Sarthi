package com.namangulati.sancharsarthi.core.session

data class AppSession(
    val firebaseUid: String? = null,
    val email: String? = null,
    val accessLevel: AccessLevel = AccessLevel.PublicCitizen,
    val backendRole: String? = null,
    val officerId: String? = null,
    val policeStation: String? = null,
    val assignedCorridors: List<String> = emptyList(),
    val assignedZones: List<String> = emptyList(),
    val assignedEventIds: List<String> = emptyList(),
) {
    val isGuest: Boolean = firebaseUid == null && accessLevel == AccessLevel.PublicCitizen
}
