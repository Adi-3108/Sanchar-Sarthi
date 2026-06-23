package com.namangulati.sancharsarthi.data.local

import com.namangulati.sancharsarthi.core.auth.AuthAuthority
import com.namangulati.sancharsarthi.core.auth.AuthBootstrapPolicy
import com.namangulati.sancharsarthi.core.auth.AuthBootstrapRoute
import com.namangulati.sancharsarthi.core.auth.AuthErrorCatalog
import com.namangulati.sancharsarthi.core.location.MapPolicy
import com.namangulati.sancharsarthi.core.network.ApiEnvironment
import com.namangulati.sancharsarthi.core.session.AccessLevel
import com.namangulati.sancharsarthi.core.sync.OfflinePolicy
import com.namangulati.sancharsarthi.domain.model.ApiFamily
import com.namangulati.sancharsarthi.domain.model.ArchitectureLayer
import com.namangulati.sancharsarthi.domain.model.BrandPillar
import com.namangulati.sancharsarthi.domain.model.MobileArea
import com.namangulati.sancharsarthi.domain.model.PlatformBlueprint
import com.namangulati.sancharsarthi.domain.model.PlatformRule

class PlatformBlueprintLocalDataSource {
    fun load(): PlatformBlueprint {
        return PlatformBlueprint(
            appName = "Sanchar Sarthi",
            tagline = "Android foundation for public intake, officer response, and predictive traffic command workflows.",
            namespace = "com.namangulati.sancharsarthi",
            webRoutes = listOf(
                "/",
                "/user",
                "/control-room",
                "/command-center",
                "/officer",
                "/admin",
                "/map-intelligence",
                "/explorer",
                "/reports",
                "/model-insights",
                "/simulation",
                "/post-event-learning",
                "/settings",
                "/login",
                "/events/[id]",
            ),
            apiFamilies = listOf(
                ApiFamily("/api/foundation/*", "Citizen, control room, admin", "Public incident intake, triage, and station workflow."),
                ApiFamily("/api/reports/*", "Citizen and intelligence pipeline", "Congestion signals feed EventFlow event intelligence."),
                ApiFamily("/api/events/*", "Officer, control room, admin", "Dossiers, simulations, and post-event records live here."),
                ApiFamily("/api/officer/*", "Police officer", "Assignment-aware field visibility comes from backend-verified scope."),
                ApiFamily("/api/recommendations/*", "Internal planning", "Estimated and recommended planning outputs only."),
                ApiFamily("/api/map/*", "Internal mapping", "MapmyIndia / Mappls only, backend-mediated."),
                ApiFamily("/api/analytics/*", "Internal intelligence", "Hotspots, model runs, and corridor analytics."),
                ApiFamily("/api/command-center/*", "Control room", "Operational summary and city-level shell state."),
                ApiFamily("/api/demo/*", "Internal demo readiness", "Seed and readiness surfaces for walkthrough prep."),
                ApiFamily("/api/admin/*", "Admin", "Governance, onboarding, and privileged station management."),
                ApiFamily("/api/health", "Internal system status", "Backend health and model artifact state."),
            ),
            brandPillars = listOf(
                BrandPillar(
                    title = "Sanchar Sarthi",
                    subtitle = "Public and operations shell",
                    summary = "Foundation intake, station mapping, triage, and the everyday user-facing shell stay under Sanchar Sarthi."
                ),
                BrandPillar(
                    title = "EventFlow AI",
                    subtitle = "Predictive intelligence layer",
                    summary = "Simulation, Event DNA, recommendations, map intelligence, and learning remain clearly marked as estimated or simulated intelligence."
                ),
            ),
            mobileAreas = listOf(
                MobileArea(
                    title = "Public issue reporting",
                    audience = "Citizen",
                    primaryAccess = AccessLevel.PublicCitizen,
                    supportedAccessLevels = listOf(AccessLevel.PublicCitizen, AccessLevel.Citizen),
                    summary = "Fast mobile reporting for public traffic issues without forcing a login wall.",
                    currentSourceOfTruth = "foundation + reports APIs",
                    backendRoutes = listOf(
                        "POST /api/foundation/incidents/report",
                        "POST /api/reports/congestion",
                    ),
                    capabilities = listOf(
                        "Guest-friendly intake",
                        "Raw multilingual description upload",
                        "Offline queue for citizen reports",
                    ),
                ),
                MobileArea(
                    title = "Incident browsing and local advisories",
                    audience = "Citizen / control room",
                    primaryAccess = AccessLevel.Citizen,
                    supportedAccessLevels = listOf(AccessLevel.PublicCitizen, AccessLevel.Citizen, AccessLevel.ControlRoom, AccessLevel.Admin),
                    summary = "Shared foundation visibility keeps citizens informed while internal users stay close to local incident flow.",
                    currentSourceOfTruth = "foundation APIs",
                    backendRoutes = listOf(
                        "GET /api/foundation/incidents",
                        "GET /api/foundation/control-room",
                    ),
                    capabilities = listOf(
                        "Read local incident state",
                        "Respect backend role enforcement",
                        "Preserve citizen and internal boundaries",
                    ),
                ),
                MobileArea(
                    title = "Officer assignment and escalation",
                    audience = "Police officer",
                    primaryAccess = AccessLevel.PoliceOfficer,
                    supportedAccessLevels = listOf(AccessLevel.PoliceOfficer),
                    summary = "Assignment-aware field tools must follow profile, corridor, zone, station, and event scope from FastAPI.",
                    currentSourceOfTruth = "officer + events + recommendations APIs",
                    backendRoutes = listOf(
                        "GET /api/officer/assignments",
                        "GET /api/events/{event_id}",
                        "POST /api/events/{event_id}/live-update",
                    ),
                    capabilities = listOf(
                        "Load verified assignments",
                        "Open event dossiers",
                        "Queue field updates offline",
                    ),
                ),
                MobileArea(
                    title = "Event simulation and planning",
                    audience = "Internal only",
                    primaryAccess = AccessLevel.ControlRoom,
                    supportedAccessLevels = listOf(AccessLevel.ControlRoom, AccessLevel.Admin),
                    summary = "Simulation remains internal and must always be labeled simulated, estimated, or recommended.",
                    currentSourceOfTruth = "events/simulate + recommendations/event-plan",
                    backendRoutes = listOf(
                        "POST /api/events/simulate",
                        "POST /api/recommendations/event-plan",
                    ),
                    capabilities = listOf(
                        "Simulation request drafting",
                        "Planning recommendation preview",
                        "No fake certainty beyond backend outputs",
                    ),
                ),
                MobileArea(
                    title = "Map intelligence",
                    audience = "Internal first",
                    primaryAccess = AccessLevel.ControlRoom,
                    supportedAccessLevels = listOf(AccessLevel.PoliceOfficer, AccessLevel.ControlRoom, AccessLevel.Admin),
                    summary = "The app must show MapmyIndia / Mappls provider state honestly.",
                    currentSourceOfTruth = "map + analytics + foundation overlays",
                    backendRoutes = listOf(
                        "GET /api/map/config",
                        "POST /api/map/route",
                        "POST /api/map/geocode",
                        "GET /api/analytics/hotspots",
                    ),
                    capabilities = listOf(
                        "Primary provider indicator",
                        "Mappls key availability visibility",
                        "Clear unavailable state when provider access is missing",
                    ),
                ),
                MobileArea(
                    title = "Learning and after-action review",
                    audience = "Internal only",
                    primaryAccess = AccessLevel.ControlRoom,
                    supportedAccessLevels = listOf(AccessLevel.ControlRoom, AccessLevel.Admin),
                    summary = "After-action review extends the same dossier contracts instead of inventing a separate mobile model.",
                    currentSourceOfTruth = "events/{id} + post-event-report",
                    backendRoutes = listOf(
                        "GET /api/events/{event_id}",
                        "POST /api/events/{event_id}/post-event-report",
                    ),
                    capabilities = listOf(
                        "Event recap",
                        "Recommendation hindsight",
                        "Dataset-honest learning summaries",
                    ),
                ),
            ),
            architectureLayers = listOf(
                ArchitectureLayer(
                    title = "core",
                    packages = listOf("auth", "network", "session", "location", "sync", "datastore"),
                    reason = "Shared authority, network, and offline rules belong in the platform core."
                ),
                ArchitectureLayer(
                    title = "data",
                    packages = listOf("remote", "local", "repository"),
                    reason = "Data access stays backend-first and repository-mediated."
                ),
                ArchitectureLayer(
                    title = "domain",
                    packages = listOf("model", "usecase"),
                    reason = "Product language and business meaning stay separate from UI widgets."
                ),
                ArchitectureLayer(
                    title = "feature",
                    packages = listOf("splash", "auth", "citizen", "officer", "foundation", "simulation", "map", "learning", "settings"),
                    reason = "Feature packages mirror the current hybrid platform instead of an old single-dashboard assumption."
                ),
                ArchitectureLayer(
                    title = "navigation + design",
                    packages = listOf("navigation", "design"),
                    reason = "Navigation and shared visuals stay platform-wide, not buried in one feature."
                ),
            ),
            platformRules = listOf(
                PlatformRule(
                    title = "Firebase proves identity; FastAPI proves authority",
                    detail = "Android may sign users in with Firebase, but the backend remains the final authority for role and scope."
                ),
                PlatformRule(
                    title = "Citizen and internal flows stay separate",
                    detail = "Public reporting cannot silently inherit officer or admin behavior just because the app shares one shell."
                ),
                PlatformRule(
                    title = "Route naming must match the current backend",
                    detail = "The mobile app should mirror existing route families instead of introducing mobile-only aliases."
                ),
                PlatformRule(
                    title = "Map honesty is part of the product",
                    detail = "MapmyIndia / Mappls is the only supported map provider for submission."
                ),
                PlatformRule(
                    title = "Intelligence copy stays honest",
                    detail = "Use estimated, recommended, simulated, advisory, and fallback wording throughout mobile."
                ),
            ),
            authBootstrapPolicy = AuthBootstrapPolicy(
                routes = listOf(
                    AuthBootstrapRoute(
                        accessLevel = AccessLevel.PublicCitizen,
                        method = "NONE",
                        path = null,
                        tokenRequired = false,
                        purpose = "Guest reporting remains usable without Firebase sign-in.",
                    ),
                    AuthBootstrapRoute(
                        accessLevel = AccessLevel.Citizen,
                        method = "GET",
                        path = "/api/foundation/incidents",
                        tokenRequired = true,
                        purpose = "Firebase user can be backend-verified or auto-provisioned as citizen.",
                    ),
                    AuthBootstrapRoute(
                        accessLevel = AccessLevel.PoliceOfficer,
                        method = "GET",
                        path = "/api/officer/assignments",
                        tokenRequired = true,
                        purpose = "Officer bootstrap returns active profile, station, assignments, corridors, zones, reports, and overlays.",
                    ),
                    AuthBootstrapRoute(
                        accessLevel = AccessLevel.ControlRoom,
                        method = "GET",
                        path = "/api/foundation/control-room",
                        tokenRequired = true,
                        purpose = "Control-room bootstrap returns incident, station, hotspot, and triage state.",
                    ),
                    AuthBootstrapRoute(
                        accessLevel = AccessLevel.Admin,
                        method = "GET",
                        path = "/api/foundation/admin/overview",
                        tokenRequired = true,
                        purpose = "Admin bootstrap confirms governance access before showing privileged workflows.",
                    ),
                    AuthBootstrapRoute(
                        accessLevel = AccessLevel.Admin,
                        method = "GET",
                        path = "/api/health",
                        tokenRequired = true,
                        purpose = "Admin summary also checks backend and artifact state.",
                    ),
                ),
                rules = listOf(
                    "Protected requests attach Authorization: Bearer <Firebase ID token>.",
                    "The mobile role picker is only a UX hint; backend role and profile state decide access.",
                    "There is no /api/officer/login endpoint; officer bootstrap uses /api/officer/assignments.",
                    "Officer access requires an active PoliceOfficerProfile plus station, corridor, zone, or event scope.",
                    "Guest/public reporting stays separated from citizen-authenticated and internal planning flows.",
                ),
            ),
            authErrorStates = AuthErrorCatalog.all,
            authAuthority = AuthAuthority(
                identityProvider = "Firebase client authentication",
                finalAuthority = "FastAPI backend role and scope checks",
                notes = listOf(
                    "New Firebase users can be auto-provisioned as citizen.",
                    "Officer access depends on an active PoliceOfficerProfile.",
                    "UI role choices are hints; backend role and profile state decide access.",
                ),
            ),
            mapPolicy = MapPolicy(
                primaryProvider = "MapmyIndia / Mappls",
                honestyNotes = listOf(
                    "Do not claim guaranteed real-world navigation precision.",
                    "Show a clear unavailable state whenever Mappls access is missing.",
                    "Keep provider state visible for command and officer users.",
                ),
            ),
            offlinePolicy = OfflinePolicy(
                citizenQueueEnabled = true,
                officerQueueEnabled = true,
                notes = listOf(
                    "Queue citizen reports and officer updates locally.",
                    "Never display queued local state as server-confirmed command state.",
                    "Retries stay bounded and visible to the user.",
                ),
            ),
            apiEnvironment = ApiEnvironment(
                localEmulatorBaseUrl = "http://10.0.2.2:8000",
                transportRule = "Android app -> FastAPI backend -> database / ML / route provider / analytics",
                forbiddenLinks = listOf(
                    "Android app -> PostgreSQL directly",
                    "Android app -> Supabase directly",
                    "Android app -> Firebase Admin SDK",
                    "Android app -> private MapmyIndia REST credentials",
                ),
            ),
        )
    }
}
