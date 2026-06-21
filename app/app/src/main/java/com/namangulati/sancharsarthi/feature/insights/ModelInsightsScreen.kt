package com.namangulati.sancharsarthi.feature.insights

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.namangulati.sancharsarthi.core.network.HealthResponse
import com.namangulati.sancharsarthi.core.network.ModelRunResponse
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText
import com.namangulati.sancharsarthi.design.PlatformSectionCard
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState

@Composable
fun ModelInsightsScreen(
    appState: PlatformFoundationUiState,
    viewModel: ModelInsightsViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    LazyColumn(
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            HeaderSection(uiState.modelRuns)
        }

        if (uiState.isLoading) {
            item {
                CircularProgressIndicator(modifier = Modifier.padding(16.dp))
            }
        } else if (uiState.error != null) {
            item {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFFEF2F2)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFECACA)),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Text(
                        text = "Error: ${uiState.error}",
                        color = Color(0xFFDC2626),
                        modifier = Modifier.padding(16.dp)
                    )
                }
            }
        } else {
            item {
                SystemHealthSection(uiState.health)
            }
            item {
                InterpretationGuideSection()
            }
            item {
                val priorityRun = uiState.modelRuns.firstOrNull { it.model_name == "priority_model" }
                ModelDetailSection(
                    title = "Priority model",
                    description = "Predicted High or Low urgency from dataset-backed event fields.",
                    status = uiState.health?.models?.priority ?: "not_loaded",
                    run = priorityRun
                )
            }
            item {
                val closureRun = uiState.modelRuns.firstOrNull { it.model_name == "road_closure_model" }
                ModelDetailSection(
                    title = "Road-closure likelihood",
                    description = "Rule-history score stays primary even when optional ML support exists.",
                    status = uiState.health?.models?.road_closure ?: "not_loaded",
                    run = closureRun
                )
            }
            item {
                val timeRun = uiState.modelRuns.firstOrNull { it.model_name == "resolution_time_model" }
                ModelDetailSection(
                    title = "Resolution-time estimator",
                    description = "Estimated clearance time, not a guaranteed operational commitment.",
                    status = uiState.health?.models?.resolution_time ?: "not_loaded",
                    run = timeRun
                )
            }
        }
    }
}

@Composable
fun HeaderSection(modelRuns: List<ModelRunResponse>) {
    val latestRun = modelRuns.maxByOrNull { it.created_at }
    PlatformSectionCard(
        title = "Dataset-honest prediction diagnostics.",
        subtitle = "MODEL INSIGHTS"
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            AutoTranslatedText(
                text = "This view tracks which prediction artifacts exist, what the latest recorded training run says, and when Sanchar Sarthi is still operating on explainable rule fallbacks.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.height(16.dp))
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(16.dp))
                    .background(Color(0xFFF0FDF4))
                    .border(1.dp, Color(0xFFBBF7D0), RoundedCornerShape(16.dp))
                    .padding(16.dp)
            ) {
                Column {
                    AutoTranslatedText("Latest recorded run", style = MaterialTheme.typography.labelSmall, color = Color(0xFF16A34A), fontWeight = FontWeight.SemiBold)
                    Spacer(modifier = Modifier.height(4.dp))
                    AutoTranslatedText(latestRun?.created_at ?: "No runs yet", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface, fontSize = 18.sp)
                }
            }
        }
    }
}

@Composable
fun SystemHealthSection(health: HealthResponse?) {
    PlatformSectionCard(
        title = "Backend and artifact state",
        subtitle = "SYSTEM HEALTH"
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            if (health != null) {
                InfoRow("Status", health.status)
                InfoRow("Database", health.database)
                InfoRow("Priority artifact", statusLabel(health.models.priority))
                InfoRow("Road-closure artifact", statusLabel(health.models.road_closure))
                InfoRow("Resolution-time artifact", statusLabel(health.models.resolution_time))
                InfoRow("Firebase", health.auth.firebase)
            } else {
                Text("Health data unavailable", color = Color.Gray)
            }
        }
    }
}

@Composable
fun InterpretationGuideSection() {
    PlatformSectionCard(
        title = "How to read this page",
        subtitle = "INTERPRETATION GUIDE"
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            BulletText("• 'Artifact not loaded' means no saved model file exists yet, so rules remain active.")
            BulletText("• 'Artifact present, dependencies missing' means a model file exists but local ML packages are not installed.")
            BulletText("• Road-closure likelihood stays rule-history first even when optional ML support is available.")
            BulletText("• Resolution-time metrics only use rows that pass the reliable timestamp filter.")
            BulletText("• Priority and road-closure metrics still rely on dataset-wide historical aggregates, so read them as prototype diagnostics, not leakage-free production validation.")
        }
    }
}

@Composable
fun BulletText(text: String) {
    AutoTranslatedText(text = text, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
}

@Composable
fun ModelDetailSection(title: String, description: String, status: String, run: ModelRunResponse?) {
    PlatformSectionCard(
        title = title,
        subtitle = "MODEL DETAILS"
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            AutoTranslatedText(text = description, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(modifier = Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                StatusBadge(statusLabel(status), statusToneColor(status), statusToneBg(status))
                val metricsStatus = run?.metrics_json?.status ?: "not_recorded"
                StatusBadge("Metrics: ${metricsStatus.replace("_", " ")}", Color(0xFF64748B), Color(0xFFF1F5F9))
            }
            Spacer(modifier = Modifier.height(16.dp))
            
            // Run Details
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .background(MaterialTheme.colorScheme.background)
                    .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(12.dp))
                    .padding(12.dp)
            ) {
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    InfoRow("Model version", run?.model_version ?: "Not recorded")
                    InfoRow("Training rows", run?.training_rows?.toString() ?: "Not recorded")
                    InfoRow("Test rows", run?.test_rows?.toString() ?: "Not recorded")
                    InfoRow("Artifact available", if (run == null) "Not recorded" else if (run.artifact_available) "Yes" else "No")
                    InfoRow("Recorded at", run?.created_at ?: "Not recorded")
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
            
            // Metrics
            if (run != null) {
                val metrics = run.metrics_json
                if (title == "Priority model") {
                    MetricGrid(
                        listOf(
                            "F1" to formatNum(metrics.f1),
                            "Recall High" to formatNum(metrics.recall_high),
                            "Positive rows" to (metrics.positive_rows?.toString() ?: "N/A"),
                            "Positive rate" to formatNum(metrics.positive_rate)
                        )
                    )
                } else if (title == "Road-closure likelihood") {
                    MetricGrid(
                        listOf(
                            "PR-AUC" to formatNum(metrics.pr_auc),
                            "Recall TRUE" to formatNum(metrics.recall_true),
                            "Positive rows" to (metrics.positive_rows?.toString() ?: "N/A"),
                            "Positive rate" to formatNum(metrics.positive_rate)
                        )
                    )
                } else {
                    MetricGrid(
                        listOf(
                            "MAE minutes" to formatNum(metrics.mae_minutes),
                            "R2 score" to formatNum(metrics.r2_score),
                            "Qualifying rows" to (metrics.qualifying_rows?.toString() ?: "N/A"),
                            "Data filter" to (metrics.data_filter ?: "N/A")
                        )
                    )
                }
            } else {
                AutoTranslatedText("No training metadata has been recorded yet.", style = MaterialTheme.typography.bodySmall, color = Color.Gray)
            }
        }
    }
}

@Composable
fun MetricGrid(items: List<Pair<String, String>>) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        for (i in items.indices step 2) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                MetricBox(items[i].first, items[i].second, Modifier.weight(1f))
                if (i + 1 < items.size) {
                    MetricBox(items[i + 1].first, items[i + 1].second, Modifier.weight(1f))
                } else {
                    Spacer(modifier = Modifier.weight(1f))
                }
            }
        }
    }
}

@Composable
fun MetricBox(label: String, value: String, modifier: Modifier = Modifier) {
    Box(
        modifier = modifier
            .clip(RoundedCornerShape(8.dp))
            .background(MaterialTheme.colorScheme.surfaceVariant)
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(8.dp))
            .padding(8.dp)
    ) {
        Column {
            Text(text = label.uppercase(), fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            Text(text = value, fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
fun StatusBadge(text: String, color: Color, bgColor: Color) {
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(100.dp))
            .background(bgColor)
            .border(1.dp, color.copy(alpha = 0.5f), RoundedCornerShape(100.dp))
            .padding(horizontal = 8.dp, vertical = 2.dp)
    ) {
        Text(text = text.uppercase(), color = color, fontSize = 10.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun InfoRow(label: String, value: String) {
    Row(modifier = Modifier.fillMaxWidth()) {
        Text(text = "$label: ", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Medium)
        Text(text = value, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurface, fontWeight = FontWeight.SemiBold)
    }
}

fun statusLabel(status: String): String {
    return when (status) {
        "loaded" -> "Loaded"
        "dependency_missing" -> "Artifact present, dependencies missing"
        else -> "Artifact not loaded"
    }
}

fun statusToneColor(status: String): Color {
    return when (status) {
        "loaded" -> Color(0xFF16A34A)
        "dependency_missing" -> Color(0xFFD97706)
        else -> Color(0xFF64748B)
    }
}

fun statusToneBg(status: String): Color {
    return when (status) {
        "loaded" -> Color(0xFFF0FDF4)
        "dependency_missing" -> Color(0xFFFFFBEB)
        else -> Color(0xFFF8FAFC)
    }
}

fun formatNum(value: Double?): String {
    if (value == null || value.isNaN()) return "N/A"
    return String.format("%.2f", value)
}

