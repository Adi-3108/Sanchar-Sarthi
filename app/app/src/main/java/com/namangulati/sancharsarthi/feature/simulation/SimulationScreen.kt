package com.namangulati.sancharsarthi.feature.simulation

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
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState
import com.namangulati.sancharsarthi.feature.explorer.EventDnaPanel
import kotlin.math.roundToInt

@Composable
fun SimulationScreen(
    state: PlatformFoundationUiState,
    viewModel: SimulationViewModel = viewModel()
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
                    AutoTranslatedText("INPUTS", fontSize = 12.sp, color = Color(0xFF0284C7), fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(16.dp))

                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        SimField(modifier = Modifier.weight(1f), label = "EVENT TYPE", value = uiState.eventType) { viewModel.updateField("eventType", it) }
                        SimField(modifier = Modifier.weight(1f), label = "EVENT CAUSE", value = uiState.eventCause) { viewModel.updateField("eventCause", it) }
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        SimField(modifier = Modifier.weight(1f), label = "LATITUDE", value = uiState.latitude) { viewModel.updateField("latitude", it) }
                        SimField(modifier = Modifier.weight(1f), label = "LONGITUDE", value = uiState.longitude) { viewModel.updateField("longitude", it) }
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        SimField(modifier = Modifier.weight(1f), label = "CORRIDOR", value = uiState.corridor) { viewModel.updateField("corridor", it) }
                        SimField(modifier = Modifier.weight(1f), label = "POLICE STATION", value = uiState.policeStation) { viewModel.updateField("policeStation", it) }
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        SimField(modifier = Modifier.weight(1f), label = "DURATION MIN", value = uiState.durationMinutes) { viewModel.updateField("durationMinutes", it) }
                        SimField(modifier = Modifier.weight(1f), label = "CROWD SIZE", value = uiState.crowdSize) { viewModel.updateField("crowdSize", it) }
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                    SimField(label = "DESCRIPTION", value = uiState.description, singleLine = false) { viewModel.updateField("description", it) }

                    Spacer(modifier = Modifier.height(24.dp))
                    Button(
                        onClick = { viewModel.runSimulation() },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7), contentColor = Color.White),
                        enabled = !uiState.isLoading
                    ) {
                        AutoTranslatedText(if (uiState.isLoading) "Simulating..." else "Run Simulation")
                    }
                    
                    if (uiState.error != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        AutoTranslatedText(uiState.error!!, color = Color.Red, fontSize = 12.sp)
                    }
                }
            }
        }

        if (uiState.result != null) {
            val result = uiState.result!!
            
            // SIMULATION SUMMARY
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = Color.White),
                    border = BorderStroke(1.dp, Color(0xFFE2E8F0))
                ) {
                    Column(modifier = Modifier.padding(24.dp)) {
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            AutoTranslatedText("SIMULATION SUMMARY", fontSize = 12.sp, color = Color(0xFF64748B), fontWeight = FontWeight.Bold)
                            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)), shape = RoundedCornerShape(8.dp)) {
                                val eventIdStr = result.event_dna?.event_id ?: result.recommendations?.event_id ?: "SIM-UNKNOWN"
                                AutoTranslatedText("Event ID: $eventIdStr", modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp), fontSize = 10.sp, color = Color.White, fontWeight = FontWeight.Bold)
                            }
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            MetricItemOutline(modifier = Modifier.weight(1f), label = "PREDICTED PRIORITY", value = result.predicted_priority ?: "N/A")
                            MetricItemOutline(modifier = Modifier.weight(1f), label = "IMPACT CATEGORY", value = result.impact_category ?: "N/A")
                        }
                    }
                }
            }

            // EVENT DNA
            if (result.event_dna != null) {
                item { EventDnaPanel(detail = com.namangulati.sancharsarthi.core.network.EventDetailResponse(
                    event = com.namangulati.sancharsarthi.core.network.EventRecordResponse(id = result.event_dna?.event_id ?: "SIM"),
                    event_dna = result.event_dna,
                    features = null
                )) }
            }

            // ESTIMATED IMPACT
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B))
                ) {
                    Column(modifier = Modifier.padding(24.dp)) {
                        AutoTranslatedText("ESTIMATED IMPACT", fontSize = 12.sp, color = Color(0xFF94A3B8), fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(8.dp))
                        AutoTranslatedText("Operational disruption estimate", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            Column {
                                AutoTranslatedText("IMPACT SCORE", fontSize = 10.sp, color = Color(0xFF94A3B8), fontWeight = FontWeight.Bold)
                                AutoTranslatedText(result.estimated_impact_score?.toString() ?: "0.0", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color.White)
                            }
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            MetricItemDark(modifier = Modifier.weight(1f), label = "PRIORITY CONF.", value = "%")
                            MetricItemDark(modifier = Modifier.weight(1f), label = "CLOSURE LIKELIHOOD", value = "%")
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun SimField(modifier: Modifier = Modifier, label: String, value: String, singleLine: Boolean = true, onChange: (String) -> Unit) {
    Column(modifier = modifier) {
        AutoTranslatedText(label, fontSize = 10.sp, color = Color(0xFF0284C7), fontWeight = FontWeight.Bold)
        Spacer(modifier = Modifier.height(4.dp))
        OutlinedTextField(
            value = value,
            onValueChange = onChange,
            singleLine = singleLine,
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = OutlinedTextFieldDefaults.colors(
                unfocusedContainerColor = Color.White,
                focusedContainerColor = Color.White,
                unfocusedBorderColor = Color(0xFFBAE6FD),
                focusedBorderColor = Color(0xFF0284C7)
            )
        )
    }
}

@Composable
fun MetricItemOutline(modifier: Modifier = Modifier, label: String, value: String) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Color(0xFFE2E8F0))
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = Color(0xFF64748B), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            AutoTranslatedText(value, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A))
        }
    }
}

@Composable
fun MetricItemDark(modifier: Modifier = Modifier, label: String, value: String) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = Color(0xFF94A3B8), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            AutoTranslatedText(value, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Color.White)
        }
    }
}

@Composable
fun CounterfactualPanel(result: com.namangulati.sancharsarthi.core.network.SimulationResponse) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("COUNTERFACTUAL", fontSize = 12.sp, color = Color(0xFF94A3B8), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Baseline vs event-adjusted impact", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color.White)
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                AutoTranslatedText("ADDITIONAL DELTA", fontSize = 10.sp, color = Color(0xFF94A3B8), fontWeight = FontWeight.Bold)
                AutoTranslatedText("+", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color(0xFFFDE047))
            }
            Spacer(modifier = Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricItemDark(modifier = Modifier.weight(1f), label = "BASELINE RISK", value = result.counterfactual?.baseline_risk_score?.toString() ?: "N/A")
                MetricItemDark(modifier = Modifier.weight(1f), label = "ADJUSTED SCORE", value = result.counterfactual?.event_impact_score?.toString() ?: "N/A")
            }
        }
    }
}

@Composable
fun LogisticsPanel(result: com.namangulati.sancharsarthi.core.network.SimulationResponse) {
    val impact = result.recommendations?.flipkart_logistics_impact ?: return
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("LOGISTICS IMPACT", fontSize = 12.sp, color = Color(0xFFF472B6), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(impact.impact_level ?: "routine monitoring", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color.White)
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricItemDark(modifier = Modifier.weight(1f), label = "RISK WINDOW", value = " min")
                MetricItemDark(modifier = Modifier.weight(1f), label = "AFFECTED RADIUS", value = " km")
            }
            Spacer(modifier = Modifier.height(16.dp))
            AutoTranslatedText(impact.dispatch_recommendation ?: "Keep routine dispatch active.", fontSize = 14.sp, color = Color(0xFFCBD5E1))
        }
    }
}

@Composable
fun ActionConfidencePanel(result: com.namangulati.sancharsarthi.core.network.SimulationResponse) {
    val ledger = result.recommendations?.action_confidence_ledger ?: return
    if (ledger.isEmpty()) return
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("ACTION CONFIDENCE LEDGER", fontSize = 12.sp, color = Color(0xFF94A3B8), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Why this plan should be trusted carefully", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color.White)
            Spacer(modifier = Modifier.height(16.dp))
            
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                ledger.forEach { item ->
                    Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)), shape = RoundedCornerShape(12.dp), modifier = Modifier.fillMaxWidth()) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            AutoTranslatedText(item.input ?: "Unknown Input", fontSize = 10.sp, color = Color(0xFF94A3B8), fontWeight = FontWeight.Bold)
                            Spacer(modifier = Modifier.height(4.dp))
                            AutoTranslatedText(item.note ?: "No note", fontSize = 14.sp, color = Color(0xFFCBD5E1))
                            Spacer(modifier = Modifier.height(8.dp))
                            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF1E3A8A)), shape = RoundedCornerShape(8.dp)) {
                                AutoTranslatedText(" CONFIDENCE", modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp), fontSize = 10.sp, color = Color(0xFFDBEAFE), fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun ManpowerPanel(result: com.namangulati.sancharsarthi.core.network.SimulationResponse) {
    val manpower = result.recommendations?.manpower ?: return
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("MANPOWER PLAN", fontSize = 12.sp, color = Color(0xFF38BDF8), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Officer deployment posture", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color.White)
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricItemDark(modifier = Modifier.weight(1f), label = "DEPLOYMENT STYLE", value = manpower.deployment_style ?: "N/A")
                MetricItemDark(modifier = Modifier.weight(1f), label = "RESERVE OFFICERS", value = manpower.reserve_officers?.toString() ?: "0")
            }
            Spacer(modifier = Modifier.height(16.dp))
            AutoTranslatedText(manpower.note ?: "Recommended manpower is dataset-backed guidance.", fontSize = 14.sp, color = Color(0xFFCBD5E1))
        }
    }
}
