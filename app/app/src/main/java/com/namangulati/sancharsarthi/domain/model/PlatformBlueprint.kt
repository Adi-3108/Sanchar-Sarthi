package com.namangulati.sancharsarthi.domain.model

import com.namangulati.sancharsarthi.core.auth.AuthAuthority
import com.namangulati.sancharsarthi.core.auth.AuthBootstrapPolicy
import com.namangulati.sancharsarthi.core.auth.AuthErrorState
import com.namangulati.sancharsarthi.core.location.MapPolicy
import com.namangulati.sancharsarthi.core.network.ApiEnvironment
import com.namangulati.sancharsarthi.core.session.AccessLevel
import com.namangulati.sancharsarthi.core.sync.OfflinePolicy

data class BrandPillar(
    val title: String,
    val subtitle: String,
    val summary: String,
)

data class ApiFamily(
    val path: String,
    val audience: String,
    val note: String,
)

data class MobileArea(
    val title: String,
    val audience: String,
    val primaryAccess: AccessLevel,
    val supportedAccessLevels: List<AccessLevel>,
    val summary: String,
    val currentSourceOfTruth: String,
    val backendRoutes: List<String>,
    val capabilities: List<String>,
)

data class ArchitectureLayer(
    val title: String,
    val packages: List<String>,
    val reason: String,
)

data class PlatformRule(
    val title: String,
    val detail: String,
)

data class PlatformBlueprint(
    val appName: String,
    val tagline: String,
    val namespace: String,
    val webRoutes: List<String>,
    val apiFamilies: List<ApiFamily>,
    val brandPillars: List<BrandPillar>,
    val mobileAreas: List<MobileArea>,
    val architectureLayers: List<ArchitectureLayer>,
    val platformRules: List<PlatformRule>,
    val authBootstrapPolicy: AuthBootstrapPolicy,
    val authErrorStates: List<AuthErrorState>,
    val authAuthority: AuthAuthority,
    val mapPolicy: MapPolicy,
    val offlinePolicy: OfflinePolicy,
    val apiEnvironment: ApiEnvironment,
)
