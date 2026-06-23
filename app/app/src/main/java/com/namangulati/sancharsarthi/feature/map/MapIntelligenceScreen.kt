package com.namangulati.sancharsarthi.feature.map

import android.annotation.SuppressLint
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.lifecycle.viewmodel.compose.viewModel
import com.namangulati.sancharsarthi.core.design.ShimmerBox
import com.namangulati.sancharsarthi.core.design.SkeletonList
import com.namangulati.sancharsarthi.core.network.HotspotResponseItem
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText
import com.namangulati.sancharsarthi.design.PlatformSectionCard
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun MapIntelligenceScreen(
    state: PlatformFoundationUiState,
    onNavigateBack: () -> Unit = {},
    viewModel: MapIntelligenceViewModel = viewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    var webViewRef by remember { mutableStateOf<WebView?>(null) }

    // Removed LaunchedEffects for map updates, will use AndroidView update block

    LazyColumn(
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        modifier = Modifier.fillMaxSize().background(MaterialTheme.colorScheme.background)
    ) {
        item {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(24.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
            ) {
                Column(modifier = Modifier.padding(24.dp)) {
                    AutoTranslatedText("MAP INTELLIGENCE", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(12.dp))
                    AutoTranslatedText("Operational map for hotspots, reports, routes, and conflicts.", fontSize = 24.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                    Spacer(modifier = Modifier.height(16.dp))
                    AutoTranslatedText("Primary geospatial layer is MapmyIndia / Mappls. Conflict overlays now come from the real multi-event analysis API, while representative report markers remain a safe demo overlay until a dedicated map feed is added.", fontSize = 14.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }

        item {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(400.dp)
                    .clip(RoundedCornerShape(24.dp))
                    .border(1.dp, MaterialTheme.colorScheme.outlineVariant, RoundedCornerShape(24.dp))
            ) {
                if (uiState.isLoading) {
                    ShimmerBox(modifier = Modifier.matchParentSize(), cornerRadius = 24.dp)
                } else {
                    AndroidView(
                    factory = { ctx ->
                        WebView(ctx).apply {
                            layoutParams = android.view.ViewGroup.LayoutParams(
                                android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                                android.view.ViewGroup.LayoutParams.MATCH_PARENT
                            )
                            settings.javaScriptEnabled = true
                            settings.domStorageEnabled = true
                            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP) {
                                settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
                            }
                            webViewClient = WebViewClient()
                            webChromeClient = android.webkit.WebChromeClient()
                            
                            addJavascriptInterface(object {
                                @android.webkit.JavascriptInterface
                                fun onMapLoaded() {
                                    post {
                                        evaluateJavascript("javascript:window.isMapReady = true;", null)
                                    }
                                }
                            }, "AndroidInterface")

                            val htmlData = context.assets.open("mappls_map.html").bufferedReader().use { it.readText() }
                            val htmlWithKey = htmlData.replace("YOUR_API_KEY_HERE", com.namangulati.sancharsarthi.BuildConfig.MAPS_API_KEY)
                            loadDataWithBaseURL("file:///android_asset/", htmlWithKey, "text/html", "UTF-8", null)
                            webViewRef = this
                        }
                    },
                    update = { webView ->
                        if (uiState.hotspots.isNotEmpty()) {
                            val hotspotsJsonList = uiState.hotspots.map { h ->
                                val severity = when {
                                    h.cluster_risk_score > 60 -> "high"
                                    h.cluster_risk_score > 30 -> "medium"
                                    else -> "low"
                                }
                                JsonObject(mapOf(
                                    "lat" to JsonPrimitive(h.centroid_latitude),
                                    "lng" to JsonPrimitive(h.centroid_longitude),
                                    "count" to JsonPrimitive(h.cluster_event_count),
                                    "label" to JsonPrimitive(h.location_cluster_id),
                                    "severity" to JsonPrimitive(severity)
                                ))
                            }
                            val jsonStr = Json.encodeToString(hotspotsJsonList)
                            webView.evaluateJavascript("if(window.loadHotspots) { loadHotspots('$jsonStr'); } else { window.pendingHotspots = '$jsonStr'; }", null)
                        }
                        
                        val route = uiState.routeData
                        if (route != null) {
                            val routeJsonList = listOf(JsonObject(mapOf(
                                "polyline" to kotlinx.serialization.json.JsonArray(route.polyline.map { point ->
                                    kotlinx.serialization.json.JsonArray(point.map { JsonPrimitive(it) })
                                })
                            )))
                            val routeJsonStr = Json.encodeToString(routeJsonList)
                            webView.evaluateJavascript("if(window.loadRoutes) { loadRoutes('$routeJsonStr'); } else { window.pendingRoutes = '$routeJsonStr'; }", null)
                        }
                    },
                    modifier = Modifier.fillMaxSize()
                    )
                }
            }
        }

        // Error banner with retry — shown when hotspot fetch failed (e.g. expired token)
        if (uiState.errorMessage != null || (uiState.hotspots.isEmpty() && !uiState.isLoading)) {
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF3CD)),
                    border = BorderStroke(1.dp, Color(0xFFFFD86E))
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            AutoTranslatedText(
                                "Hotspots unavailable",
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF7A5000),
                                fontSize = 14.sp
                            )
                            if (uiState.errorMessage != null) {
                                Spacer(modifier = Modifier.height(4.dp))
                                AutoTranslatedText(
                                    uiState.errorMessage!!,
                                    color = Color(0xFF7A5000),
                                    fontSize = 12.sp
                                )
                            }
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Button(
                            onClick = { viewModel.reload() },
                            shape = RoundedCornerShape(12.dp),
                            colors = ButtonDefaults.buttonColors(
                                containerColor = Color(0xFFF59E0B),
                                contentColor = Color.White
                            )
                        ) {
                            AutoTranslatedText("Retry", fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                Card(modifier = Modifier.weight(1f), shape = RoundedCornerShape(24.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        AutoTranslatedText("Map access sign-in", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface, fontSize = 16.sp)
                        Spacer(modifier = Modifier.height(8.dp))
                        AutoTranslatedText("Hotspots, routing, geocode, and multi-event coordination are protected internal tools even though the map shell itself can still load.", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Spacer(modifier = Modifier.height(12.dp))
                        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant), border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
                            Column(modifier = Modifier.padding(12.dp).fillMaxWidth()) {
                                val email = when (val result = state.sessionBootstrapResult) {
                                    is com.namangulati.sancharsarthi.core.session.SessionBootstrapResult.Authorized -> result.session.email
                                    is com.namangulati.sancharsarthi.core.session.SessionBootstrapResult.Blocked -> result.fallbackSession.email
                                } ?: "Not signed in"
                                AutoTranslatedText("Signed in: $email", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                AutoTranslatedText("Selected UI role: ${state.selectedAccessLevel.displayName}", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedButton(
                            onClick = { /* Sign out logic */ },
                            shape = RoundedCornerShape(100.dp),
                            border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant),
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.onSurfaceVariant)
                        ) {
                            AutoTranslatedText("Sign out", fontSize = 13.sp)
                        }
                    }
                }
                Card(modifier = Modifier.weight(1f), shape = RoundedCornerShape(24.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        AutoTranslatedText("PROVIDER", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(8.dp))
                        AutoTranslatedText(uiState.mapConfig?.activeProvider ?: "Checking provider", fontWeight = FontWeight.Bold, fontSize = 16.sp, color = MaterialTheme.colorScheme.onSurface)
                        Spacer(modifier = Modifier.height(8.dp))
                        AutoTranslatedText("Map key available: ${if (uiState.mapConfig?.mapKeyAvailable == true) "yes" else "no"}", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        AutoTranslatedText("Routing status: ${uiState.routeData?.provider ?: "demo overlay"}", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
            }
        }

        item {
            Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                Card(modifier = Modifier.weight(1f), shape = RoundedCornerShape(24.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        AutoTranslatedText("GEOCODE SEARCH", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedTextField(
                            value = uiState.geocodeQuery,
                            onValueChange = { viewModel.updateGeocodeQuery(it) },
                            label = { AutoTranslatedText("Address query") },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Button(onClick = { viewModel.searchAddress() }, modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(12.dp)) {
                            AutoTranslatedText(if(uiState.isGeocoding) "Searching..." else "Search address")
                        }
                        Spacer(modifier = Modifier.height(12.dp))
                        AutoTranslatedText("Search results will appear as map markers when provider geocoding is available.", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        uiState.geocodeCandidates.forEach { candidate ->
                            Spacer(modifier = Modifier.height(8.dp))
                            Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)) {
                                Column(modifier = Modifier.padding(12.dp).fillMaxWidth()) {
                                    AutoTranslatedText(candidate.label, fontWeight = FontWeight.Bold)
                                    AutoTranslatedText("${candidate.coordinate.getOrNull(1)}, ${candidate.coordinate.getOrNull(0)} - ${candidate.confidence}", fontSize = 12.sp)
                                }
                            }
                        }
                    }
                }
                Card(modifier = Modifier.weight(1f), shape = RoundedCornerShape(24.dp), colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface), border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        AutoTranslatedText("OVERLAY COUNTS", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(12.dp))
                        val counts = listOf(
                            "Hotspots" to uiState.hotspots.size.toString(),
                            "Reports" to "4",
                            "Search markers" to uiState.geocodeCandidates.size.toString(),
                            "Conflicts" to (uiState.multiEventAnalysis?.officer_allocation?.size ?: 0).toString()
                        )
                        counts.forEach { (label, count) ->
                            Row(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                                AutoTranslatedText(label, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                AutoTranslatedText(count, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                            }
                        }
                    }
                }
            }
        }

        item {
            Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                ) {
                    Column(modifier = Modifier.padding(24.dp)) {
                        AutoTranslatedText("MULTI-EVENT ANALYSIS", fontSize = 11.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                        Spacer(modifier = Modifier.height(16.dp))
                        OutlinedTextField(
                            value = uiState.eventIdsInput,
                            onValueChange = { viewModel.updateEventIds(it) },
                            label = { AutoTranslatedText("Event IDs (comma separated)") },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedTextField(
                            value = uiState.availableOfficersInput,
                            onValueChange = { viewModel.updateOfficers(it) },
                            label = { AutoTranslatedText("Available officers") },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp)
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(
                            onClick = { viewModel.runMultiEventAnalysis() },
                            shape = RoundedCornerShape(12.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary, contentColor = MaterialTheme.colorScheme.onPrimary),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            AutoTranslatedText(if(uiState.isAnalyzing) "Analyzing..." else "Run analysis")
                        }
                        Spacer(modifier = Modifier.height(12.dp))
                        AutoTranslatedText("This feeds the conflict layer from the real multi-event backend analysis instead of a synthetic overlay.", fontSize = 13.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }
                
                Card(
                    modifier = Modifier.fillMaxWidth().defaultMinSize(minHeight = 200.dp),
                    shape = RoundedCornerShape(24.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant) // Grey empty state background
                ) {
                    val analysis = uiState.multiEventAnalysis
                    if (analysis != null) {
                        Column(modifier = Modifier.padding(24.dp)) {
                            AutoTranslatedText("Analysis Status: ${analysis.status}", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                            Spacer(modifier = Modifier.height(12.dp))
                            analysis.officer_allocation.forEach { alloc ->
                                AutoTranslatedText("Event: ${alloc.event_id}", color = MaterialTheme.colorScheme.onSurface)
                                AutoTranslatedText("Officers needed: ${alloc.recommended_officers}", color = MaterialTheme.colorScheme.onSurface)
                                AutoTranslatedText("Rationale: ${alloc.rationale}", color = MaterialTheme.colorScheme.outlineVariant, fontSize = 12.sp)
                                Spacer(modifier = Modifier.height(8.dp))
                            }
                        }
                    } else if (uiState.isAnalyzing) {
                        Column(modifier = Modifier.padding(24.dp)) {
                            SkeletonList(count = 2)
                        }
                    } else {
                        Box(modifier = Modifier.fillMaxSize().padding(32.dp), contentAlignment = Alignment.Center) {
                            AutoTranslatedText("No multi-event coordination analysis has been generated yet.", color = MaterialTheme.colorScheme.onSurfaceVariant, fontSize = 14.sp)
                        }
                    }
                }
            }
        }
        
        if (uiState.hotspots.isNotEmpty()) {
            item {
                AutoTranslatedText("Hotspots", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface, modifier = Modifier.padding(top = 16.dp, bottom = 8.dp))
            }
            item {
                androidx.compose.foundation.lazy.LazyRow(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(16.dp),
                    contentPadding = PaddingValues(bottom = 16.dp)
                ) {
                    items(uiState.hotspots) { hotspot ->
                        HotspotCard(hotspot = hotspot, modifier = Modifier.width(280.dp))
                    }
                }
            }
        }
    }
}

@Composable
fun HotspotCard(hotspot: HotspotResponseItem, modifier: Modifier = Modifier) {
    val severityColor = when {
        hotspot.cluster_risk_score > 60 -> Color(0xFFF59E0B) // High -> Orange
        hotspot.cluster_risk_score > 30 -> Color(0xFFEAB308) // Medium -> Yellow
        else -> Color(0xFF3B82F6) // Low -> Blue
    }
    
    val severityText = when {
        hotspot.cluster_risk_score > 60 -> "High"
        hotspot.cluster_risk_score > 30 -> "Medium"
        else -> "Low"
    }

    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant), // Dark background like the screenshot
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                AutoTranslatedText("HOTSPOT", fontSize = 10.sp, color = MaterialTheme.colorScheme.onSurfaceVariant, fontWeight = FontWeight.Bold)
                AutoTranslatedText(severityText.uppercase(), fontSize = 10.sp, color = severityColor, fontWeight = FontWeight.Bold)
            }
            Spacer(modifier = Modifier.height(4.dp))
            AutoTranslatedText(hotspot.location_cluster_id, fontSize = 16.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f)) {
                    AutoTranslatedText("Events", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    AutoTranslatedText(hotspot.cluster_event_count.toString(), fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                }
                Column(modifier = Modifier.weight(1f)) {
                    AutoTranslatedText("Risk score", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    AutoTranslatedText(hotspot.cluster_risk_score.toInt().toString(), fontSize = 20.sp, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                }
            }
            Spacer(modifier = Modifier.height(16.dp))
            
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                AutoTranslatedText("Top cause", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                AutoTranslatedText(hotspot.cluster_top_event_cause ?: "unknown", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface)
            }
            Spacer(modifier = Modifier.height(4.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                AutoTranslatedText("Road closure", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                AutoTranslatedText("0%", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface)
            }
            Spacer(modifier = Modifier.height(4.dp))
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                AutoTranslatedText("Peak hour", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                AutoTranslatedText("0%", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurface)
            }
        }
    }
}

