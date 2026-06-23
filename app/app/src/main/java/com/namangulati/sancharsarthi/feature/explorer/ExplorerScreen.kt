package com.namangulati.sancharsarthi.feature.explorer

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.namangulati.sancharsarthi.core.design.SkeletonList
import com.namangulati.sancharsarthi.core.design.SkeletonMetricGrid
import com.namangulati.sancharsarthi.core.network.EventDetailResponse
import com.namangulati.sancharsarthi.core.network.HotspotResponseItem
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState

@Composable
fun ExplorerScreen(
    state: PlatformFoundationUiState,
    viewModel: ExplorerViewModel = viewModel()
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
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
            ) {
                Column(modifier = Modifier.padding(24.dp)) {
                    AutoTranslatedText("EXPLORER", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(12.dp))
                    AutoTranslatedText("Dataset-backed hotspot and event dossier explorer.", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                }
            }
        }

        if (uiState.eventDetail == null) {
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                ) {
                    Column(modifier = Modifier.padding(24.dp)) {
                        AutoTranslatedText("DATASET", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(16.dp))
                        if (uiState.isSummaryLoading) {
                            SkeletonMetricGrid(count = 4)
                        } else if (uiState.summary != null) {
                            val summary = uiState.summary!!
                            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                MetricItem("Total events", summary.total_events.toString())
                                MetricItem("Planned", summary.planned_events.toString())
                                MetricItem("Unplanned", summary.unplanned_events.toString())
                                MetricItem("Hotspots", summary.hotspot_count.toString())
                            }
                        }
                    }
                }
            }
        }
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(24.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
            ) {
                Column(modifier = Modifier.padding(24.dp)) {
                    AutoTranslatedText("OPEN DOSSIER", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(16.dp))
                    OutlinedTextField(
                        value = uiState.eventIdInput,
                        onValueChange = { viewModel.updateEventIdInput(it) },
                        label = { AutoTranslatedText("Event ID") },
                        placeholder = { AutoTranslatedText("FKID000001") },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Button(
                        onClick = { viewModel.fetchEventDossier() },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary, contentColor = MaterialTheme.colorScheme.onPrimary)
                    ) {
                        AutoTranslatedText(if (uiState.isEventLoading) "Opening..." else "Open event")
                    }
                    if (uiState.eventLoadError != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        AutoTranslatedText(uiState.eventLoadError!!, color = Color.Red, fontSize = 12.sp)
                    }
                }
            }
        }

        if (uiState.eventDetail != null) {
            val detail = uiState.eventDetail!!
            item { EventDnaPanel(detail = detail) }
            item { RecommendationPanel(detail = detail) }
            item { SimilarEventsPanel(detail = detail) }
            item { LiveEscalationTimeline(detail = detail) }
        } else {
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                ) {
                    Column(modifier = Modifier.padding(24.dp)) {
                        AutoTranslatedText("HOTSPOT CLUSTERS", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        if (uiState.isHotspotsLoading) {
                            SkeletonList(count = 3)
                        } else if (uiState.hotspots.isEmpty()) {
                            AutoTranslatedText("No hotspots match the selected filter.", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 14.sp)
                        } else {
                            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                                uiState.hotspots.forEach { hotspot ->
                                    HotspotCard(hotspot)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun EventDnaPanel(detail: EventDetailResponse) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("EVENT DNA", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Operational fingerprint", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(detail.event_dna?.dna_summary ?: "No fingerprint available.", fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            
            Spacer(modifier = Modifier.height(24.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                DarkMetricCard(modifier = Modifier.weight(1f), label = "SIMILAR MEMORY", value = "${detail.similar_events?.size ?: 0} matches")
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            DarkInfoCard(label = "TIME CONTEXT", text = detail.event_dna?.time_context ?: "N/A")
            Spacer(modifier = Modifier.height(12.dp))
            DarkInfoCard(label = "LOCATION CONTEXT", text = detail.event_dna?.location_context ?: "N/A")
            Spacer(modifier = Modifier.height(12.dp))
            DarkInfoCard(label = "CAUSE CONTEXT", text = detail.event_dna?.cause_context ?: "N/A")
            Spacer(modifier = Modifier.height(12.dp))
            DarkInfoCard(label = "HISTORICAL PATTERN", text = detail.event_dna?.historical_pattern ?: "N/A")
            
            Spacer(modifier = Modifier.height(24.dp))
            AutoTranslatedText("RISK INDICATORS", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(12.dp))
            
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                DarkMetricCard(modifier = Modifier.weight(1f), label = "IS PEAK HOUR", value = if (detail.features?.is_peak_hour == true) "100%" else "0%")
                DarkMetricCard(modifier = Modifier.weight(1f), label = "IS WEEKEND", value = if (detail.features?.is_weekend == true) "100%" else "0%")
            }
        }
    }
}

@Composable
fun DarkMetricCard(modifier: Modifier = Modifier, label: String, value: String) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(value, fontSize = 18.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
        }
    }
}

@Composable
fun DarkInfoCard(label: String, text: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(text, fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
fun SimilarEventsPanel(detail: EventDetailResponse) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("SIMILAR EVENT MEMORY", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Historical operational matches", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            Spacer(modifier = Modifier.height(16.dp))
            
            if (detail.similar_events.isNullOrEmpty()) {
                AutoTranslatedText("No similar events found.", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 14.sp)
            } else {
                Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    detail.similar_events.forEach { sim ->
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(16.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                        ) {
                            Column(modifier = Modifier.padding(16.dp)) {
                                Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                                    AutoTranslatedText(sim.event_id ?: "Unknown", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                                    val simScore = ((sim.similarity ?: 0.0) * 100).toInt()
                                    Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF4C1D95)), shape = RoundedCornerShape(8.dp)) {
                                        AutoTranslatedText("${simScore} SIMILARITY", modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp), fontSize = 10.sp, color = Color(0xFFDDD6FE), fontWeight = FontWeight.Bold)
                                    }
                                }
                                Spacer(modifier = Modifier.height(8.dp))
                                AutoTranslatedText(sim.event_cause_clean ?: "Unknown event", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                
                                Spacer(modifier = Modifier.height(16.dp))
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    DarkMetricCard(modifier = Modifier.weight(1f), label = "Priority", value = sim.priority ?: "N/A")
                                    DarkMetricCard(modifier = Modifier.weight(1f), label = "Road Closure", value = if (sim.requires_road_closure == true) "Required" else "Not required")
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun RecommendationPanel(detail: EventDetailResponse) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF0F9FF)),
        border = BorderStroke(1.dp, Color(0xFFBAE6FD))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("RECOMMENDATION", fontSize = 12.sp, color = Color(0xFF0369A1), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Generate event plan", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0C4A6E))
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Regenerate the stored plan for this event and immediately rehydrate the dossier panels below.", fontSize = 13.sp, color = Color(0xFF0369A1))
            
            Spacer(modifier = Modifier.height(16.dp))
            OutlinedTextField(
                value = "10",
                onValueChange = {},
                label = { AutoTranslatedText("OFFICERS") },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp)
            )
            Spacer(modifier = Modifier.height(12.dp))
            Button(
                onClick = { },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary, contentColor = MaterialTheme.colorScheme.onPrimary)
            ) {
                AutoTranslatedText("Generate")
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            AutoTranslatedText(detail.recommendation?.recommended_action_summary ?: detail.recommendation?.manpower?.note ?: "No specific recommendation generated.", fontSize = 14.sp, color = Color(0xFF0C4A6E))
        }
    }
}

@Composable
fun LiveEscalationTimeline(detail: EventDetailResponse) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("LIVE ESCALATION TIMELINE", fontSize = 12.sp, color = Color(0xFFD8B4FE), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Field updates and adaptive actions", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            Spacer(modifier = Modifier.height(16.dp))
            
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    AutoTranslatedText("CONTROL ROOM", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(8.dp))
                    AutoTranslatedText("Warning congestion update", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                    Spacer(modifier = Modifier.height(8.dp))
                    AutoTranslatedText("Field team reports crowd spillover and slow movement.", fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF065F46)), shape = RoundedCornerShape(16.dp)) {
                            AutoTranslatedText("STABLE", modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp), fontSize = 10.sp, color = Color(0xFFD1FAE5), fontWeight = FontWeight.Bold)
                        }
                        AutoTranslatedText("20 JUN 2026, 6:14 AM", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }
    }
}
@Composable
fun MetricItem(label: String, value: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            AutoTranslatedText(label.uppercase(), fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            AutoTranslatedText(value, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
        }
    }
}

@Composable
fun HotspotCard(hotspot: HotspotResponseItem) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Column {
                    AutoTranslatedText("CLUSTER", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                    AutoTranslatedText(hotspot.location_cluster_id, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                AutoTranslatedText("Events", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                AutoTranslatedText(hotspot.cluster_event_count.toString(), fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                AutoTranslatedText("Risk", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                AutoTranslatedText("", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurface)
            }
        }
    }
}

