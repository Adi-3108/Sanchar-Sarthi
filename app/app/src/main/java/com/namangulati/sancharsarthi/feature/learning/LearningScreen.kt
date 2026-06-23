package com.namangulati.sancharsarthi.feature.learning

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.namangulati.sancharsarthi.core.design.SkeletonScreen
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

@Composable
fun LearningScreen(
    state: PlatformFoundationUiState,
    viewModel: LearningViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp, vertical = 24.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(24.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFFF0F9FF)),
                border = BorderStroke(1.dp, Color(0xFFBAE6FD))
            ) {
                Column(modifier = Modifier.padding(24.dp)) {
                    AutoTranslatedText("GENERATE REPORT", fontSize = 12.sp, color = Color(0xFF0284C7), fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(16.dp))
                    OutlinedTextField(
                        value = uiState.eventIdInput,
                        onValueChange = { viewModel.updateEventId(it) },
                        label = { AutoTranslatedText("Event ID") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                            focusedContainerColor = MaterialTheme.colorScheme.surface
                        )
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Button(
                        onClick = { viewModel.generateReport() },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                        enabled = !uiState.isLoading,
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                    ) {
                        AutoTranslatedText(if (uiState.isLoading) "Generating..." else "Generate After-Action Report")
                    }
                    if (uiState.error != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        AutoTranslatedText(uiState.error!!, color = Color.Red, fontSize = 12.sp)
                    }
                }
            }
        }

        if (uiState.isLoading) {
            item {
                SkeletonScreen(cards = 3)
            }
        } else if (uiState.result != null) {
            val result = uiState.result!!
            
            // Header
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
                ) {
                    Column(modifier = Modifier.padding(24.dp)) {
                        AutoTranslatedText("POST-EVENT LEARNING", fontSize = 12.sp, color = Color(0xFF10B981), fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(8.dp))
                        AutoTranslatedText("After-action report", fontSize = 28.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                        Spacer(modifier = Modifier.height(16.dp))
                        Row(horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.Top, modifier = Modifier.fillMaxWidth()) {
                            AutoTranslatedText(result.event_summary ?: "No summary available.", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 14.sp, modifier = Modifier.weight(1f))
                            Spacer(modifier = Modifier.width(16.dp))
                            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF064E3B)), shape = RoundedCornerShape(16.dp), border = BorderStroke(1.dp, Color(0xFF34D399))) {
                                AutoTranslatedText((result.final_status ?: "CLOSED").uppercase(), modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp), fontSize = 12.sp, color = Color(0xFF6EE7B7), fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }

            // Metrics Grid
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                    MetricBox(modifier = Modifier.weight(1f), label = "PREDICTED IMPACT", value = result.predicted_impact_score?.toString() ?: "0.0")
                    MetricBox(modifier = Modifier.weight(1f), label = "OBSERVED IMPACT", value = result.simulated_actual_impact_score?.toString() ?: "0.0")
                }
                Spacer(modifier = Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                    MetricBox(modifier = Modifier.weight(1f), label = "DEVIATION", value = result.impact_deviation?.toString() ?: "0.0")
                    
                    val reportsConsidered = result.report_json?.jsonObject?.get("reports_considered")?.jsonPrimitive?.content ?: "0"
                    MetricBox(modifier = Modifier.weight(1f), label = "REPORTS CONSIDERED", value = reportsConsidered)
                }
            }

            // Summaries 2x2 Grid (Stacked for mobile)
            item { SummaryCard(label = "PREDICTION SUMMARY", text = result.prediction_summary) }
            item { SummaryCard(label = "RECOMMENDATION SUMMARY", text = result.recommendation_summary) }
            item { SummaryCard(label = "CITIZEN REPORT SUMMARY", text = result.citizen_report_summary) }
            item { SummaryCard(label = "LIVE ESCALATION SUMMARY", text = result.live_escalation_summary) }

            // Lessons Learned
            item { HighlightCard(label = "LESSONS LEARNED", text = result.lessons_learned, borderColor = Color(0xFF059669), labelColor = Color(0xFF34D399)) }
            
            // Future Recommendations
            item { HighlightCard(label = "FUTURE RECOMMENDATIONS", text = result.future_recommendations, borderColor = Color(0xFF0284C7), labelColor = Color(0xFF38BDF8)) }

            // Structured Learning Snapshot
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)),
                    border = BorderStroke(1.dp, Color(0xFF1E293B))
                ) {
                    Column(modifier = Modifier.padding(24.dp)) {
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            AutoTranslatedText("STRUCTURED LEARNING SNAPSHOT", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                            AutoTranslatedText("Stored in post_event_reports.report_json", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        val highConf = result.report_json?.jsonObject?.get("high_confidence_reports")?.jsonPrimitive?.content ?: "0"
                        val liveUp = result.report_json?.jsonObject?.get("live_updates_count")?.jsonPrimitive?.content ?: "0"
                        val critUp = result.report_json?.jsonObject?.get("critical_updates_count")?.jsonPrimitive?.content ?: "0"
                        val weatherSrc = result.report_json?.jsonObject?.get("weather_source")?.jsonPrimitive?.content ?: "unknown"

                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                            SnapshotBox(modifier = Modifier.weight(1f), label = "HIGH CONFIDENCE\nREPORTS", value = highConf)
                            SnapshotBox(modifier = Modifier.weight(1f), label = "LIVE UPDATES", value = liveUp)
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                            SnapshotBox(modifier = Modifier.weight(1f), label = "CRITICAL UPDATES", value = critUp)
                            SnapshotBox(modifier = Modifier.weight(1f), label = "WEATHER SOURCE", value = weatherSrc)
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun MetricBox(modifier: Modifier = Modifier, label: String, value: String) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)),
        border = BorderStroke(1.dp, Color(0xFF1E293B))
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(value, fontSize = 24.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
        }
    }
}

@Composable
fun SummaryCard(label: String, text: String?) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(12.dp))
            AutoTranslatedText(text ?: "N/A", fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurface)
        }
    }
}

@Composable
fun HighlightCard(label: String, text: String?, borderColor: Color, labelColor: Color) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)),
        border = BorderStroke(1.dp, borderColor)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = labelColor, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(12.dp))
            AutoTranslatedText(text ?: "N/A", fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurface)
        }
    }
}

@Composable
fun SnapshotBox(modifier: Modifier = Modifier, label: String, value: String) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF020617))
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            AutoTranslatedText(label, fontSize = 9.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(value, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
        }
    }
}

