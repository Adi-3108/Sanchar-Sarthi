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
import androidx.compose.material3.CircularProgressIndicator
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
import androidx.lifecycle.viewmodel.compose.viewModel
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText

@Composable
fun ControlRoomScreen(viewModel: AdminViewModel = viewModel()) {
    val uiState by viewModel.uiState.collectAsState()

    if (uiState.loading) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = androidx.compose.foundation.layout.Arrangement.Center
        ) {
            CircularProgressIndicator()
        }
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
            IncidentCard(
                incident = incident,
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
            IncidentCard(
                incident = incident,
                isEscalating = uiState.actionLoading,
                onActivate = { viewModel.transitionIncidentStatus(incident.id, "active") },
                onResolve = { viewModel.transitionIncidentStatus(incident.id, "resolved") },
                onReject = { viewModel.transitionIncidentStatus(incident.id, "rejected") },
                onEscalate = { viewModel.escalateIncident(incident.id) }
            )
        }

        // Spacer at bottom
        item {
            Spacer(modifier = Modifier.height(32.dp))
        }
    }
}

