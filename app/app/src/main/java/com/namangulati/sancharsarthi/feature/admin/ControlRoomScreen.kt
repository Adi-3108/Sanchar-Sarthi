package com.namangulati.sancharsarthi.feature.admin

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.clickable
import androidx.compose.ui.draw.clip
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.ButtonDefaults
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.runtime.remember
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.foundation.BorderStroke
import com.namangulati.sancharsarthi.core.design.SkeletonScreen
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText

@Composable
fun ControlRoomScreen(viewModel: AdminViewModel = viewModel()) {
    val uiState by viewModel.uiState.collectAsState()

    var selectedIncidentId by remember { mutableStateOf<String?>(null) }
    var selectedStationName by remember { mutableStateOf<String?>(null) }

    if (uiState.loading) {
        SkeletonScreen(
            modifier = Modifier
                .fillMaxSize()
                .padding(20.dp),
            cards = 5
        )
        return
    }

    if (uiState.error != null) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = androidx.compose.foundation.layout.Arrangement.Center
        ) {
            Text("Error loading data: ${uiState.error}", color = MaterialTheme.colorScheme.error)
        }
        return
    }

    LazyColumn(
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = androidx.compose.foundation.layout.Arrangement.spacedBy(16.dp)
    ) {
        // Active incidents
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

        // User reported incidents
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

        // Station mapping
        item {
            Column {
                Spacer(modifier = Modifier.height(16.dp))
                AutoTranslatedText("Station mapping", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(4.dp))
                AutoTranslatedText("Units handling active incidents", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }

        val activeStations = uiState.overview?.stations?.filter { it.active } ?: emptyList()
        if (activeStations.isEmpty()) {
            item {
                Text("No active stations.", color = Color.Gray)
            }
        }
        items(activeStations) { station ->
            val isSelected = selectedStationName == station.name || (selectedIncidentId != null && uiState.overview?.incidents?.find { it.id == selectedIncidentId }?.assigned_station_name == station.name)
            
            val borderColor = if (isSelected) Color(0xFF3B82F6) else MaterialTheme.colorScheme.outlineVariant.copy(alpha = 0.5f)
            val bgColor = if (isSelected) Color(0xFFEFF6FF) else MaterialTheme.colorScheme.surface
            val borderWidth = if (isSelected) 2.dp else 1.dp
            
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp)
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
                border = BorderStroke(borderWidth, borderColor),
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
                }
            }
        }

        // Spacer at bottom
        item {
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

