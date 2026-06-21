package com.namangulati.sancharsarthi.data.local

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PlatformBlueprintLocalDataSourceTest {
    private val dataSource = PlatformBlueprintLocalDataSource()

    @Test
    fun load_returns_phase22a_aligned_namespace_and_map_policy() {
        val blueprint = dataSource.load()

        assertEquals("com.namangulati.sancharsarthi", blueprint.namespace)
        assertEquals("MapmyIndia / Mappls", blueprint.mapPolicy.primaryProvider)
        assertEquals("OpenStreetMap local overlay mode", blueprint.mapPolicy.fallbackProvider)
        assertEquals("FastAPI backend role and scope checks", blueprint.authAuthority.finalAuthority)
    }

    @Test
    fun load_keeps_current_backend_route_families() {
        val blueprint = dataSource.load()
        val paths = blueprint.apiFamilies.map { it.path }

        assertTrue(paths.contains("/api/foundation/*"))
        assertTrue(paths.contains("/api/reports/*"))
        assertTrue(paths.contains("/api/events/*"))
        assertTrue(paths.contains("/api/officer/*"))
        assertTrue(paths.contains("/api/recommendations/*"))
        assertTrue(paths.contains("/api/map/*"))
        assertTrue(paths.contains("/api/analytics/*"))
        assertTrue(paths.contains("/api/command-center/*"))
        assertTrue(paths.contains("/api/demo/*"))
        assertTrue(paths.contains("/api/admin/*"))
        assertTrue(paths.contains("/api/health"))
    }

    @Test
    fun load_uses_current_auth_bootstrap_routes_without_fake_officer_login() {
        val blueprint = dataSource.load()
        val routes = blueprint.authBootstrapPolicy.routes.mapNotNull { it.path }

        assertFalse(routes.contains("/api/officer/login"))
        assertTrue(routes.contains("/api/officer/assignments"))
        assertTrue(routes.contains("/api/foundation/control-room"))
        assertTrue(routes.contains("/api/foundation/admin/overview"))
        assertTrue(routes.contains("/api/health"))
    }

    @Test
    fun load_documents_all_phase22b_auth_error_states() {
        val blueprint = dataSource.load()

        assertEquals(8, blueprint.authErrorStates.size)
        assertTrue(blueprint.authErrorStates.any { it.kind.label == "Officer profile missing" })
        assertTrue(blueprint.authErrorStates.any { it.kind.label == "Backend unavailable" })
    }
}
