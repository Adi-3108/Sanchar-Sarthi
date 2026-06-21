package com.namangulati.sancharsarthi.core.report

import kotlinx.serialization.Serializable

enum class ReportMode(
    val id: String,
    val label: String,
    val route: String,
    val routePurpose: String,
) {
    FoundationIncident(
        id = "foundation",
        label = "Public incident",
        route = "POST /api/foundation/incidents/report",
        routePurpose = "Sanchar Sarthi station workflow intake",
    ),
    CongestionSignal(
        id = "congestion",
        label = "Traffic issue",
        route = "POST /api/reports/congestion",
        routePurpose = "EventFlow congestion intelligence signal",
    ),
}

enum class ReportLanguage(val code: String, val label: String) {
    Auto("auto", "Auto"),
    English("en", "English"),
    Kannada("kn", "Kannada"),
    Hindi("hi", "Hindi"),
    Other("other", "Other"),
}

enum class MobileReportSyncStatus(val value: String) {
    Queued("queued"),
    Syncing("syncing"),
    Submitted("submitted"),
    Failed("failed"),
}

@Serializable
data class FoundationIncidentCreateRequest(
    val incident_type: String,
    val title: String,
    val description: String,
    val severity: String,
    val location_name: String,
    val latitude: Double,
    val longitude: Double,
    val locality: String? = null,
    val ward: String? = null,
    val language: String = "auto",
)

data class CitizenReportCreateRequest(
    val report_source: String = "citizen",
    val report_type: String,
    val latitude: Double,
    val longitude: Double,
    val severity: String? = null,
    val description: String,
    val language: String = "auto",
    val event_id: String? = null,
)

data class PendingMobileReport(
    val localId: String,
    val reportMode: String,
    val payloadJson: String,
    val syncStatus: String,
    val retryCount: Int,
    val createdAtMillis: Long,
    val serverReference: String? = null,
    val failureReason: String? = null,
)

data class MobileReportDraft(
    val mode: ReportMode,
    val incidentType: String,
    val reportType: String,
    val title: String,
    val description: String,
    val severity: String,
    val locationName: String,
    val latitudeText: String,
    val longitudeText: String,
    val locality: String? = null,
    val ward: String? = null,
    val language: ReportLanguage = ReportLanguage.Auto,
    val eventId: String? = null,
)

data class MobileReportPreview(
    val heading: String,
    val route: String,
    val details: List<Pair<String, String>>,
)
