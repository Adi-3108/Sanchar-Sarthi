package com.namangulati.sancharsarthi.feature.simulation

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
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
import com.namangulati.sancharsarthi.core.design.SkeletonScreen
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState
import java.util.Locale
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

@Composable
fun SimulationScreen(
    state: PlatformFoundationUiState,
    viewModel: SimulationViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF8FAFC))
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
                        SimField(modifier = Modifier.weight(1f), label = "JUNCTION", value = uiState.junction) { viewModel.updateField("junction", it) }
                        SimField(modifier = Modifier.weight(1f), label = "START TIME", value = uiState.startDatetime) { viewModel.updateField("startDatetime", it) }
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        SimField(modifier = Modifier.weight(1f), label = "DURATION MIN", value = uiState.durationMinutes) { viewModel.updateField("durationMinutes", it) }
                        SimField(modifier = Modifier.weight(1f), label = "CROWD SIZE", value = uiState.crowdSize) { viewModel.updateField("crowdSize", it) }
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        SimField(modifier = Modifier.weight(1f), label = "AVAILABLE OFFICERS", value = uiState.availableOfficers) { viewModel.updateField("availableOfficers", it) }
                        SimField(modifier = Modifier.weight(1f), label = "WEATHER", value = uiState.weatherCondition) { viewModel.updateField("weatherCondition", it) }
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                    SimField(label = "VISIBILITY METERS", value = uiState.visibilityM) { viewModel.updateField("visibilityM", it) }
                    Spacer(modifier = Modifier.height(16.dp))
                    SimField(label = "DESCRIPTION", value = uiState.description, singleLine = false) { viewModel.updateField("description", it) }

                    Spacer(modifier = Modifier.height(24.dp))
                    Button(
                        onClick = { viewModel.runSimulation() },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary, contentColor = MaterialTheme.colorScheme.onPrimary),
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

        if (uiState.isLoading) {
            item {
                SkeletonScreen(cards = 3)
            }
        } else if (uiState.result != null) {
            val result = uiState.result!!
            
            // SIMULATION SUMMARY
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                ) {
                    Column(modifier = Modifier.padding(24.dp)) {
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            AutoTranslatedText("SIMULATION SUMMARY", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)), shape = RoundedCornerShape(8.dp)) {
                                val eventIdStr = result.event_dna?.event_id ?: result.recommendations?.event_id ?: "SIM-UNKNOWN"
                                AutoTranslatedText("Event ID: $eventIdStr", modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp), fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.Bold)
                            }
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            MetricItemOutline(modifier = Modifier.weight(1f), label = "PREDICTED PRIORITY", value = displayLabel(result.predicted_priority))
                            MetricItemOutline(modifier = Modifier.weight(1f), label = "IMPACT CATEGORY", value = displayLabel(result.impact_category))
                        }
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            MetricItemOutline(modifier = Modifier.weight(1f), label = "CLEARANCE", value = formatMinutes(result.estimated_clearance_minutes))
                            MetricItemOutline(modifier = Modifier.weight(1f), label = "ROAD CLOSURE", value = if (result.predicted_road_closure == true) "Yes" else "No")
                        }
                    }
                }
            }
            item { SimulationEventDnaPanel(eventDna = result.event_dna) }

            // ESTIMATED IMPACT
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
                ) {
                    Column(modifier = Modifier.padding(24.dp)) {
                        AutoTranslatedText("ESTIMATED IMPACT", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(8.dp))
                        AutoTranslatedText("Operational disruption estimate", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                            Column {
                                AutoTranslatedText("IMPACT SCORE", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                                AutoTranslatedText(result.estimated_impact_score?.toString() ?: "0.0", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                            }
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            MetricItemDark(modifier = Modifier.weight(1f), label = "PRIORITY CONF.", value = formatPercent(result.priority_confidence))
                            MetricItemDark(modifier = Modifier.weight(1f), label = "CLOSURE LIKELIHOOD", value = formatPercent(result.road_closure_probability))
                        }
                        Spacer(modifier = Modifier.height(12.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                            MetricItemDark(modifier = Modifier.weight(1f), label = "VEHICLE FACTOR", value = formatNumber(result.vehicle_impact_factor, 2))
                            MetricItemDark(modifier = Modifier.weight(1f), label = "RADIUS", value = "${formatNumber(result.impact_radius_km, 2)} km")
                        }
                        Spacer(modifier = Modifier.height(16.dp))
                        InfoTextBlock(label = "VEHICLE NOTE", text = result.vehicle_impact_note ?: "Vehicle impact factor was not available for this scenario.")
                    }
                }
            }
            item { CounterfactualPanel(result) }
            item { WeatherRiskPanel(result) }
            item { ManpowerPanel(result) }
            item { BarricadePanel(result) }
            item { DiversionPanel(result) }
            item { EmergencyCorridorPanel(result) }
            item { LogisticsPanel(result) }
            item { ActionConfidencePanel(result) }
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
                unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                focusedContainerColor = MaterialTheme.colorScheme.surface,
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
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            AutoTranslatedText(value, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
        }
    }
}

@Composable
fun MetricItemDark(modifier: Modifier = Modifier, label: String, value: String) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFFFFFFF)),
        border = BorderStroke(1.dp, Color(0xFFD8E3F0))
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = Color(0xFF64748B), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            AutoTranslatedText(value, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A))
        }
    }
}

@Composable
fun CounterfactualPanel(result: com.namangulati.sancharsarthi.core.network.SimulationResponse) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("COUNTERFACTUAL", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Baseline vs event-adjusted impact", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                AutoTranslatedText("ADDITIONAL DELTA", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                AutoTranslatedText(signedNumber(result.counterfactual?.additional_event_delta), fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color(0xFFEAB308))
            }
            Spacer(modifier = Modifier.height(16.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricItemDark(modifier = Modifier.weight(1f), label = "BASELINE RISK", value = formatNumber(result.counterfactual?.baseline_risk_score, 2))
                MetricItemDark(modifier = Modifier.weight(1f), label = "EVENT-ADJUSTED", value = formatNumber(result.counterfactual?.event_impact_score, 2))
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
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("LOGISTICS IMPACT", fontSize = 12.sp, color = Color(0xFFF472B6), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(impact.impact_level ?: "routine monitoring", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricItemDark(modifier = Modifier.weight(1f), label = "RISK WINDOW", value = formatMinutes(impact.delivery_risk_window_minutes?.toDouble()))
                MetricItemDark(modifier = Modifier.weight(1f), label = "AFFECTED RADIUS", value = "${formatNumber(impact.affected_radius_km, 2)} km")
            }
            Spacer(modifier = Modifier.height(16.dp))
            AutoTranslatedText(impact.dispatch_recommendation ?: "Keep routine dispatch active.", fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
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
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Color(0xFFD8E3F0))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("ACTION CONFIDENCE LEDGER", fontSize = 12.sp, color = Color(0xFF38BDF8), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Why this plan should be trusted carefully", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A))
            Spacer(modifier = Modifier.height(16.dp))
            ledger.forEach { item ->
                InfoTextBlock(
                    label = displayLabel(item.input),
                    text = "${item.note ?: "No note"} (${formatPercent(item.confidence)} confidence)"
                )
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
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("MANPOWER PLAN", fontSize = 12.sp, color = Color(0xFF38BDF8), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Officer deployment posture", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricItemDark(modifier = Modifier.weight(1f), label = "DEPLOYMENT STYLE", value = manpower.deployment_style ?: "N/A")
                MetricItemDark(modifier = Modifier.weight(1f), label = "RESERVE OFFICERS", value = manpower.reserve_officers?.toString() ?: "0")
            }
            Spacer(modifier = Modifier.height(16.dp))
            AutoTranslatedText(manpower.note ?: "Recommended manpower is dataset-backed guidance.", fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}


@Composable
fun SimulationEventDnaPanel(eventDna: com.namangulati.sancharsarthi.core.network.EventDnaResponse?) {
    if (eventDna == null) {
        InfoTextBlock("EVENT DNA", "Event DNA is not available yet.")
        return
    }
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Color(0xFFD8E3F0))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText("EVENT DNA", fontSize = 12.sp, color = Color(0xFF38BDF8), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("Operational fingerprint", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A))
            Spacer(modifier = Modifier.height(12.dp))
            AutoTranslatedText(cleanDnaSummary(eventDna.dna_summary), fontSize = 14.sp, color = Color(0xFF334155))
            Spacer(modifier = Modifier.height(16.dp))
            InfoTextBlock("TIME CONTEXT", eventDna.time_context ?: "n/a")
            InfoTextBlock("LOCATION CONTEXT", eventDna.location_context ?: "n/a")
            InfoTextBlock("CAUSE CONTEXT", eventDna.cause_context ?: "n/a")
            InfoTextBlock("HISTORICAL PATTERN", eventDna.historical_pattern ?: "n/a")
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText("RISK INDICATORS", fontSize = 12.sp, color = Color(0xFF64748B), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            val indicators = eventDna.risk_indicators_json?.entries?.take(8).orEmpty()
            if (indicators.isEmpty()) {
                AutoTranslatedText("No risk indicators were available.", fontSize = 14.sp, color = Color(0xFF64748B))
            } else {
                indicators.chunked(2).forEach { row ->
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                        row.forEach { (label, value) ->
                            MetricItemDark(modifier = Modifier.weight(1f), label = displayLabel(label), value = formatRiskValue(value))
                        }
                        if (row.size == 1) Spacer(modifier = Modifier.weight(1f))
                    }
                    Spacer(modifier = Modifier.height(12.dp))
                }
            }
        }
    }
}

@Composable
fun WeatherRiskPanel(result: com.namangulati.sancharsarthi.core.network.SimulationResponse) {
    val weather = result.weather_adjustment ?: result.recommendations?.weather_risk ?: return
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Color(0xFFD8E3F0))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f)) {
                    AutoTranslatedText("WEATHER RISK", fontSize = 12.sp, color = Color(0xFF2563EB), fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(8.dp))
                    AutoTranslatedText("Rain, visibility, and waterlogging posture", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A))
                }
                AutoTranslatedText("${formatNumber(weather.weather_factor, 2)}x", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A))
            }
            Spacer(modifier = Modifier.height(16.dp))
            MetricRows(listOf(
                "CONDITION" to displayLabel(weather.weather_condition),
                "RAIN MM" to formatNumber(weather.rain_mm, 1),
                "VISIBILITY" to "${formatNumber(weather.visibility_m, 0)} m",
                "WATERLOGGING" to displayLabel(weather.waterlogging_risk),
                "SOURCE" to weatherSource(weather),
                "LOW VISIBILITY" to if (weather.low_visibility == true) "Yes" else "No"
            ))
            InfoTextBlock("NOTE", weather.note ?: "Neutral weather modifier.")
        }
    }
}

@Composable
fun BarricadePanel(result: com.namangulati.sancharsarthi.core.network.SimulationResponse) {
    val barricades = result.recommendations?.barricades ?: return
    CardPanel("BARRICADE PLAN", displayLabel(barricades.barricade_level), Color(0xFFD97706)) {
        MetricRows(listOf(
            "ESTIMATED UNITS" to (barricades.estimated_units?.toString() ?: "0"),
            "COVERAGE RADIUS" to "${formatNumber(barricades.coverage_radius_km, 2)} km"
        ))
        ChipBlock("PLACEMENT PRIORITY", barricades.placement_priority.orEmpty())
        AutoTranslatedText(barricades.field_note ?: barricades.note ?: "Barricade guidance is an MVP operational template.", fontSize = 14.sp, color = Color(0xFF334155))
    }
}

@Composable
fun DiversionPanel(result: com.namangulati.sancharsarthi.core.network.SimulationResponse) {
    val diversions = result.recommendations?.diversions ?: return
    CardPanel("DIVERSION PLAN", displayLabel(diversions.strategy), Color(0xFF059669)) {
        AutoTranslatedText(diversions.note ?: "Diversion guidance is simplified MVP routing support.", fontSize = 14.sp, color = Color(0xFF334155))
        Spacer(modifier = Modifier.height(12.dp))
        MetricRows(listOf(
            "CORRIDOR TO PROTECT" to (diversions.corridor_to_protect ?: "n/a"),
            "DIVERSION SCOPE" to (diversions.diversion_scope ?: "n/a")
        ))
        ChipBlock("UPSTREAM FOCUS POINTS", diversions.upstream_focus_points.orEmpty())
        AutoTranslatedText(diversions.heavy_vehicle_advisory ?: diversions.field_note ?: "Keep advisory monitoring active.", fontSize = 14.sp, color = Color(0xFF334155))
    }
}

@Composable
fun EmergencyCorridorPanel(result: com.namangulati.sancharsarthi.core.network.SimulationResponse) {
    val corridor = result.recommendations?.emergency_corridor ?: return
    CardPanel("EMERGENCY CORRIDOR", displayLabel(corridor.priority), Color(0xFFE11D48)) {
        MetricRows(listOf(
            "PROTECTED CORRIDOR" to (corridor.protected_corridor ?: "n/a"),
            "ACTIVATION TRIGGER" to (corridor.activation_trigger ?: "n/a"),
            "LANE POLICY" to (corridor.lane_policy ?: "n/a")
        ))
        AutoTranslatedText(corridor.authentication_note ?: "Corridor advisory only.", fontSize = 14.sp, color = Color(0xFF334155))
    }
}

@Composable
fun CardPanel(eyebrow: String, title: String, accent: Color, content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = Color.White),
        border = BorderStroke(1.dp, Color(0xFFD8E3F0))
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText(eyebrow, fontSize = 12.sp, color = accent, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(title, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A))
            Spacer(modifier = Modifier.height(16.dp))
            content()
        }
    }
}

@Composable
fun InfoTextBlock(label: String, text: String) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF8FAFC)),
        border = BorderStroke(1.dp, Color(0xFFE2E8F0))
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            AutoTranslatedText(label, fontSize = 10.sp, color = Color(0xFF64748B), fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(8.dp))
            AutoTranslatedText(text, fontSize = 14.sp, color = Color(0xFF334155))
        }
    }
}

@Composable
fun MetricRows(metrics: List<Pair<String, String>>) {
    metrics.chunked(2).forEach { row ->
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
            row.forEach { (label, value) -> MetricItemDark(modifier = Modifier.weight(1f), label = label, value = value) }
            if (row.size == 1) Spacer(modifier = Modifier.weight(1f))
        }
        Spacer(modifier = Modifier.height(12.dp))
    }
}

@Composable
fun ChipBlock(label: String, values: List<String>) {
    if (values.isEmpty()) return
    AutoTranslatedText(label, fontSize = 10.sp, color = Color(0xFF64748B), fontWeight = FontWeight.Bold)
    Spacer(modifier = Modifier.height(8.dp))
    values.take(6).chunked(2).forEach { row ->
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
            row.forEach { value ->
                Card(
                    modifier = Modifier.weight(1f),
                    shape = RoundedCornerShape(50),
                    colors = CardDefaults.cardColors(containerColor = Color.White),
                    border = BorderStroke(1.dp, Color(0xFFD8E3F0))
                ) {
                    AutoTranslatedText(displayLabel(value), modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp), fontSize = 10.sp, color = Color(0xFF334155))
                }
            }
            if (row.size == 1) Spacer(modifier = Modifier.weight(1f))
        }
        Spacer(modifier = Modifier.height(8.dp))
    }
}

fun formatNumber(value: Double?, digits: Int = 1): String {
    if (value == null || value.isNaN()) return "n/a"
    return String.format(Locale.US, "%.${digits}f", value)
}

fun formatMinutes(value: Double?): String = value?.let { "${it.toInt()} min" } ?: "n/a"

fun formatPercent(value: Double?): String {
    if (value == null || value.isNaN()) return "n/a"
    return "${(value * 100).toInt()}%"
}

fun signedNumber(value: Double?): String {
    if (value == null || value.isNaN()) return "n/a"
    return if (value >= 0) "+${formatNumber(value, 2)}" else formatNumber(value, 2)
}

fun displayLabel(value: String?): String {
    if (value.isNullOrBlank()) return "n/a"
    return value.replace('_', ' ')
        .split(' ')
        .filter { it.isNotBlank() }
        .joinToString(" ") { word ->
            word.lowercase(Locale.US).replaceFirstChar { first -> if (first.isLowerCase()) first.titlecase(Locale.US) else first.toString() }
        }
}

fun formatRiskValue(value: JsonElement): String {
    return try {
        val primitive = value.jsonPrimitive
        val number = primitive.doubleOrNull
        if (number != null) {
            if (number in 0.0..1.0) formatPercent(number) else formatNumber(number, 2)
        } else {
            displayLabel(primitive.contentOrNull)
        }
    } catch (_: Exception) {
        "n/a"
    }
}

fun weatherSource(weather: com.namangulati.sancharsarthi.core.network.SimulationWeatherAdjustment): String {
    val source = displayLabel(weather.source)
    val provider = displayLabel(weather.provider).takeIf { it != "n/a" }
    return if (provider != null) "$source via $provider" else source
}

fun cleanDnaSummary(summary: String?): String {
    if (summary.isNullOrBlank()) return "No Event DNA summary was available."
    return summary
        .replace(Regex("\\s*Similar-event memory found [^.]*\\.", RegexOption.IGNORE_CASE), "")
        .replace(Regex("\\s+"), " ")
        .trim()
}
