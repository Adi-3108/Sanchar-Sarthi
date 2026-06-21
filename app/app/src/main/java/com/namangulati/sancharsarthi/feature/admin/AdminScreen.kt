package com.namangulati.sancharsarthi.feature.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText

import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun AdminScreen(
    viewModel: AdminViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    if (uiState.loading && uiState.overview == null) {
        Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator()
        }
        return
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        item {
            AutoTranslatedText(
                text = "Admin Portal",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(8.dp))
            if (uiState.error != null) {
                Card(
                    modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF1F2)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFECDD3))
                ) {
                    Text(
                        text = uiState.error!!,
                        color = Color(0xFF9F1239),
                        modifier = Modifier.padding(16.dp)
                    )
                }
            }
            if (uiState.successMessage != null) {
                Card(
                    modifier = Modifier.fillMaxWidth().padding(bottom = 16.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFECFDF5)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFA7F3D0))
                ) {
                    Text(
                        text = uiState.successMessage!!,
                        color = Color(0xFF065F46),
                        modifier = Modifier.padding(16.dp)
                    )
                }
            }
        }

        // 1. Officer access
        item {
            AdminSectionCard("Officer access", "Create registered police officer") {
                Field("Officer email", uiState.officerForm.email) { viewModel.updateOfficerForm("email", it) }
                Field("Password", uiState.officerForm.password ?: "", true) { viewModel.updateOfficerForm("password", it) }
                Field("Officer ID", uiState.officerForm.badge_number ?: "") { viewModel.updateOfficerForm("badge_number", it) }
                Field("Display name", uiState.officerForm.display_name ?: "") { viewModel.updateOfficerForm("display_name", it) }
                Field("Rank", uiState.officerForm.rank ?: "") { viewModel.updateOfficerForm("rank", it) }
                
                // Station Dropdown
                var expanded by remember { mutableStateOf(false) }
                Column(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                    AutoTranslatedText(
                        text = "Police station",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(bottom = 4.dp)
                    )
                    ExposedDropdownMenuBox(
                        expanded = expanded,
                        onExpandedChange = { expanded = !expanded },
                    ) {
                        OutlinedTextField(
                            value = uiState.officerForm.police_station ?: "",
                            onValueChange = {},
                            readOnly = true,
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
                            modifier = Modifier.menuAnchor().fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                                focusedContainerColor = MaterialTheme.colorScheme.surface,
                                unfocusedBorderColor = Color(0xFFCBD5E1),
                                focusedBorderColor = Color(0xFF60A5FA)
                            )
                        )
                        ExposedDropdownMenu(
                            expanded = expanded,
                            onDismissRequest = { expanded = false }
                        ) {
                            uiState.overview?.stations?.forEach { station ->
                                DropdownMenuItem(
                                    text = { AutoTranslatedText(station.name) },
                                    onClick = {
                                        viewModel.updateOfficerForm("police_station", station.name)
                                        expanded = false
                                    }
                                )
                            }
                        }
                    }
                }

                Field("Assigned corridors", uiState.officerForm.assigned_corridors.joinToString(", ")) { viewModel.updateOfficerForm("assigned_corridors", it) }
                Field("Assigned zones", uiState.officerForm.assigned_zones.joinToString(", ")) { viewModel.updateOfficerForm("assigned_zones", it) }

                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = { viewModel.createOfficer() },
                    enabled = !uiState.actionLoading,
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    AutoTranslatedText("Create officer")
                }
            }
        }

        // 2. Command Access
        item {
            AdminSectionCard("Command Access", "Create control room user") {
                Field("Email", uiState.controlRoomForm.email) { viewModel.updateControlRoomForm("email", it) }
                Field("Password", uiState.controlRoomForm.password ?: "", true) { viewModel.updateControlRoomForm("password", it) }
                Field("Display Name", uiState.controlRoomForm.display_name ?: "") { viewModel.updateControlRoomForm("display_name", it) }

                Spacer(modifier = Modifier.height(16.dp))
                Button(
                    onClick = { viewModel.createControlRoomUser() },
                    enabled = !uiState.actionLoading,
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    AutoTranslatedText("Create control room user")
                }
            }
        }

        // 3. Status distribution
        item {
            AdminSectionCard("Status distribution", "Lifecycle mix") {
                uiState.overview?.summary?.status_counts?.forEach { (status, count) ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(MaterialTheme.colorScheme.background)
                            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(12.dp))
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        AutoTranslatedText(status, color = Color(0xFF334155), fontWeight = FontWeight.Medium)
                        Text(text = count.toString(), fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                    }
                }
            }
        }

        // 4. Active incidents
        item {
            Column {
                AutoTranslatedText("Incident management", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(4.dp))
                AutoTranslatedText("Active incidents", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            }
        }
        
        val activeIncidents = uiState.overview?.incidents?.filter { it.status == "active" || it.status == "escalated" || it.status == "resolved" }?.take(8) ?: emptyList()
        items(activeIncidents) { incident ->
            IncidentCard(
                incident = incident,
                isEscalating = uiState.actionLoading,
                onActivate = { viewModel.transitionIncidentStatus(incident.id, "active") },
                onResolve = { viewModel.transitionIncidentStatus(incident.id, "resolved") },
                onReject = { viewModel.transitionIncidentStatus(incident.id, "rejected") },
                onEscalate = { viewModel.escalateIncident(incident.id) }
            )
        }

        // 4b. User reported incidents
        item {
            Column {
                Spacer(modifier = Modifier.height(16.dp))
                AutoTranslatedText("User reported incidents", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            }
        }

        val userReportedIncidents = uiState.overview?.incidents?.filter { it.status == "pending_verification" || it.status == "reported" }?.take(8) ?: emptyList()
        if (userReportedIncidents.isEmpty()) {
            item {
                Text("No user reported incidents currently.", color = Color.Gray)
            }
        }
        items(userReportedIncidents) { incident ->
            IncidentCard(
                incident = incident,
                isEscalating = uiState.actionLoading,
                onActivate = { viewModel.transitionIncidentStatus(incident.id, "active") },
                onResolve = { viewModel.transitionIncidentStatus(incident.id, "resolved") },
                onReject = { viewModel.transitionIncidentStatus(incident.id, "rejected") },
                onEscalate = { viewModel.escalateIncident(incident.id) }
            )
        }

        // 5. Stations
        item {
            AdminSectionCard("Stations", "Station controls") {
                uiState.overview?.stations?.forEach { station ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(MaterialTheme.colorScheme.background)
                            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(12.dp))
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                            AutoTranslatedText(station.name, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                            AutoTranslatedText("${station.locality} · ${station.station_code}", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp)
                            AutoTranslatedText(station.contact_number ?: "Contact unavailable", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp)
                        }
                        OutlinedButton(
                            onClick = { viewModel.toggleStation(station.id, station.active) },
                            shape = RoundedCornerShape(12.dp),
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF334155))
                        ) {
                            AutoTranslatedText(if (station.active) "Disable" else "Enable")
                        }
                    }
                }
            }
        }

        // 6. Users
        item {
            AdminSectionCard("Users", "User access") {
                uiState.overview?.users?.take(8)?.forEach { user ->
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp)
                            .clip(RoundedCornerShape(12.dp))
                            .background(MaterialTheme.colorScheme.background)
                            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(12.dp))
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                            AutoTranslatedText(user.display_name ?: user.auth_provider_uid ?: "Unknown", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                            AutoTranslatedText(user.role, color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp)
                        }
                        OutlinedButton(
                            onClick = { viewModel.toggleUser(user.id, user.is_active) },
                            shape = RoundedCornerShape(12.dp),
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF334155))
                        ) {
                            AutoTranslatedText(if (user.is_active) "Disable" else "Enable")
                        }
                    }
                }
            }
        }
        
        // Spacer at bottom
        item {
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

@Composable
fun Field(label: String, value: String, isPassword: Boolean = false, onChange: (String) -> Unit) {
    Column(modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
        AutoTranslatedText(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            fontWeight = FontWeight.Bold,
            modifier = Modifier.padding(bottom = 4.dp)
        )
        OutlinedTextField(
            value = value,
            onValueChange = onChange,
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            visualTransformation = if (isPassword) PasswordVisualTransformation() else androidx.compose.ui.text.input.VisualTransformation.None,
            colors = OutlinedTextFieldDefaults.colors(
                unfocusedContainerColor = MaterialTheme.colorScheme.surface,
                focusedContainerColor = MaterialTheme.colorScheme.surface,
                unfocusedBorderColor = Color(0xFFCBD5E1),
                focusedBorderColor = Color(0xFF60A5FA)
            )
        )
    }
}

@Composable
fun IncidentCard(
    incident: com.namangulati.sancharsarthi.core.report.IncidentResponse,
    isEscalating: Boolean,
    onActivate: () -> Unit,
    onResolve: () -> Unit,
    onReject: () -> Unit,
    onEscalate: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f).padding(end = 8.dp)) {
                    AutoTranslatedText(incident.title, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                    AutoTranslatedText("${incident.location_name} · ${incident.status.replace("_", " ").capitalize()}", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 14.sp)
                    Spacer(modifier = Modifier.height(4.dp))
                    AutoTranslatedText(incident.route_impact_summary ?: "Route impact under review.", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 14.sp)
                }
                Box(
                    modifier = Modifier
                        .background(Color.White, RoundedCornerShape(12.dp))
                        .padding(horizontal = 12.dp, vertical = 4.dp)
                        .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(12.dp))
                ) {
                    AutoTranslatedText(incident.severity, color = Color(0xFF334155), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Row {
                        Text("EVENT ID: ", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                        Text(incident.id.take(12), color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp, fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace)
                    }
                    Text("TIME", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 10.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 4.dp))
                    Text(incident.created_at.take(16).replace("T", " "), color = MaterialTheme.colorScheme.onSurface, fontSize = 13.sp)
                }
                Column {
                    Text("STATUS", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 10.sp, fontWeight = FontWeight.Bold)
                    Text(incident.status.replace("_", " ").capitalize(), color = MaterialTheme.colorScheme.onSurface, fontSize = 13.sp)
                    Text("STATION", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 10.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 4.dp))
                    Text(incident.assigned_station_name ?: "-", color = MaterialTheme.colorScheme.onSurface, fontSize = 13.sp)
                }
            }

            Spacer(modifier = Modifier.height(8.dp))
            Text("CONFIDENCE", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            val conf = incident.confidence_score
            Text("${(conf * 100).roundToInt()}%", color = MaterialTheme.colorScheme.onSurface, fontSize = 13.sp)

            Spacer(modifier = Modifier.height(16.dp))
            
            // Voting buttons (always disabled in Control Room per user request)
            @OptIn(ExperimentalLayoutApi::class)
            FlowRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = { },
                    enabled = false,
                    shape = RoundedCornerShape(100.dp),
                    colors = ButtonDefaults.outlinedButtonColors(disabledContentColor = Color(0xFF94A3B8)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                ) {
                    Text("Vote true (${incident.true_vote_count})", fontSize = 12.sp)
                }
                OutlinedButton(
                    onClick = { },
                    enabled = false,
                    shape = RoundedCornerShape(100.dp),
                    colors = ButtonDefaults.outlinedButtonColors(disabledContentColor = Color(0xFF94A3B8)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                ) {
                    Text("Vote false (${incident.false_vote_count})", fontSize = 12.sp)
                }
                Button(
                    onClick = { },
                    enabled = false,
                    shape = RoundedCornerShape(100.dp),
                    colors = ButtonDefaults.buttonColors(disabledContainerColor = Color(0xFFEFF6FF), disabledContentColor = Color(0xFF60A5FA))
                ) {
                    Text("View alternate routes", fontSize = 12.sp)
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            @OptIn(ExperimentalLayoutApi::class)
            FlowRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                if (incident.status == "pending_verification" || incident.status == "reported") {
                    OutlinedButton(onClick = onReject, shape = RoundedCornerShape(100.dp), colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF334155))) {
                        AutoTranslatedText("Reject")
                    }
                    OutlinedButton(onClick = onActivate, shape = RoundedCornerShape(100.dp), colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF334155))) {
                        AutoTranslatedText("Activate")
                    }
                } else if (incident.status == "active" || incident.status == "escalated") {
                    OutlinedButton(onClick = onResolve, shape = RoundedCornerShape(100.dp), colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF334155))) {
                        AutoTranslatedText("Resolve")
                    }
                    if (incident.status == "active") {
                        Button(
                            onClick = onEscalate,
                            enabled = !isEscalating,
                            shape = RoundedCornerShape(100.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEFF6FF), contentColor = Color(0xFF1D4ED8))
                        ) {
                            AutoTranslatedText(if (isEscalating) "Escalating…" else "Escalate to Event")
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun AdminSectionCard(
    subtitle: String,
    title: String,
    content: @Composable () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp)
        ) {
            AutoTranslatedText(
                text = subtitle.uppercase(),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(4.dp))
            AutoTranslatedText(
                text = title,
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(20.dp))
            content()
        }
    }
}

