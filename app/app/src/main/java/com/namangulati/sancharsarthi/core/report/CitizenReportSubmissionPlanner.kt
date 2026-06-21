package com.namangulati.sancharsarthi.core.report

import java.util.Locale
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

object CitizenReportSubmissionPlanner {
    private const val PUBLIC_RATE_LIMIT_SUMMARY = "10 public congestion reports per 60 seconds per client source bucket"

    fun validate(draft: MobileReportDraft): List<String> {
        val errors = mutableListOf<String>()

        if (draft.description.isBlank()) {
            errors += "Description is required."
        }
        if (draft.locationName.isBlank()) {
            errors += "Location name is required when GPS is not used."
        }
        if (draft.latitudeText.toDoubleOrNull() == null) {
            errors += "Latitude must be a valid number."
        }
        if (draft.longitudeText.toDoubleOrNull() == null) {
            errors += "Longitude must be a valid number."
        }
        if (draft.mode == ReportMode.FoundationIncident && draft.title.isBlank()) {
            errors += "Incident title is required for foundation intake."
        }
        if (draft.mode == ReportMode.CongestionSignal && draft.reportType.isBlank()) {
            errors += "Report type is required for congestion intelligence."
        }

        return errors
    }

    fun createPendingReport(
        draft: MobileReportDraft,
        nowMillis: Long,
    ): Result<PendingMobileReport> {
        val errors = validate(draft)
        if (errors.isNotEmpty()) {
            return Result.failure(IllegalArgumentException(errors.joinToString(" ")))
        }

        val localId = buildLocalId(draft, nowMillis)
        return Result.success(
            PendingMobileReport(
                localId = localId,
                reportMode = draft.mode.id,
                payloadJson = buildPayloadJson(draft),
                syncStatus = MobileReportSyncStatus.Queued.value,
                retryCount = 0,
                createdAtMillis = nowMillis,
            ),
        )
    }

    fun buildPreview(draft: MobileReportDraft): MobileReportPreview {
        return when (draft.mode) {
            ReportMode.FoundationIncident -> MobileReportPreview(
                heading = "Accepted for station workflow preview",
                route = ReportMode.FoundationIncident.route,
                details = listOf(
                    "Status" to "queued locally until backend submission",
                    "Incident type" to draft.incidentType,
                    "Severity" to draft.severity,
                    "Language" to draft.language.code,
                ),
            )
            ReportMode.CongestionSignal -> MobileReportPreview(
                heading = "EventFlow intelligence feedback preview",
                route = ReportMode.CongestionSignal.route,
                details = listOf(
                    "matched_event_id" to (draft.eventId?.takeIf { it.isNotBlank() } ?: "pending backend match"),
                    "report_confidence" to "backend-calculated after submission",
                    "impact_score_change" to "backend-calculated after submission",
                    "new_alert_level" to "backend-calculated after submission",
                    "recommended_action" to "backend recommendation returned by congestion endpoint",
                    "public_rate_limit" to PUBLIC_RATE_LIMIT_SUMMARY,
                ),
            )
        }
    }

    fun buildFoundationRequest(draft: MobileReportDraft): FoundationIncidentCreateRequest {
        return FoundationIncidentCreateRequest(
            incident_type = draft.incidentType,
            title = draft.title,
            description = draft.description,
            severity = draft.severity,
            location_name = draft.locationName,
            latitude = draft.latitudeText.toDouble(),
            longitude = draft.longitudeText.toDouble(),
            locality = draft.locality?.takeIf { it.isNotBlank() },
            ward = draft.ward?.takeIf { it.isNotBlank() },
            language = draft.language.code,
        )
    }

    fun buildCongestionRequest(draft: MobileReportDraft): CitizenReportCreateRequest {
        return CitizenReportCreateRequest(
            report_type = draft.reportType,
            latitude = draft.latitudeText.toDouble(),
            longitude = draft.longitudeText.toDouble(),
            severity = draft.severity.takeIf { it.isNotBlank() },
            description = draft.description,
            language = draft.language.code,
            event_id = draft.eventId?.takeIf { it.isNotBlank() },
        )
    }

    fun buildPayloadJson(draft: MobileReportDraft): String {
        return when (draft.mode) {
            ReportMode.FoundationIncident -> foundationJson(buildFoundationRequest(draft))
            ReportMode.CongestionSignal -> congestionJson(buildCongestionRequest(draft))
        }
    }

    private fun buildLocalId(draft: MobileReportDraft, nowMillis: Long): String {
        val locationPart = "${draft.latitudeText},${draft.longitudeText}".lowercase(Locale.US)
        val modePart = draft.mode.id
        val hashPart = "${draft.description}|${draft.locationName}|$locationPart".hashCode().toUInt().toString(16)
        return "$modePart-$nowMillis-$hashPart"
    }

    private fun foundationJson(request: FoundationIncidentCreateRequest): String {
        return Json.encodeToString(request)
    }

    private fun congestionJson(request: CitizenReportCreateRequest): String {
        return Json.encodeToString(request)
    }
}
