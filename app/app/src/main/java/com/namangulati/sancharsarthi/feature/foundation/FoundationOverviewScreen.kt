package com.namangulati.sancharsarthi.feature.foundation

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberCoroutineScope
import android.widget.Toast
import androidx.compose.ui.platform.LocalContext
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.clickable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.ui.unit.sp
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.ui.viewinterop.AndroidView
import com.namangulati.sancharsarthi.core.design.SkeletonScreen
import com.namangulati.sancharsarthi.core.report.HotspotResponse
import com.namangulati.sancharsarthi.core.report.IncidentResponse
import com.namangulati.sancharsarthi.core.report.StationResponse
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText
import com.namangulati.sancharsarthi.design.PlatformSectionCard
import com.namangulati.sancharsarthi.feature.splash.LaunchBanner

@Composable
fun FoundationOverviewScreen(
    state: PlatformFoundationUiState,
    onNavigateToModelInsights: () -> Unit = {},
    onNavigateToSubmitReport: () -> Unit = {},
    onNavigateToMapIntelligence: () -> Unit = {},
    viewModel: FoundationOverviewViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()

    var selectedIncidentId by remember { mutableStateOf<String?>(null) }
    var selectedStationName by remember { mutableStateOf<String?>(null) }

    LazyColumn(
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            CommandCenterHeader(
                onNavigateToModelInsights = onNavigateToModelInsights,
                onNavigateToSubmitReport = onNavigateToSubmitReport,
                onNavigateToMapIntelligence = onNavigateToMapIntelligence
            )
        }

        if (uiState.isLoading) {
            item {
                SkeletonScreen(cards = 4)
            }
        } else if (uiState.error != null) {
            item {
                Text(
                    text = "Error loading incidents: ${uiState.error}",
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.padding(16.dp)
                )
            }
        } else {
            item {
                SystemStateGrid(metrics = uiState.metrics)
            }
            item {
                MapPanel(
                    activeIncidents = uiState.activeIncidents,
                    reportedIncidents = uiState.reportedIncidents,
                    hotspots = uiState.hotspots,
                    routes = uiState.routes
                )
            }
            item {
                HotspotPanel(hotspots = uiState.hotspots)
            }
            item {
                StationPanel(
                    stations = uiState.stations,
                    incidents = uiState.activeIncidents + uiState.reportedIncidents,
                    selectedStationName = selectedStationName,
                    selectedIncidentId = selectedIncidentId,
                    onStationClick = { stationName ->
                        if (selectedStationName == stationName) {
                            selectedStationName = null
                            selectedIncidentId = null
                        } else {
                            selectedStationName = stationName
                            selectedIncidentId = null
                        }
                    }
                )
            }
            item {
                IncidentListSection(
                    title = "Active incidents",
                    incidents = uiState.activeIncidents,
                    selectedIncidentId = selectedIncidentId,
                    selectedStationName = selectedStationName,
                    onIncidentClick = { incident ->
                        if (selectedIncidentId == incident.id) {
                            selectedIncidentId = null
                            selectedStationName = null
                        } else {
                            selectedIncidentId = incident.id
                            selectedStationName = incident.assigned_station_name
                        }
                    }
                )
            }
            item {
                IncidentListSection(
                    title = "User reported incidents",
                    incidents = uiState.reportedIncidents,
                    selectedIncidentId = selectedIncidentId,
                    selectedStationName = selectedStationName,
                    onIncidentClick = { incident ->
                        if (selectedIncidentId == incident.id) {
                            selectedIncidentId = null
                            selectedStationName = null
                        } else {
                            selectedIncidentId = incident.id
                            selectedStationName = incident.assigned_station_name
                        }
                    }
                )
            }
        }
    }
}
@Composable
fun MapPanel(
    activeIncidents: List<IncidentResponse>,
    reportedIncidents: List<IncidentResponse>,
    hotspots: List<HotspotResponse> = emptyList(),
    routes: List<com.namangulati.sancharsarthi.core.network.ActiveRoute> = emptyList()
) {
    PlatformSectionCard(
        title = "Bengaluru incident map",
        subtitle = "Live geographic overview (MapmyIndia)"
    ) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(300.dp)
                .clip(RoundedCornerShape(16.dp))
                .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(16.dp))
        ) {
            AndroidView(
                factory = { context ->
                    android.webkit.WebView(context).apply {
                        layoutParams = android.view.ViewGroup.LayoutParams(
                            android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                            android.view.ViewGroup.LayoutParams.MATCH_PARENT
                        )
                        webViewClient = android.webkit.WebViewClient()
                        webChromeClient = android.webkit.WebChromeClient()
                        settings.javaScriptEnabled = true
                        settings.domStorageEnabled = true
                        // Allow loading mixed content (file:// loading https:// CDN resources)
                        if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
                            settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                        }
                        
                        // Add JS Interface
                        addJavascriptInterface(object {
                            @android.webkit.JavascriptInterface
                            fun onMapLoaded() {
                                // Once map is loaded, trigger update
                                post {
                                    evaluateJavascript("javascript:window.isMapReady = true;", null)
                                }
                            }
                        }, "AndroidInterface")

                        val htmlData = context.assets.open("mappls_map.html").bufferedReader().use { it.readText() }
                        val htmlWithKey = htmlData.replace("YOUR_API_KEY_HERE", com.namangulati.sancharsarthi.BuildConfig.MAPS_API_KEY)
                        loadDataWithBaseURL("file:///android_asset/", htmlWithKey, "text/html", "UTF-8", null)
                    }
                },
                update = { webView ->
                    // Re-inject markers whenever incidents change
                    val markers = mutableListOf<Map<String, Any>>()
                    activeIncidents.forEach {
                        markers.add(mapOf("lat" to it.latitude, "lng" to it.longitude, "title" to it.title, "severity" to it.severity, "type" to "active"))
                    }
                    reportedIncidents.forEach {
                        markers.add(mapOf("lat" to it.latitude, "lng" to it.longitude, "title" to it.title, "severity" to "Reported", "type" to "reported"))
                    }
                    val markersJson = org.json.JSONArray(markers).toString()

                    val hotspotsData = mutableListOf<Map<String, Any>>()
                    hotspots.forEach {
                        hotspotsData.add(mapOf(
                            "lat" to it.latitude,
                            "lng" to it.longitude,
                            "label" to it.label,
                            "severity" to it.severity,
                            "count" to it.incident_count
                        ))
                    }
                    val hotspotsJson = org.json.JSONArray(hotspotsData).toString()

                    val routesData = mutableListOf<Map<String, Any>>()
                    routes.forEach {
                        routesData.add(mapOf(
                            "incidentId" to it.incidentId,
                            "polyline" to it.polyline
                        ))
                    }
                    val routesJson = org.json.JSONArray(routesData).toString()

                    webView.evaluateJavascript("""
                        (function() {
                            var markersData = $markersJson;
                            var hotspotsData = $hotspotsJson;
                            var routesData = $routesJson;
                            
                            var markersStr = JSON.stringify(markersData);
                            var hotspotsStr = JSON.stringify(hotspotsData);
                            var routesStr = JSON.stringify(routesData);
                            
                            if (typeof loadIncidents === 'function') {
                                loadIncidents(markersStr);
                            } else {
                                window.pendingMarkers = markersStr;
                            }
                            if (typeof loadHotspots === 'function') {
                                loadHotspots(hotspotsStr);
                            } else {
                                window.pendingHotspots = hotspotsStr;
                            }
                            if (typeof loadRoutes === 'function') {
                                loadRoutes(routesStr);
                            } else {
                                window.pendingRoutes = routesStr;
                            }
                        })();
                    """.trimIndent(), null)
                },
                modifier = Modifier.matchParentSize()
            )

            Column(
                modifier = Modifier
                    .padding(12.dp)
                    .clip(RoundedCornerShape(12.dp))
                    .background(MaterialTheme.colorScheme.surface.copy(alpha = 0.9f))
                    .padding(8.dp)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(8.dp).clip(CircleShape).background(Color(0xFF2563EB)))
                    Spacer(modifier = Modifier.width(6.dp))
                    AutoTranslatedText(text = "Active", style = MaterialTheme.typography.labelSmall)
                }
                Spacer(modifier = Modifier.height(4.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(modifier = Modifier.size(8.dp).clip(CircleShape).background(Color(0xFFF59E0B)))
                    Spacer(modifier = Modifier.width(6.dp))
                    AutoTranslatedText(text = "Reports", style = MaterialTheme.typography.labelSmall)
                }
            }
        }
    }
}


@Composable
fun HotspotPanel(hotspots: List<HotspotResponse>) {
    PlatformSectionCard(
        title = "Hotspots",
        subtitle = "Incident clusters"
    ) {
        if (hotspots.isEmpty()) {
            AutoTranslatedText(
                text = "No hotspots are active right now.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 8.dp)
            )
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                hotspots.sortedByDescending { it.incident_count }.forEach { hotspot ->
                    val severityColor = when (hotspot.severity.lowercase()) {
                        "critical" -> Color(0xFFBE123C)
                        "high" -> Color(0xFFD97706)
                        "medium" -> Color(0xFF0284C7)
                        else -> Color(0xFF16A34A)
                    }
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant),
                        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.Top
                            ) {
                                Column(modifier = Modifier.weight(1f).padding(end = 12.dp)) {
                                    AutoTranslatedText(
                                        text = hotspot.label,
                                        style = MaterialTheme.typography.titleMedium,
                                        fontWeight = FontWeight.Bold,
                                        color = MaterialTheme.colorScheme.onSurface
                                    )
                                    AutoTranslatedText(
                                        text = hotspot.hotspot_id,
                                        style = MaterialTheme.typography.bodySmall,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(100.dp))
                                        .background(severityColor.copy(alpha = 0.12f))
                                        .border(1.dp, severityColor.copy(alpha = 0.35f), RoundedCornerShape(100.dp))
                                        .padding(horizontal = 10.dp, vertical = 4.dp)
                                ) {
                                    AutoTranslatedText(
                                        text = hotspot.severity.uppercase(),
                                        color = severityColor,
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }

                            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                HotspotMetric(
                                    label = "Incidents",
                                    value = hotspot.incident_count.toString(),
                                    modifier = Modifier.weight(1f)
                                )
                                HotspotMetric(
                                    label = "Linked IDs",
                                    value = hotspot.active_incident_ids.size.toString(),
                                    modifier = Modifier.weight(1f)
                                )
                            }

                            if (hotspot.active_incident_ids.isNotEmpty()) {
                                AutoTranslatedText(
                                    text = hotspot.active_incident_ids.take(4).joinToString(", "),
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun HotspotMetric(label: String, value: String, modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .clip(RoundedCornerShape(12.dp))
            .background(MaterialTheme.colorScheme.background)
            .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(12.dp))
            .padding(12.dp)
    ) {
        AutoTranslatedText(
            text = label.uppercase(),
            style = MaterialTheme.typography.labelSmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(4.dp))
        AutoTranslatedText(
            text = value,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface,
            fontWeight = FontWeight.Bold
        )
    }
}
@Composable
fun StationPanel(
    stations: List<StationResponse>,
    incidents: List<IncidentResponse>,
    selectedStationName: String?,
    selectedIncidentId: String?,
    onStationClick: (String) -> Unit
) {
    val activeStations = stations.filter { station -> incidents.any { it.assigned_station_name == station.name } }
    
    PlatformSectionCard(
        title = "Station mapping",
        subtitle = "Units handling active incidents"
    ) {
        if (activeStations.isEmpty()) {
            AutoTranslatedText(
                text = "No stations have active incidents right now.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 8.dp)
            )
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                activeStations.forEach { station ->
                    val linked = incidents.filter { it.assigned_station_name == station.name }
                    val isSelected = selectedStationName == station.name || (selectedIncidentId != null && incidents.find { it.id == selectedIncidentId }?.assigned_station_name == station.name)
                    val borderColor = if (isSelected) Color(0xFF3B82F6) else MaterialTheme.colorScheme.outlineVariant
                    val bgColor = if (isSelected) Color(0xFFEFF6FF) else MaterialTheme.colorScheme.background
                    val borderWidth = if (isSelected) 2.dp else 1.dp

                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .clip(RoundedCornerShape(12.dp))
                            .background(bgColor)
                            .border(borderWidth, borderColor, RoundedCornerShape(12.dp))
                            .clickable { onStationClick(station.name) }
                            .padding(12.dp)
                    ) {
                        AutoTranslatedText(text = station.name, fontWeight = FontWeight.Bold, style = MaterialTheme.typography.bodyMedium)
                        AutoTranslatedText(text = "${station.locality} - ${station.station_code}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        AutoTranslatedText(text = "Contact: ${station.contact_number ?: "Not available"}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            linked.take(3).forEach { incident ->
                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(16.dp))
                                        .background(MaterialTheme.colorScheme.surface)
                                        .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(16.dp))
                                        .padding(horizontal = 8.dp, vertical = 4.dp)
                                ) {
                                    AutoTranslatedText(text = incident.title.take(15) + if(incident.title.length > 15) "..." else "", style = MaterialTheme.typography.labelSmall, color = Color(0xFF334155))
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
fun IncidentListSection(
    title: String,
    incidents: List<IncidentResponse>,
    selectedIncidentId: String?,
    selectedStationName: String?,
    onIncidentClick: (IncidentResponse) -> Unit
) {
    PlatformSectionCard(
        title = title,
        subtitle = "Live data from server"
    ) {
        if (incidents.isEmpty()) {
            AutoTranslatedText(
                text = "No incidents here right now.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 8.dp)
            )
        } else {
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                incidents.forEach { incident ->
                    val isSelected = selectedIncidentId == incident.id || (selectedStationName != null && incident.assigned_station_name == selectedStationName)
                    IncidentCard(
                        incident = incident,
                        isSelected = isSelected,
                        onClick = { onIncidentClick(incident) }
                    )
                }
            }
        }
    }
}

@Composable
fun IncidentCard(
    incident: IncidentResponse,
    isSelected: Boolean = false,
    onClick: (() -> Unit)? = null
) {
    val statusColor = when (incident.status) {
        "active" -> Color(0xFF16A34A)
        "escalated" -> Color(0xFFDC2626)
        "resolved" -> Color(0xFF0284C7)
        "pending_verification" -> Color(0xFFD97706)
        "archived" -> Color(0xFF64748B)
        else -> Color(0xFF6B7280)
    }
    val severityColor = when (incident.severity) {
        "critical" -> Color(0xFFBE123C)
        "high" -> Color(0xFFD97706)
        "medium" -> Color(0xFF0284C7)
        else -> Color(0xFF64748B)
    }
    fun pretty(s: String) = s.replace(Regex("[_\\-]+"), " ")
        .split(" ")
        .joinToString(" ") { it.replaceFirstChar { c -> c.uppercase() } }

    val borderColor = if (isSelected) Color(0xFF3B82F6) else MaterialTheme.colorScheme.outlineVariant
    val bgColor = if (isSelected) Color(0xFFEFF6FF) else MaterialTheme.colorScheme.surfaceVariant
    val borderWidth = if (isSelected) 2.dp else 1.dp

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = bgColor),
        border = androidx.compose.foundation.BorderStroke(borderWidth, borderColor),
        elevation = CardDefaults.cardElevation(defaultElevation = if (isSelected) 4.dp else 0.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // Title row + severity badge
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                AutoTranslatedText(
                    text = incident.title,
                    fontWeight = FontWeight.SemiBold,
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(100.dp))
                        .background(severityColor.copy(alpha = 0.12f))
                        .border(1.dp, severityColor.copy(alpha = 0.3f), RoundedCornerShape(100.dp))
                        .padding(horizontal = 10.dp, vertical = 4.dp)
                ) {
                    Text(
                        text = pretty(incident.severity),
                        color = severityColor,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }

            Spacer(modifier = Modifier.height(4.dp))

            // Location + Status
            Row(verticalAlignment = Alignment.CenterVertically) {
                AutoTranslatedText(
                    text = incident.location_name,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(text = " - ", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 12.sp)
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(100.dp))
                        .background(statusColor.copy(alpha = 0.1f))
                        .padding(horizontal = 8.dp, vertical = 2.dp)
                ) {
                    Text(
                        text = pretty(incident.status),
                        color = statusColor,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }

            // Route impact
            if (incident.route_impact_summary != null) {
                Spacer(modifier = Modifier.height(6.dp))
                AutoTranslatedText(
                    text = incident.route_impact_summary,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(10.dp))
            androidx.compose.material3.Divider(color = MaterialTheme.colorScheme.outlineVariant, thickness = 1.dp)
            Spacer(modifier = Modifier.height(10.dp))

            // Details grid: ID, Confidence, Force, Barricades
            Row(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text = "ID",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        letterSpacing = 0.5.sp
                    )
                    Text(
                        text = incident.id.take(16) + "...",
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontWeight = FontWeight.Medium
                    )
                }
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text = "CONFIDENCE",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        letterSpacing = 0.5.sp
                    )
                    Text(
                        text = "${(incident.confidence_score * 100).toInt()}%",
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            Row(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text = "FORCE",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        letterSpacing = 0.5.sp
                    )
                    Text(
                        text = incident.police_force_required?.toString() ?: "-",
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontWeight = FontWeight.Medium
                    )
                }
                Column(modifier = Modifier.weight(1f), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    Text(
                        text = "BARRICADES",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        letterSpacing = 0.5.sp
                    )
                    Text(
                        text = incident.barricades_required?.toString() ?: "-",
                        fontSize = 11.sp,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun CommandCenterHeader(
    onNavigateToModelInsights: () -> Unit = {},
    onNavigateToSubmitReport: () -> Unit = {},
    onNavigateToMapIntelligence: () -> Unit = {}
) {
    val context = LocalContext.current
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(24.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
        border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
    ) {
        Column(modifier = Modifier.padding(24.dp)) {
            AutoTranslatedText(
                text = "SANCHAR SARTHI",
                style = MaterialTheme.typography.labelSmall,
                color = Color(0xFF1D4ED8),
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(12.dp))
            AutoTranslatedText(
                text = "Predictive traffic command twin for event-driven congestion.",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.padding(bottom = 16.dp)
            )
            
            FlowRow(
                modifier = Modifier.fillMaxWidth().padding(bottom = 20.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                val buttonColors = ButtonDefaults.outlinedButtonColors(containerColor = MaterialTheme.colorScheme.surfaceVariant, contentColor = Color(0xFF334155))
                OutlinedButton(onClick = onNavigateToModelInsights, shape = RoundedCornerShape(100.dp), colors = buttonColors, border = androidx.compose.foundation.BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
                    AutoTranslatedText("Open model insights", fontSize = 13.sp)
                }
                OutlinedButton(onClick = onNavigateToSubmitReport, shape = RoundedCornerShape(100.dp), colors = ButtonDefaults.outlinedButtonColors(containerColor = Color(0xFFECFEFF), contentColor = Color(0xFF0891B2)), border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFCFFAFE))) {
                    AutoTranslatedText("Submit report", fontSize = 13.sp)
                }
                OutlinedButton(onClick = onNavigateToMapIntelligence, shape = RoundedCornerShape(100.dp), colors = ButtonDefaults.outlinedButtonColors(containerColor = Color(0xFFFFFBEB), contentColor = Color(0xFFD97706)), border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFEF3C7))) {
                    AutoTranslatedText("Open map intelligence", fontSize = 13.sp)
                }
                OutlinedButton(onClick = { Toast.makeText(context, "Post-event learning: Coming soon", Toast.LENGTH_SHORT).show() }, shape = RoundedCornerShape(100.dp), colors = ButtonDefaults.outlinedButtonColors(containerColor = Color(0xFFF0FDF4), contentColor = Color(0xFF16A34A)), border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFDCFCE7))) {
                    AutoTranslatedText("Open post-event learning", fontSize = 13.sp)
                }
            }

            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(16.dp))
                    .background(Color(0xFFF0F6FF))
                    .border(1.dp, Color(0xFFDBEAFE), RoundedCornerShape(16.dp))
                    .padding(16.dp)
            ) {
                Column {
                    AutoTranslatedText("SYSTEM STATE", style = MaterialTheme.typography.labelSmall, color = Color(0xFF3B82F6), fontWeight = FontWeight.SemiBold)
                    Spacer(modifier = Modifier.height(4.dp))
                    AutoTranslatedText("Operational shell ready", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface, fontSize = 18.sp)
                }
            }
        }
    }
}

@Composable
fun SystemStateGrid(metrics: SystemStateMetrics) {
    PlatformSectionCard(
        title = "System State",
        subtitle = "COMMAND CENTER"
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 4.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Row(modifier = Modifier.fillMaxWidth()) {
                MetricItem("Active Events", metrics.activeEvents.toString(), Modifier.weight(1f), Color(0xFF1D4ED8))
                MetricItem("Critical Events", metrics.criticalEvents.toString(), Modifier.weight(1f), Color(0xFFBE123C))
            }
            Row(modifier = Modifier.fillMaxWidth()) {
                MetricItem("Hotspots", metrics.hotspots.toString(), Modifier.weight(1f), Color(0xFFD97706))
                MetricItem("Pending Reports", metrics.pendingReports.toString(), Modifier.weight(1f), Color(0xFF0284C7))
            }
            Row(modifier = Modifier.fillMaxWidth()) {
                MetricItem("Resolved Today", metrics.resolvedToday.toString(), Modifier.weight(1f), Color(0xFF16A34A))
                MetricItem("Recommendations", metrics.recommendations.toString(), Modifier.weight(1f), Color(0xFF0284C7))
            }
            Row(modifier = Modifier.fillMaxWidth()) {
                MetricItem("Total Events", metrics.totalEvents.toString(), Modifier.weight(1f), Color(0xFF0F172A))
                MetricItem("Total Incidents", metrics.totalIncidents.toString(), Modifier.weight(1f), Color(0xFF0F172A))
            }
        }
    }
}

@Composable
fun MetricItem(label: String, value: String, modifier: Modifier = Modifier, valueColor: Color = Color.Black) {
    Row(modifier = modifier) {
        AutoTranslatedText(text = "$label: ", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 15.sp)
        AutoTranslatedText(text = value, color = valueColor, fontWeight = FontWeight.Bold, fontSize = 15.sp)
    }
}

