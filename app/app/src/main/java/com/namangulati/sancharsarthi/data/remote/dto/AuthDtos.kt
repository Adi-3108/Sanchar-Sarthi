package com.namangulati.sancharsarthi.data.remote.dto

import kotlinx.serialization.Serializable

@Serializable
data class OfficerLoginResponseDto(
    val role: String,
    val firebase_uid: String,
    val officer_id: String? = null,
    val police_station: String? = null,
    val assigned_corridors: List<String> = emptyList(),
    val assigned_zones: List<String> = emptyList(),
)

@Serializable
data class OfficerAssignmentsDto(
    val officer_id: String,
    val police_station: String,
    val assigned_events: List<String> = emptyList(),
    val assigned_corridors: List<String> = emptyList(),
    val assigned_zones: List<String> = emptyList(),
    val pending_report_confirmations: List<String> = emptyList(),
)
