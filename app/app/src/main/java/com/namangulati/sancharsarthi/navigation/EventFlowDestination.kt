package com.namangulati.sancharsarthi.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Article
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material.icons.outlined.Map
import androidx.compose.material.icons.outlined.Security
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material.icons.outlined.BarChart
import androidx.compose.material.icons.outlined.Explore
import androidx.compose.material.icons.outlined.Science
import androidx.compose.material.icons.outlined.TipsAndUpdates
import androidx.compose.material.icons.outlined.SupportAgent
import androidx.compose.ui.graphics.vector.ImageVector

enum class EventFlowDestination(
    val label: String,
    val icon: ImageVector,
) {
    Overview(label = "Overview", icon = Icons.Outlined.Home),
    Auth(label = "Auth", icon = Icons.Outlined.Lock),
    Citizen(label = "Citizen", icon = Icons.Outlined.Article),
    Officer(label = "Officer", icon = Icons.Outlined.Security),
    Map(label = "Map", icon = Icons.Outlined.Map),
    Admin(label = "Admin", icon = Icons.Outlined.Security),
    ModelInsights(label = "Model Insights", icon = Icons.Outlined.BarChart),
    Explorer(label = "Explorer", icon = Icons.Outlined.Explore),
    Simulation(label = "Simulation", icon = Icons.Outlined.Science),
    PostEventLearning(label = "Post-Event Learning", icon = Icons.Outlined.TipsAndUpdates),
    ControlRoom(label = "Control Room", icon = Icons.Outlined.SupportAgent)
}
