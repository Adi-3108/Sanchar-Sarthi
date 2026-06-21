package com.namangulati.sancharsarthi.core.session

enum class AccessLevel(val displayName: String, val landingLabel: String) {
    PublicCitizen(
        displayName = "Public citizen",
        landingLabel = "Guest landing: citizen reporting shell",
    ),
    Citizen(
        displayName = "Citizen",
        landingLabel = "Citizen landing: authenticated public reporting",
    ),
    PoliceOfficer(
        displayName = "Police officer",
        landingLabel = "Officer landing: assignments and live escalation",
    ),
    ControlRoom(
        displayName = "Control room",
        landingLabel = "Control-room landing: triage and city visibility",
    ),
    Admin(
        displayName = "Admin",
        landingLabel = "Admin landing: governance and system summary",
    ),
}

