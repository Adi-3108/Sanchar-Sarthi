package com.namangulati.sancharsarthi.core.session

object RoleAliasNormalizer {
    fun normalize(rawRole: String?): AccessLevel? {
        val normalized = rawRole
            ?.trim()
            ?.lowercase()
            ?.replace("-", "_")
            ?.replace(" ", "_")

        return when (normalized) {
            "admin" -> AccessLevel.Admin
            "control_room", "controlroom", "command_center" -> AccessLevel.ControlRoom
            "police_officer", "police", "officer" -> AccessLevel.PoliceOfficer
            "citizen", "user" -> AccessLevel.Citizen
            "public_citizen", "guest", null, "" -> AccessLevel.PublicCitizen
            else -> null
        }
    }
}
