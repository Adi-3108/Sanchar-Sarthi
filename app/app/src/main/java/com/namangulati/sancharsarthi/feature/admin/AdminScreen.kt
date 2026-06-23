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
import androidx.compose.foundation.clickable
import com.namangulati.sancharsarthi.core.design.SkeletonScreen
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText

import kotlin.math.roundToInt

@OptIn(ExperimentalMaterial3Api::class, ExperimentalLayoutApi::class)
@Composable
fun AdminScreen(
    viewModel: AdminViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    var selectedIncidentId by remember { mutableStateOf<String?>(null) }
    var selectedStationName by remember { mutableStateOf<String?>(null) }

    if (uiState.loading && uiState.overview == null) {
        SkeletonScreen(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            cards = 6
        )
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
                Field("Password", uiState.officerForm.password, true) { viewModel.updateOfficerForm("password", it) }
                Field("Officer ID", uiState.officerForm.officer_id) { viewModel.updateOfficerForm("officer_id", it) }
                Field("Display name", uiState.officerForm.display_name) { viewModel.updateOfficerForm("display_name", it) }
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
            val isSelected = selectedIncidentId == incident.id || (selectedStationName != null && incident.assigned_station_name == selectedStationName)
            IncidentCard(
                incident = incident,
                isSelected = isSelected,
                onClick = { 
                    if (selectedIncidentId == incident.id) {
                        selectedIncidentId = null
                        selectedStationName = null
                    } else {
                        selectedIncidentId = incident.id
                        selectedStationName = incident.assigned_station_name
                    }
                },
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
            val isSelected = selectedIncidentId == incident.id || (selectedStationName != null && incident.assigned_station_name == selectedStationName)
            IncidentCard(
                incident = incident,
                isSelected = isSelected,
                onClick = { 
                    if (selectedIncidentId == incident.id) {
                        selectedIncidentId = null
                        selectedStationName = null
                    } else {
                        selectedIncidentId = incident.id
                        selectedStationName = incident.assigned_station_name
                    }
                },
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
                    val isSelected = selectedStationName == station.name || (selectedIncidentId != null && uiState.overview?.incidents?.find { it.id == selectedIncidentId }?.assigned_station_name == station.name)
                    
                    val borderColor = if (isSelected) Color(0xFF3B82F6) else MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f)
                    val bgColor = if (isSelected) Color(0xFFEFF6FF) else MaterialTheme.colorScheme.surface
                    val borderWidth = if (isSelected) 2.dp else 1.dp
                    
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 6.dp)
                            .clip(RoundedCornerShape(16.dp))
                            .clickable {
                                if (selectedStationName == station.name) {
                                    selectedStationName = null
                                    selectedIncidentId = null
                                } else {
                                    selectedStationName = station.name
                                    selectedIncidentId = null
                                }
                            },
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = bgColor),
                        border = androidx.compose.foundation.BorderStroke(borderWidth, borderColor),
                        elevation = CardDefaults.cardElevation(defaultElevation = if (isSelected) 4.dp else 0.dp)
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column(modifier = Modifier.weight(1f).padding(end = 12.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Box(
                                        modifier = Modifier
                                            .size(8.dp)
                                            .clip(androidx.compose.foundation.shape.CircleShape)
                                            .background(if (station.active) Color(0xFF10B981) else Color(0xFF94A3B8))
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    AutoTranslatedText(
                                        text = station.name,
                                        fontWeight = FontWeight.ExtraBold,
                                        color = if (isSelected) Color(0xFF1E3A8A) else MaterialTheme.colorScheme.onSurface,
                                        fontSize = 16.sp
                                    )
                                }
                                Spacer(modifier = Modifier.height(4.dp))
                                AutoTranslatedText(
                                    text = "${station.locality} - Code: ${station.station_code}",
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    fontSize = 13.sp,
                                    fontWeight = FontWeight.Medium
                                )
                                Spacer(modifier = Modifier.height(2.dp))
                                AutoTranslatedText(
                                    text = "Contact: ${station.contact_number ?: "Unavailable"}",
                                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                                    fontSize = 12.sp
                                )
                            }
                            OutlinedButton(
                                onClick = { viewModel.toggleStation(station.id, station.active) },
                                shape = RoundedCornerShape(12.dp),
                                colors = ButtonDefaults.outlinedButtonColors(
                                    contentColor = if (isSelected) Color(0xFF1D4ED8) else Color(0xFF334155)
                                ),
                                border = androidx.compose.foundation.BorderStroke(1.dp, if (isSelected) Color(0xFF93C5FD) else MaterialTheme.colorScheme.outlineVariant)
                            ) {
                                AutoTranslatedText(if (station.active) "Disable" else "Enable", fontWeight = FontWeight.Bold)
                            }
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
    isSelected: Boolean = false,
    onClick: (() -> Unit)? = null,
    isEscalating: Boolean,
    onActivate: () -> Unit,
    onResolve: () -> Unit,
    onReject: () -> Unit,
    onEscalate: () -> Unit
) {
    val borderColor = if (isSelected) Color(0xFF3B82F6) else MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f)
    val bgColor = if (isSelected) Color(0xFFEFF6FF) else MaterialTheme.colorScheme.surface
    val borderWidth = if (isSelected) 2.dp else 1.dp

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = bgColor),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isSelected) 8.dp else 6.dp),
        border = androidx.compose.foundation.BorderStroke(borderWidth, borderColor)
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            // Header: Title and Severity Badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column(modifier = Modifier.weight(1f).padding(end = 12.dp)) {
                    AutoTranslatedText(
                        text = incident.title,
                        fontWeight = FontWeight.ExtraBold,
                        color = MaterialTheme.colorScheme.onSurface,
                        style = MaterialTheme.typography.titleMedium
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(4.dp))
                                .background(MaterialTheme.colorScheme.primaryContainer)
                                .padding(horizontal = 6.dp, vertical = 2.dp)
                        ) {
                            AutoTranslatedText(
                                text = incident.status.replace("_", " ").uppercase(),
                                color = MaterialTheme.colorScheme.onPrimaryContainer,
                                fontSize = 9.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        AutoTranslatedText(
                            text = incident.location_name,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
                
                val severityColor = when (incident.severity.lowercase()) {
                    "critical" -> Color(0xFFDC2626)
                    "high" -> Color(0xFFEA580C)
                    "medium" -> Color(0xFFD97706)
                    else -> Color(0xFF16A34A)
                }
                Box(
                    modifier = Modifier
                        .background(severityColor.copy(alpha = 0.15f), RoundedCornerShape(12.dp))
                        .border(1.dp, severityColor.copy(alpha = 0.3f), RoundedCornerShape(12.dp))
                        .padding(horizontal = 12.dp, vertical = 6.dp),
                    contentAlignment = Alignment.Center
                ) {
                    AutoTranslatedText(
                        text = incident.severity.uppercase(),
                        color = severityColor,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.ExtraBold
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // AI Impact Box
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(Color(0xFFF8FAFC), RoundedCornerShape(12.dp))
                    .border(1.dp, Color(0xFFE2E8F0), RoundedCornerShape(12.dp))
                    .padding(12.dp)
            ) {
                Column {
                    AutoTranslatedText("SYSTEM INSIGHT", fontSize = 10.sp, color = Color(0xFF64748B), fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(4.dp))
                    AutoTranslatedText(
                        text = incident.route_impact_summary ?: "No major route impact detected.",
                        color = Color(0xFF334155),
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Metadata Grid
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                // Column 1
                Column(modifier = Modifier.weight(1f)) {
                    AutoTranslatedText("TIME REPORTED", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    Text(incident.created_at.take(16).replace("T", " "), color = MaterialTheme.colorScheme.onSurface, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    Spacer(modifier = Modifier.height(12.dp))
                    AutoTranslatedText("EVENT ID", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    Text(incident.id.take(10), color = MaterialTheme.colorScheme.onSurface, fontSize = 13.sp, fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace, fontWeight = FontWeight.SemiBold)
                }
                // Column 2
                Column(modifier = Modifier.weight(1f)) {
                    AutoTranslatedText("ASSIGNED STATION", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    AutoTranslatedText(incident.assigned_station_name ?: "Unassigned", color = MaterialTheme.colorScheme.onSurface, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
                    Spacer(modifier = Modifier.height(12.dp))
                    AutoTranslatedText("VERIFICATION CONFIDENCE", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                    val conf = incident.confidence_score
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("${(conf * 100).roundToInt()}%", color = if (conf > 0.7) Color(0xFF16A34A) else Color(0xFFD97706), fontSize = 14.sp, fontWeight = FontWeight.ExtraBold)
                        Spacer(modifier = Modifier.width(6.dp))
                        AutoTranslatedText("(${incident.true_vote_count} votes)", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 11.sp)
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f))
            Spacer(modifier = Modifier.height(16.dp))

            // Action Buttons
            @OptIn(ExperimentalLayoutApi::class)
            FlowRow(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                if (incident.status == "pending_verification" || incident.status == "reported") {
                    OutlinedButton(
                        onClick = onReject,
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFEF4444)),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFECACA))
                    ) {
                        AutoTranslatedText("Reject", fontWeight = FontWeight.Bold)
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    Button(
                        onClick = onActivate,
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981), contentColor = Color.White)
                    ) {
                        AutoTranslatedText("Activate Incident", fontWeight = FontWeight.Bold)
                    }
                } else if (incident.status == "active" || incident.status == "escalated") {
                    OutlinedButton(
                        onClick = onResolve,
                        shape = RoundedCornerShape(12.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF10B981)),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFA7F3D0))
                    ) {
                        AutoTranslatedText("Mark Resolved", fontWeight = FontWeight.Bold)
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    if (incident.status == "active") {
                        Button(
                            onClick = onEscalate,
                            enabled = !isEscalating,
                            shape = RoundedCornerShape(12.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF3B82F6), contentColor = Color.White)
                        ) {
                            AutoTranslatedText(if (isEscalating) "Escalating..." else "Escalate to Event", fontWeight = FontWeight.Bold)
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

