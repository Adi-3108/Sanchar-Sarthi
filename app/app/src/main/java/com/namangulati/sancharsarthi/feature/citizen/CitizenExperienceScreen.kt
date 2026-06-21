package com.namangulati.sancharsarthi.feature.citizen

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.location.LocationManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MyLocation
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.namangulati.sancharsarthi.core.network.RetrofitClient
import com.namangulati.sancharsarthi.core.report.FoundationIncidentCreateRequest
import com.namangulati.sancharsarthi.core.report.IncidentResponse
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CitizenExperienceScreen(
    state: PlatformFoundationUiState,
    onReportSuccess: () -> Unit = {},
) {
    var title by remember { mutableStateOf("") }
    var incidentType by remember { mutableStateOf("Roadblock") }
    var severity by remember { mutableStateOf("Medium") }
    var locationName by remember { mutableStateOf("") }
    var locality by remember { mutableStateOf("") }
    var ward by remember { mutableStateOf("") }
    var latitude by remember { mutableStateOf("12.9716") }
    var longitude by remember { mutableStateOf("77.5946") }
    var descriptionLanguage by remember { mutableStateOf("Auto-detect") }
    var description by remember { mutableStateOf("") }
    
    var isSubmitting by remember { mutableStateOf(false) }
    var feedbackMsg by remember { mutableStateOf("") }
    
    var reportedIncidents by remember { mutableStateOf<List<IncidentResponse>>(emptyList()) }
    var isIncidentsLoading by remember { mutableStateOf(true) }

    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    fun fetchIncidents() {
        scope.launch {
            try {
                isIncidentsLoading = true
                val response = RetrofitClient.foundationApi.getIncidents()
                reportedIncidents = response.incidents.filter { it.status in listOf("reported", "pending_verification", "rejected") }
            } catch (e: Exception) {
                // Silently fail or show error
            } finally {
                isIncidentsLoading = false
            }
        }
    }

    LaunchedEffect(Unit) {
        fetchIncidents()
    }

    @SuppressLint("MissingPermission")
    fun fetchLocation() {
        try {
            val locationManager = context.getSystemService(Context.LOCATION_SERVICE) as LocationManager
            val location = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER) 
                ?: locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER)
            if (location != null) {
                latitude = location.latitude.toString()
                longitude = location.longitude.toString()
                feedbackMsg = "Location updated successfully!"
            } else {
                feedbackMsg = "Could not fetch location. Ensure GPS is on."
            }
        } catch (e: Exception) {
            feedbackMsg = "Error fetching location: ${e.message}"
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
        onResult = { isGranted ->
            if (isGranted) {
                fetchLocation()
            } else {
                feedbackMsg = "Location permission denied."
            }
        }
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(24.dp)
    ) {
        Text("Report incident", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = Color(0xFF1E293B))
        Spacer(modifier = Modifier.height(24.dp))

        Card(
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(containerColor = Color.White),
            elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(24.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = title,
                        onValueChange = { title = it },
                        label = { Text("TITLE", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                    )
                    OutlinedTextField(
                        value = severity,
                        onValueChange = { severity = it },
                        label = { Text("SEVERITY", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                    )
                }
                Spacer(modifier = Modifier.height(16.dp))

                Row(horizontalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = incidentType,
                        onValueChange = { incidentType = it },
                        label = { Text("INCIDENT TYPE", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                    )
                    OutlinedTextField(
                        value = locationName,
                        onValueChange = { locationName = it },
                        label = { Text("LOCATION", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                    )
                }
                Spacer(modifier = Modifier.height(16.dp))

                Row(horizontalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = locality,
                        onValueChange = { locality = it },
                        label = { Text("LOCALITY", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                    )
                    OutlinedTextField(
                        value = ward,
                        onValueChange = { ward = it },
                        label = { Text("WARD", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                    )
                }
                Spacer(modifier = Modifier.height(16.dp))

                Row(horizontalArrangement = Arrangement.spacedBy(16.dp), modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = latitude,
                        onValueChange = { latitude = it },
                        label = { Text("LATITUDE", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                    )
                    OutlinedTextField(
                        value = longitude,
                        onValueChange = { longitude = it },
                        label = { Text("LONGITUDE", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                        modifier = Modifier.weight(1f),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                    )
                }
                Spacer(modifier = Modifier.height(16.dp))

                OutlinedTextField(
                    value = descriptionLanguage,
                    onValueChange = { descriptionLanguage = it },
                    label = { Text("DESCRIPTION LANGUAGE", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                )
                Spacer(modifier = Modifier.height(16.dp))

                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("DESCRIPTION", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B)) },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 4,
                    maxLines = 6,
                    colors = OutlinedTextFieldDefaults.colors(unfocusedBorderColor = Color(0xFFE2E8F0))
                )
                Spacer(modifier = Modifier.height(24.dp))

                Row(horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    OutlinedButton(
                        onClick = {
                            val hasPermission = ContextCompat.checkSelfPermission(
                                context,
                                Manifest.permission.ACCESS_FINE_LOCATION
                            ) == PackageManager.PERMISSION_GRANTED
                            
                            if (hasPermission) {
                                fetchLocation()
                            } else {
                                permissionLauncher.launch(Manifest.permission.ACCESS_FINE_LOCATION)
                            }
                        },
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF1E293B)),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFE2E8F0))
                    ) {
                        Text("Use my location", fontWeight = FontWeight.Medium)
                    }

                    Button(
                        onClick = {
                            if (title.isBlank() || description.isBlank()) {
                                feedbackMsg = "Title and description are required."
                                return@Button
                            }
                            val lat = latitude.toDoubleOrNull() ?: 0.0
                            val lng = longitude.toDoubleOrNull() ?: 0.0
                            
                            isSubmitting = true
                            feedbackMsg = ""
                            
                            val request = FoundationIncidentCreateRequest(
                                incident_type = incidentType.lowercase(),
                                title = title,
                                description = description,
                                severity = severity.lowercase(),
                                location_name = locationName,
                                latitude = lat,
                                longitude = lng,
                                locality = locality.takeIf { it.isNotBlank() },
                                ward = ward.takeIf { it.isNotBlank() },
                                language = if (descriptionLanguage.lowercase().contains("auto")) "auto" else descriptionLanguage.lowercase()
                            )
                            
                            scope.launch {
                                try {
                                    RetrofitClient.reportApi.createIncidentReport(request)
                                    feedbackMsg = "Incident reported successfully!"
                                    title = ""
                                    description = ""
                                    onReportSuccess()
                                    fetchIncidents() // Refresh list
                                } catch (e: Exception) {
                                    feedbackMsg = "Failed to submit: ${e.message}"
                                } finally {
                                    isSubmitting = false
                                }
                            }
                        },
                        shape = RoundedCornerShape(8.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2563EB)),
                        enabled = !isSubmitting
                    ) {
                        Text(if (isSubmitting) "Submitting..." else "Submit", fontWeight = FontWeight.Medium)
                    }
                }
                if (feedbackMsg.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(feedbackMsg, color = if (feedbackMsg.contains("success", true) || feedbackMsg.contains("updated")) Color(0xFF10B981) else Color.Red, fontSize = 14.sp)
                }
            }
        }

        Spacer(modifier = Modifier.height(32.dp))

        // USER REPORTED INCIDENTS SECTION
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.Bottom
        ) {
            Text("User reported incidents", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color(0xFF1E293B))
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(100.dp))
                    .background(Color(0xFFF1F5F9))
                    .padding(horizontal = 12.dp, vertical = 4.dp)
            ) {
                Text(reportedIncidents.size.toString(), color = Color(0xFF475569), fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
            }
        }
        Spacer(modifier = Modifier.height(16.dp))

        if (isIncidentsLoading) {
            CircularProgressIndicator(modifier = Modifier.align(Alignment.CenterHorizontally))
        } else if (reportedIncidents.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(16.dp))
                    .border(1.dp, Color(0xFFE2E8F0), RoundedCornerShape(16.dp))
                    .padding(24.dp),
                contentAlignment = Alignment.Center
            ) {
                Text("No incidents here right now.", color = Color(0xFF64748B), fontSize = 14.sp)
            }
        } else {
            reportedIncidents.forEach { incident ->
                CitizenIncidentCard(
                    incident = incident,
                    onVote = { voteVal ->
                        scope.launch {
                            try {
                                RetrofitClient.foundationApi.voteIncident(incident.id, mapOf("vote_value" to voteVal))
                                fetchIncidents() // Refresh votes
                            } catch (e: Exception) {
                                // Handled
                            }
                        }
                    }
                )
                Spacer(modifier = Modifier.height(12.dp))
            }
        }
        Spacer(modifier = Modifier.height(24.dp))
    }
}

@Composable
fun CitizenIncidentCard(
    incident: IncidentResponse,
    onVote: (String) -> Unit
) {
    Card(
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFFF8FAFC)),
        border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFE2E8F0)),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(incident.title, fontWeight = FontWeight.Bold, color = Color(0xFF0F172A), fontSize = 16.sp)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(incident.location_name, color = Color(0xFF475569), fontSize = 13.sp)
                }
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(100.dp))
                        .background(Color.White)
                        .padding(horizontal = 10.dp, vertical = 4.dp)
                ) {
                    Text(
                        incident.severity.uppercase(),
                        color = Color(0xFF475569),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                OutlinedButton(
                    onClick = { onVote("true") },
                    shape = RoundedCornerShape(100.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF1E293B)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFE2E8F0)),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    Text("Vote true (${incident.true_vote_count})", fontSize = 13.sp)
                }
                OutlinedButton(
                    onClick = { onVote("false") },
                    shape = RoundedCornerShape(100.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFF1E293B)),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFE2E8F0)),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                ) {
                    Text("Vote false (${incident.false_vote_count})", fontSize = 13.sp)
                }
            }
        }
    }
}
