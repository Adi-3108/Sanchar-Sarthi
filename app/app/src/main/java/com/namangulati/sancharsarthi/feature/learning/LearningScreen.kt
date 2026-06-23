package com.namangulati.sancharsarthi.feature.learning

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.namangulati.sancharsarthi.core.design.SkeletonScreen
import com.namangulati.sancharsarthi.core.network.PostEventLearningResponse
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState
import java.util.Locale
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

private val ScreenBackground = Color(0xFFF8FAFC)
private val PanelColor = Color(0xFFFFFFFF)
private val PanelAltColor = Color(0xFFF1F5F9)
private val BorderColor = Color(0xFFD8E3F0)
private val HeadingColor = Color(0xFF0F172A)
private val BodyColor = Color(0xFF334155)
private val MutedColor = Color(0xFF64748B)
private val AccentColor = Color(0xFF1769B6)
private val AccentSoftColor = Color(0xFF3B82F6)
private val SuccessBgColor = Color(0xFFE8F8F0)
private val SuccessBorderColor = Color(0xFF94DDBD)
private val SuccessTextColor = Color(0xFF047857)

@Composable
fun LearningScreen(
    state: PlatformFoundationUiState,
    viewModel: LearningViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(ScreenBackground)
            .padding(horizontal = 16.dp, vertical = 24.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        item {
            GenerateReportCard(
                eventId = uiState.eventIdInput,
                isLoading = uiState.isLoading,
                error = uiState.error,
                onEventIdChange = viewModel::updateEventId,
                onGenerate = viewModel::generateReport,
            )
        }

        if (uiState.isLoading) {
            item { SkeletonScreen(cards = 3) }
        } else if (uiState.result != null) {
            val result = uiState.result!!
            val reportJson = result.report_json

            item { ReportHeader(result = result) }

            item {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                    MetricBox(
                        modifier = Modifier.weight(1f),
                        label = "PREDICTED IMPACT",
                        value = formatNumber(result.predicted_impact_score),
                    )
                    MetricBox(
                        modifier = Modifier.weight(1f),
                        label = "OBSERVED IMPACT",
                        value = formatNumber(result.simulated_actual_impact_score),
                    )
                }
                Spacer(modifier = Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                    MetricBox(
                        modifier = Modifier.weight(1f),
                        label = "DEVIATION",
                        value = formatNumber(result.impact_deviation),
                    )
                    MetricBox(
                        modifier = Modifier.weight(1f),
                        label = "REPORTS CONSIDERED",
                        value = reportMetric(reportJson, "report_count", fallback = "0"),
                    )
                }
            }

            item { SummaryCard(label = "PREDICTION SUMMARY", text = result.prediction_summary) }
            item { SummaryCard(label = "RECOMMENDATION SUMMARY", text = result.recommendation_summary) }
            item { SummaryCard(label = "CITIZEN REPORT SUMMARY", text = result.citizen_report_summary) }
            item { SummaryCard(label = "LIVE ESCALATION SUMMARY", text = result.live_escalation_summary) }

            item {
                HighlightCard(
                    label = "LESSONS LEARNED",
                    text = result.lessons_learned,
                    borderColor = Color(0xFF86EFAC),
                    labelColor = SuccessTextColor,
                )
            }
            item {
                HighlightCard(
                    label = "FUTURE RECOMMENDATIONS",
                    text = result.future_recommendations,
                    borderColor = Color(0xFF93C5FD),
                    labelColor = AccentColor,
                )
            }

            item {
                StructuredSnapshot(reportJson = reportJson)
            }
        }
    }
}

@Composable
private fun GenerateReportCard(
    eventId: String,
    isLoading: Boolean,
    error: String?,
    onEventIdChange: (String) -> Unit,
    onGenerate: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFEFF6FF)),
        border = BorderStroke(1.dp, Color(0xFFBFDBFE))
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            AutoTranslatedText(
                "GENERATE REPORT",
                fontSize = 12.sp,
                color = AccentColor,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(16.dp))
            OutlinedTextField(
                value = eventId,
                onValueChange = onEventIdChange,
                label = { AutoTranslatedText("Event ID", color = MutedColor) },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = HeadingColor,
                    unfocusedTextColor = HeadingColor,
                    focusedContainerColor = PanelColor,
                    unfocusedContainerColor = PanelColor,
                    focusedBorderColor = AccentSoftColor,
                    unfocusedBorderColor = Color(0xFFBFD3EA),
                    cursorColor = AccentColor,
                )
            )
            Spacer(modifier = Modifier.height(16.dp))
            Button(
                onClick = onGenerate,
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                enabled = !isLoading,
                colors = ButtonDefaults.buttonColors(containerColor = AccentColor)
            ) {
                AutoTranslatedText(if (isLoading) "Generating..." else "Generate After-Action Report")
            }
            if (error != null) {
                Spacer(modifier = Modifier.height(8.dp))
                AutoTranslatedText(error, color = Color(0xFFDC2626), fontSize = 12.sp)
            }
        }
    }
}

@Composable
private fun ReportHeader(result: PostEventLearningResponse) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = PanelColor),
        border = BorderStroke(1.dp, BorderColor)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            AutoTranslatedText(
                "POST-EVENT LEARNING",
                fontSize = 12.sp,
                color = AccentColor,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(
                "After-action report",
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = HeadingColor,
            )
            Spacer(modifier = Modifier.height(16.dp))
            Row(
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top,
                modifier = Modifier.fillMaxWidth()
            ) {
                AutoTranslatedText(
                    result.event_summary ?: "No summary available.",
                    color = BodyColor,
                    fontSize = 14.sp,
                    modifier = Modifier.weight(1f),
                )
                Spacer(modifier = Modifier.width(12.dp))
                Card(
                    colors = CardDefaults.cardColors(containerColor = SuccessBgColor),
                    shape = RoundedCornerShape(16.dp),
                    border = BorderStroke(1.dp, SuccessBorderColor)
                ) {
                    Text(
                        text = (result.final_status ?: "CLOSED").uppercase(Locale.US),
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
                        fontSize = 12.sp,
                        color = SuccessTextColor,
                        fontWeight = FontWeight.Bold,
                    )
                }
            }
        }
    }
}

@Composable
private fun MetricBox(modifier: Modifier = Modifier, label: String, value: String) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = PanelColor),
        border = BorderStroke(1.dp, BorderColor)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = MutedColor, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text(value, fontSize = 22.sp, fontWeight = FontWeight.Bold, color = HeadingColor)
        }
    }
}

@Composable
private fun SummaryCard(label: String, text: String?) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = PanelAltColor),
        border = BorderStroke(1.dp, Color(0xFFE2E8F0))
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = MutedColor, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(12.dp))
            AutoTranslatedText(text ?: "N/A", fontSize = 14.sp, color = BodyColor)
        }
    }
}

@Composable
private fun HighlightCard(label: String, text: String?, borderColor: Color, labelColor: Color) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = PanelColor),
        border = BorderStroke(1.dp, borderColor)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = labelColor, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(12.dp))
            AutoTranslatedText(text ?: "N/A", fontSize = 14.sp, color = BodyColor)
        }
    }
}

@Composable
private fun StructuredSnapshot(reportJson: JsonObject?) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = PanelColor),
        border = BorderStroke(1.dp, BorderColor)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            AutoTranslatedText(
                "STRUCTURED LEARNING SNAPSHOT",
                fontSize = 12.sp,
                color = MutedColor,
                fontWeight = FontWeight.Bold,
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Stored in post_event_reports.report_json",
                fontSize = 10.sp,
                color = MutedColor,
            )
            Spacer(modifier = Modifier.height(16.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                SnapshotBox(
                    modifier = Modifier.weight(1f),
                    label = "HIGH CONFIDENCE REPORTS",
                    value = reportMetric(reportJson, "high_confidence_report_count", fallback = "0"),
                )
                SnapshotBox(
                    modifier = Modifier.weight(1f),
                    label = "LIVE UPDATES",
                    value = reportMetric(reportJson, "live_update_count", fallback = "0"),
                )
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                SnapshotBox(
                    modifier = Modifier.weight(1f),
                    label = "CRITICAL UPDATES",
                    value = reportMetric(reportJson, "critical_live_update_count", fallback = "0"),
                )
                SnapshotBox(
                    modifier = Modifier.weight(1f),
                    label = "WEATHER SOURCE",
                    value = reportMetric(
                        reportJson,
                        "recommendation_weather_source",
                        fallback = "n/a",
                        titleCase = true,
                    ),
                )
            }
        }
    }
}

@Composable
private fun SnapshotBox(modifier: Modifier = Modifier, label: String, value: String) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = PanelAltColor),
        border = BorderStroke(1.dp, Color(0xFFE2E8F0))
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            AutoTranslatedText(label, fontSize = 9.sp, color = MutedColor, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            Text(value, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = HeadingColor)
        }
    }
}

private fun formatNumber(value: Double?): String {
    return value?.let { String.format(Locale.US, "%.1f", it) } ?: "n/a"
}

private fun reportMetric(
    reportJson: JsonObject?,
    key: String,
    fallback: String = "n/a",
    titleCase: Boolean = false,
): String {
    val raw = reportJson
        ?.jsonObject
        ?.get(key)
        ?.jsonPrimitive
        ?.contentOrNull
        ?.takeIf { it.isNotBlank() }
        ?: return fallback

    return if (titleCase) raw.toDisplayLabel() else raw
}

private fun String.toDisplayLabel(): String {
    return replace('_', ' ')
        .split(' ')
        .filter { it.isNotBlank() }
        .joinToString(" ") { word ->
            word.lowercase(Locale.US).replaceFirstChar { firstChar ->
                if (firstChar.isLowerCase()) firstChar.titlecase(Locale.US) else firstChar.toString()
            }
        }
}
