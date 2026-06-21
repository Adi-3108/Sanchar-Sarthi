package com.namangulati.sancharsarthi.core.report

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CitizenReportSubmissionPlannerTest {
    @Test
    fun foundationDraft_buildsFoundationIncidentPayloadOnly() {
        val draft = validDraft(mode = ReportMode.FoundationIncident)

        val payload = CitizenReportSubmissionPlanner.buildPayloadJson(draft)
        val request = CitizenReportSubmissionPlanner.buildFoundationRequest(draft)

        assertEquals("road_obstruction", request.incident_type)
        assertEquals("Public incident near junction", request.title)
        assertTrue(payload.contains("\"incident_type\":\"road_obstruction\""))
        assertTrue(payload.contains("\"location_name\":\"MG Road\""))
        assertFalse(payload.contains("\"report_source\":\"citizen\""))
    }

    @Test
    fun congestionDraft_buildsCongestionSignalPayloadOnly() {
        val draft = validDraft(mode = ReportMode.CongestionSignal)

        val payload = CitizenReportSubmissionPlanner.buildPayloadJson(draft)
        val request = CitizenReportSubmissionPlanner.buildCongestionRequest(draft)

        assertEquals("citizen", request.report_source)
        assertEquals("congestion", request.report_type)
        assertTrue(payload.contains("\"report_source\":\"citizen\""))
        assertTrue(payload.contains("\"report_type\":\"congestion\""))
        assertFalse(payload.contains("\"incident_type\":\"road_obstruction\""))
    }

    @Test
    fun validation_requiresDescriptionAndCoordinates() {
        val errors = CitizenReportSubmissionPlanner.validate(
            validDraft(mode = ReportMode.CongestionSignal).copy(
                description = "",
                latitudeText = "not-a-number",
            ),
        )

        assertTrue(errors.any { it.contains("Description") })
        assertTrue(errors.any { it.contains("Latitude") })
    }

    @Test
    fun pendingReport_usesLocalIdAndDoesNotAssumeBackendIdempotency() {
        val result = CitizenReportSubmissionPlanner.createPendingReport(
            draft = validDraft(mode = ReportMode.CongestionSignal),
            nowMillis = 12345L,
        )

        assertTrue(result.isSuccess)
        val pending = result.getOrThrow()
        assertTrue(pending.localId.startsWith("congestion-12345-"))
        assertEquals("congestion", pending.reportMode)
        assertEquals("queued", pending.syncStatus)
        assertEquals(0, pending.retryCount)
        assertEquals(null, pending.serverReference)
    }

    @Test
    fun congestionPreviewDocumentsBackendIntelligenceFields() {
        val preview = CitizenReportSubmissionPlanner.buildPreview(
            validDraft(mode = ReportMode.CongestionSignal),
        )
        val labels = preview.details.map { it.first }

        assertTrue(labels.contains("matched_event_id"))
        assertTrue(labels.contains("report_confidence"))
        assertTrue(labels.contains("impact_score_change"))
        assertTrue(labels.contains("new_alert_level"))
        assertTrue(labels.contains("recommended_action"))
    }

    private fun validDraft(mode: ReportMode): MobileReportDraft {
        return MobileReportDraft(
            mode = mode,
            incidentType = "road_obstruction",
            reportType = "congestion",
            title = "Public incident near junction",
            description = "Traffic is building up near the signal.",
            severity = "medium",
            locationName = "MG Road",
            latitudeText = "12.9716",
            longitudeText = "77.5946",
            language = ReportLanguage.Auto,
        )
    }
}
