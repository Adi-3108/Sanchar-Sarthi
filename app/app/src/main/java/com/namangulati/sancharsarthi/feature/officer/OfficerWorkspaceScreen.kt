package com.namangulati.sancharsarthi.feature.officer

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.namangulati.sancharsarthi.core.design.SkeletonScreen
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import com.namangulati.sancharsarthi.data.remote.OfficerAssignmentsResponse
import com.namangulati.sancharsarthi.data.remote.LiveUpdateRequestDto
import com.namangulati.sancharsarthi.design.LabelValue
import com.namangulati.sancharsarthi.design.PlatformSectionCard
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState
import kotlinx.coroutines.launch

import androidx.lifecycle.viewmodel.compose.viewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OfficerWorkspaceScreen(
    state: PlatformFoundationUiState,
    viewModel: OfficerWorkspaceViewModel = viewModel()
) {
    val assignments by viewModel.assignments.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val errorMessage by viewModel.errorMessage.collectAsState()

    var selectedEventId by remember { mutableStateOf<String?>(null) }
    
    // Live Escalation Form States
    var congestion by remember { mutableStateOf("Warning") }
    var fieldUpdate by remember { mutableStateOf("Crowd spillover near upstream junction") }
    var roadClosure by remember { mutableStateOf(false) }
    var officerShortage by remember { mutableStateOf(false) }
    var crowdIncrease by remember { mutableStateOf(true) }
    var rainWaterlogging by remember { mutableStateOf(false) }

    val isSubmitting by viewModel.isSubmitting.collectAsState()
    val submitResult by viewModel.submitResult.collectAsState()
    val submitError by viewModel.submitError.collectAsState()

    LaunchedEffect(assignments) {
        val firstEvent = assignments?.assigned_events?.firstOrNull()?.id
        if (selectedEventId == null && firstEvent != null) {
            selectedEventId = firstEvent
        }
    }

    if (isLoading) {
        SkeletonScreen(
            modifier = Modifier
                .fillMaxSize()
                .padding(20.dp),
            cards = 4
        )
        return
    }

    if (errorMessage != null) {
        Text("Error: $errorMessage", color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(20.dp))
        return
    }

    LazyColumn(
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            PlatformSectionCard(
                title = "Officer Profile",
                subtitle = "Station: ${assignments?.police_station ?: "N/A"}",
            ) {
                LabelValue(label = "Officer ID", value = assignments?.officer_id ?: "Unknown")
            }
        }
        
        item {
            Text("ASSIGNED EVENTS (SELECT AN EVENT)", style = MaterialTheme.typography.labelMedium, modifier = Modifier.padding(top = 8.dp))
        }

        items(assignments?.assigned_events ?: emptyList()) { event ->
            val isSelected = selectedEventId == event.id
            val border = if (isSelected) {
                BorderStroke(2.dp, MaterialTheme.colorScheme.primary)
            } else {
                BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
            }
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { selectedEventId = event.id },
                border = border,
                colors = CardDefaults.cardColors(
                    containerColor = if (isSelected) {
                        MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.15f)
                    } else {
                        MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)
                    }
                )
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Text(
                        text = event.id,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        text = "${event.event_cause_clean ?: "Unknown"} - ${event.corridor ?: event.zone ?: event.junction ?: "Unknown Location"}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                        LabelValue(label = "Priority", value = event.priority ?: "Normal")
                        LabelValue(label = "Status", value = event.status ?: "Active")
                    }
                }
            }
        }
        
        item {
            PlatformSectionCard(
                title = "Live Escalation",
                subtitle = "Submit field update",
            ) {
                if (selectedEventId == null) {
                    Text(
                        text = "Please select an assigned event from the list above.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.error
                    )
                } else {
                    var dropdownExpanded by remember { mutableStateOf(false) }
                    val congestionLevels = listOf("Info", "Watch", "Stable", "Warning", "Critical")
                    
                    // Congestion Dropdown
                    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Text(
                            text = "CONGESTION",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(bottom = 4.dp)
                        )
                        ExposedDropdownMenuBox(
                            expanded = dropdownExpanded,
                            onExpandedChange = { dropdownExpanded = !dropdownExpanded }
                        ) {
                            OutlinedTextField(
                                value = congestion,
                                onValueChange = {},
                                readOnly = true,
                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = dropdownExpanded) },
                                modifier = Modifier.menuAnchor().fillMaxWidth(),
                                shape = RoundedCornerShape(12.dp),
                                colors = OutlinedTextFieldDefaults.colors(
                                    unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                                    focusedContainerColor = MaterialTheme.colorScheme.surface
                                )
                            )
                            ExposedDropdownMenu(
                                expanded = dropdownExpanded,
                                onDismissRequest = { dropdownExpanded = false }
                            ) {
                                congestionLevels.forEach { level ->
                                    DropdownMenuItem(
                                        text = { Text(level) },
                                        onClick = {
                                            congestion = level
                                            dropdownExpanded = false
                                        }
                                    )
                                }
                            }
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    // Field Update Text
                    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Text(
                            text = "FIELD UPDATE",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(bottom = 4.dp)
                        )
                        OutlinedTextField(
                            value = fieldUpdate,
                            onValueChange = { fieldUpdate = it },
                            modifier = Modifier.fillMaxWidth(),
                            minLines = 3,
                            shape = RoundedCornerShape(12.dp)
                        )
                    }
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    // 2x2 Checkbox Grid
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Card(
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f)),
                                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
                                modifier = Modifier.weight(1f).clickable { roadClosure = !roadClosure }
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text("Road closure active", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                                    Checkbox(checked = roadClosure, onCheckedChange = { roadClosure = it })
                                }
                            }
                            Card(
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f)),
                                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
                                modifier = Modifier.weight(1f).clickable { officerShortage = !officerShortage }
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text("Officer shortage", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                                    Checkbox(checked = officerShortage, onCheckedChange = { officerShortage = it })
                                }
                            }
                        }
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Card(
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f)),
                                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
                                modifier = Modifier.weight(1f).clickable { crowdIncrease = !crowdIncrease }
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text("Crowd increasing", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                                    Checkbox(checked = crowdIncrease, onCheckedChange = { crowdIncrease = it })
                                }
                            }
                            Card(
                                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.2f)),
                                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
                                modifier = Modifier.weight(1f).clickable { rainWaterlogging = !rainWaterlogging }
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text("Rain or waterlogging", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                                    Checkbox(checked = rainWaterlogging, onCheckedChange = { rainWaterlogging = it })
                                }
                            }
                        }
                    }
                    
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Button(
                        onClick = {
                            val eventId = selectedEventId ?: return@Button
                            viewModel.submitLiveUpdate(
                                eventId = eventId,
                                request = LiveUpdateRequestDto(
                                    current_congestion_level = congestion,
                                    field_update = fieldUpdate,
                                    road_closure_active = roadClosure,
                                    officer_shortage = officerShortage,
                                    crowd_increase = crowdIncrease,
                                    rain_waterlogging = rainWaterlogging,
                                    new_nearby_incident = false
                                )
                            )
                        },
                        enabled = !isSubmitting,
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text(if (isSubmitting) "Submitting live update..." else "Submit live update")
                    }
                    
                    if (submitError != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Error: $submitError",
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodySmall
                        )
                    }
                    
                    if (submitResult != null) {
                        Spacer(modifier = Modifier.height(12.dp))
                        Card(
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.2f)),
                            border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.5f)),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Text(
                                    text = "Update Submitted Successfully",
                                    fontWeight = FontWeight.Bold,
                                    color = MaterialTheme.colorScheme.primary,
                                    style = MaterialTheme.typography.bodyMedium
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(
                                    text = "Current Impact Score: ${"%.1f".format(submitResult?.current_impact_score ?: 0.0)}",
                                    style = MaterialTheme.typography.bodySmall
                                )
                                Text(
                                    text = "Alert Level: ${submitResult?.alert_level ?: "N/A"}",
                                    style = MaterialTheme.typography.bodySmall
                                )
                                Text(
                                    text = "Adaptive Action: ${submitResult?.adaptive_action ?: "N/A"}",
                                    style = MaterialTheme.typography.bodySmall
                                )
                                Text(
                                    text = "Honesty Note: ${submitResult?.honesty_note ?: "N/A"}",
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

