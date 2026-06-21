package com.namangulati.sancharsarthi.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Assessment
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.Dashboard
import androidx.compose.material.icons.outlined.Explore
import androidx.compose.material.icons.outlined.Map
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Public
import androidx.compose.material.icons.outlined.Route
import androidx.compose.material.icons.outlined.Science
import androidx.compose.material.icons.outlined.Security
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material.icons.outlined.SupportAgent
import androidx.compose.material.icons.outlined.TipsAndUpdates
import androidx.compose.material.icons.outlined.AdminPanelSettings
import androidx.compose.ui.graphics.vector.ImageVector

data class NavigationSection(
    val title: String,
    val items: List<AppNavigationItem>
)

enum class AppNavigationItem(
    val label: String,
    val icon: ImageVector,
    val destination: EventFlowDestination // Mapped to existing screens
) {
    // PORTALS
    CommandCenter("Command Center", Icons.Outlined.Dashboard, EventFlowDestination.Overview),
    ControlRoom("Control Room", Icons.Outlined.SupportAgent, EventFlowDestination.Overview),
    OfficerPortal("Officer Portal", Icons.Outlined.Security, EventFlowDestination.Officer),
    AdminPortal("Admin Portal", Icons.Outlined.AdminPanelSettings, EventFlowDestination.Admin),
    UserMode("User Mode", Icons.Outlined.Person, EventFlowDestination.Citizen),

    // DASHBOARDS
    MapIntelligence("Map Intelligence", Icons.Outlined.Map, EventFlowDestination.Map),
    Explorer("Explorer", Icons.Outlined.Explore, EventFlowDestination.Explorer),

    // INTELLIGENCE
    ModelInsights("Model Insights", Icons.Outlined.AutoAwesome, EventFlowDestination.ModelInsights),
    Simulation("Simulation", Icons.Outlined.Science, EventFlowDestination.Simulation),
    PostEventLearning("Post-Event Learning", Icons.Outlined.TipsAndUpdates, EventFlowDestination.PostEventLearning)
}

val AppNavigationSections = listOf(
    NavigationSection(
        title = "PORTALS",
        items = listOf(
            AppNavigationItem.CommandCenter,
            AppNavigationItem.ControlRoom,
            AppNavigationItem.OfficerPortal,
            AppNavigationItem.AdminPortal,
            AppNavigationItem.UserMode,
        )
    ),
    NavigationSection(
        title = "DASHBOARDS",
        items = listOf(
            AppNavigationItem.MapIntelligence,
            AppNavigationItem.Explorer,
        )
    ),
    NavigationSection(
        title = "INTELLIGENCE",
        items = listOf(
            AppNavigationItem.ModelInsights,
            AppNavigationItem.Simulation,
            AppNavigationItem.PostEventLearning,
        )
    )
)
