package com.namangulati.sancharsarthi.navigation

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.Language
import androidx.compose.material.icons.outlined.Lock
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.DrawerValue
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ModalDrawerSheet
import androidx.compose.material3.ModalNavigationDrawer
import androidx.compose.material3.NavigationDrawerItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.rememberDrawerState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import com.google.firebase.auth.FirebaseAuth
import com.google.mlkit.nl.translate.TranslateLanguage
import com.namangulati.sancharsarthi.core.design.SkeletonScreen
import com.namangulati.sancharsarthi.core.session.AccessLevel
import com.namangulati.sancharsarthi.core.session.ProfileStatsStore
import com.namangulati.sancharsarthi.core.translation.TranslationManager
import com.namangulati.sancharsarthi.feature.auth.AuthSessionScreen
import com.namangulati.sancharsarthi.feature.auth.LoginScreen
import com.namangulati.sancharsarthi.feature.auth.LoginViewModel
import com.namangulati.sancharsarthi.feature.citizen.CitizenExperienceScreen
import com.namangulati.sancharsarthi.feature.foundation.FoundationOverviewScreen
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationViewModel
import com.namangulati.sancharsarthi.feature.map.MapIntelligenceScreen
import com.namangulati.sancharsarthi.feature.officer.OfficerWorkspaceScreen
import com.namangulati.sancharsarthi.feature.rag.NammaSarthiAssistantOverlay
import com.namangulati.sancharsarthi.feature.rag.RagAssistantViewModel

import com.namangulati.sancharsarthi.feature.insights.ModelInsightsScreen
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EventFlowApp(viewModel: PlatformFoundationViewModel) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    var currentNavItem by rememberSaveable { mutableStateOf(AppNavigationItem.CommandCenter) }

    LaunchedEffect(state.selectedAccessLevel) {
        if (state.selectedAccessLevel !in listOf(AccessLevel.Admin, AccessLevel.ControlRoom) && currentNavItem == AppNavigationItem.CommandCenter) {
            currentNavItem = AppNavigationItem.UserMode
        }
    }

    val loginViewModel: LoginViewModel = viewModel()
    val loginState by loginViewModel.uiState.collectAsStateWithLifecycle()
    var isLoggedIn by rememberSaveable { mutableStateOf(false) }
    var isCheckingSession by rememberSaveable { mutableStateOf(true) }

    val drawerState = rememberDrawerState(initialValue = DrawerValue.Closed)
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        loginViewModel.checkExistingSession { accessLevel ->
            if (accessLevel != null) {
                viewModel.setAccessLevel(accessLevel)
                isLoggedIn = true
            }
            isCheckingSession = false
        }
    }

    if (isCheckingSession) {
        SkeletonScreen(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            cards = 4
        )
        return
    }

    if (!isLoggedIn) {
        LoginScreen(
            state = loginState,
            onEmailChange = loginViewModel::updateEmail,
            onPasswordChange = loginViewModel::updatePassword,
            onLoginClick = { 
                loginViewModel.submit(onSuccess = { accessLevel ->
                    viewModel.setAccessLevel(accessLevel)
                    isLoggedIn = true
                })
            },
            onToggleMode = loginViewModel::toggleMode,
            onResendVerification = loginViewModel::resendVerification,
            onRoleChange = loginViewModel::updateRole,
        )
    } else {
        val ragAssistantViewModel: RagAssistantViewModel = viewModel()
        val ragAssistantState by ragAssistantViewModel.uiState.collectAsStateWithLifecycle()

        ModalNavigationDrawer(
            drawerState = drawerState,
            drawerContent = {
                ModalDrawerSheet(
                    modifier = Modifier.width(300.dp)
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(16.dp)
                            .verticalScroll(rememberScrollState())
                    ) {
                        // Header (SS Logo + Sanchar Sarthi)
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(bottom = 24.dp, top = 16.dp)
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(40.dp)
                                    .clip(RoundedCornerShape(8.dp))
                                    .background(Color(0xFF0D47A1)),
                                contentAlignment = Alignment.Center
                            ) {
                                Text("SS", color = Color.White, fontWeight = FontWeight.Bold)
                            }
                            Spacer(modifier = Modifier.width(16.dp))
                            Text("Sanchar Sarthi", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                        }

                        // Sections
                        AppNavigationSections.forEach { section ->
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = section.title,
                                color = Color(0xFF1976D2),
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(start = 16.dp, bottom = 8.dp)
                            )
                            section.items.forEach { item ->
                                NavigationDrawerItem(
                                    label = { com.namangulati.sancharsarthi.core.translation.AutoTranslatedText(item.label) },
                                    selected = currentNavItem == item,
                                    onClick = { 
                                        currentNavItem = item
                                        scope.launch { drawerState.close() }
                                    },
                                    icon = { Icon(imageVector = item.icon, contentDescription = null) },
                                    modifier = Modifier.padding(vertical = 2.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.weight(1f))
                        androidx.compose.material3.HorizontalDivider(modifier = Modifier.padding(vertical = 8.dp))
                        NavigationDrawerItem(
                            label = { Text("Logout", color = androidx.compose.material3.MaterialTheme.colorScheme.error) },
                            selected = false,
                            onClick = {
                                scope.launch { drawerState.close() }
                                loginViewModel.logout()
                                ProfileStatsStore.reset()
                                isLoggedIn = false
                                currentNavItem = AppNavigationItem.CommandCenter // Reset nav
                            },
                            modifier = Modifier.padding(bottom = 16.dp)
                        )
                    }
                }
            }
        ) {
            Scaffold(
                topBar = {
                    TopAppBar(
                        title = {
                            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                Text(text = state.blueprint.appName)
                            }
                        },
                        navigationIcon = {
                            IconButton(onClick = { scope.launch { drawerState.open() } }) {
                                Icon(Icons.Default.Menu, contentDescription = "Menu")
                            }
                        },
                        actions = {
                            val profileStats by ProfileStatsStore.stats.collectAsStateWithLifecycle()
                            TopBarAccountActions(
                                email = FirebaseAuth.getInstance().currentUser?.email ?: loginState.email,
                                roleLabel = state.selectedAccessLevel.displayName,
                                incidentsReported = profileStats.incidentsReported,
                                incidentsVoted = profileStats.incidentsVoted,
                                onLogout = {
                                    scope.launch { drawerState.close() }
                                    loginViewModel.logout()
                                    ProfileStatsStore.reset()
                                    isLoggedIn = false
                                    currentNavItem = AppNavigationItem.CommandCenter
                                }
                            )
                        }
                    )

                }
            ) { innerPadding ->
                Box(
                    modifier = Modifier
                        .padding(innerPadding)
                        .fillMaxSize()
                ) {
                    Column(modifier = Modifier.fillMaxSize()) {
                        when (currentNavItem.destination) {
                            EventFlowDestination.Overview -> {
                                if (state.selectedAccessLevel in listOf(AccessLevel.Admin, AccessLevel.ControlRoom)) {
                                    FoundationOverviewScreen(
                                        state = state,
                                        onNavigateToModelInsights = { currentNavItem = AppNavigationItem.ModelInsights },
                                        onNavigateToSubmitReport = { currentNavItem = AppNavigationItem.UserMode },
                                        onNavigateToMapIntelligence = { currentNavItem = AppNavigationItem.MapIntelligence }
                                    )
                                } else {
                                    AccessProtectedScreen("Command Center access is protected.")
                                }
                            }
                            EventFlowDestination.Auth -> AuthSessionScreen(state = state)
                            EventFlowDestination.Citizen -> CitizenExperienceScreen(
                                state = state,
                                onReportSuccess = {
                                    currentNavItem = AppNavigationItem.CommandCenter
                                }
                            )
                            EventFlowDestination.Officer -> {
                                if (state.selectedAccessLevel == AccessLevel.PoliceOfficer) {
                                    OfficerWorkspaceScreen(state = state)
                                } else {
                                    AccessProtectedScreen("Officer workspace is restricted to Police Officers only.")
                                }
                            }
                            EventFlowDestination.Map -> MapIntelligenceScreen(state = state)
                            EventFlowDestination.Explorer -> {
                                com.namangulati.sancharsarthi.feature.explorer.ExplorerScreen(state = state)
                            }
                            EventFlowDestination.ModelInsights -> {
                                if (state.selectedAccessLevel in listOf(AccessLevel.Admin, AccessLevel.ControlRoom)) {
                                    ModelInsightsScreen(appState = state)
                                } else {
                                    AccessProtectedScreen("Model Insights access is protected.")
                                }
                            }
                            EventFlowDestination.Admin -> {
                                if (state.selectedAccessLevel == AccessLevel.Admin) {
                                    com.namangulati.sancharsarthi.feature.admin.AdminScreen()
                                } else {
                                    AccessProtectedScreen("Admin access is protected.")
                                }
                            }
                            EventFlowDestination.ControlRoom -> {
                                if (state.selectedAccessLevel in listOf(AccessLevel.Admin, AccessLevel.ControlRoom)) {
                                    com.namangulati.sancharsarthi.feature.admin.ControlRoomScreen()
                                } else {
                                    AccessProtectedScreen("Control Room access is protected.")
                                }
                            }
                            EventFlowDestination.Simulation -> {
                                com.namangulati.sancharsarthi.feature.simulation.SimulationScreen(state = state)
                            }
                            EventFlowDestination.PostEventLearning -> {
                                com.namangulati.sancharsarthi.feature.learning.LearningScreen(state = state)
                            }
                        }
                    }
                    NammaSarthiAssistantOverlay(
                        state = ragAssistantState,
                        accessLevel = state.selectedAccessLevel,
                        onToggle = ragAssistantViewModel::togglePanel,
                        onClose = ragAssistantViewModel::closePanel,
                        onSend = { question -> ragAssistantViewModel.sendQuestion(question) },
                        onClear = ragAssistantViewModel::clearConversation,
                    )
                }
        }
    }
}
}


@Composable
private fun TopBarAccountActions(
    email: String,
    roleLabel: String,
    incidentsReported: Int,
    incidentsVoted: Int,
    onLogout: () -> Unit,
) {
    val currentLanguage by TranslationManager.currentLanguage.collectAsStateWithLifecycle()
    var languageExpanded by androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf(false) }
    var profileExpanded by androidx.compose.runtime.remember { androidx.compose.runtime.mutableStateOf(false) }
    val displayEmail = email.ifBlank { "Signed in" }
    val initial = displayEmail.firstOrNull { it.isLetterOrDigit() }?.uppercaseChar()?.toString() ?: "U"
    val languageLabel = if (currentLanguage == TranslateLanguage.KANNADA) "\u0C95\u0CA8\u0CCD\u0CA8\u0CA1" else "English"

    Row(
        modifier = Modifier.padding(end = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        // Language icon-only button (compact)
        Box {
            IconButton(
                onClick = { languageExpanded = true },
                modifier = Modifier.size(40.dp)
            ) {
                Icon(
                    Icons.Default.Language,
                    contentDescription = "Language",
                    tint = Color(0xFF1D2A44),
                    modifier = Modifier.size(22.dp)
                )
            }
            DropdownMenu(expanded = languageExpanded, onDismissRequest = { languageExpanded = false }) {
                DropdownMenuItem(
                    text = { Text("English") },
                    onClick = {
                        TranslationManager.setLanguage(TranslateLanguage.ENGLISH)
                        languageExpanded = false
                    }
                )
                DropdownMenuItem(
                    text = { Text("\u0C95\u0CA8\u0CCD\u0CA8\u0CA1 (Kannada)") },
                    onClick = {
                        TranslationManager.setLanguage(TranslateLanguage.KANNADA)
                        languageExpanded = false
                    }
                )
            }
        }

        // Avatar with role badge — profile dropdown shows full details
        Box {
            IconButton(onClick = { profileExpanded = true }, modifier = Modifier.size(44.dp)) {
                Box(
                    modifier = Modifier
                        .size(36.dp)
                        .clip(CircleShape)
                        .background(Color(0xFF0D64B8))
                        .border(2.dp, Color.White, CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Text(initial, color = Color.White, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                }
            }
            DropdownMenu(
                expanded = profileExpanded,
                onDismissRequest = { profileExpanded = false },
                modifier = Modifier.width(300.dp)
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text(displayEmail, color = Color(0xFF1D2A44), fontSize = 14.sp, fontWeight = FontWeight.Bold, maxLines = 2)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = roleLabel,
                        color = Color(0xFF1565C0),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                    HorizontalDivider(modifier = Modifier.padding(vertical = 14.dp), color = Color(0xFFD0D8E6))
                    ProfileMenuStatRow(label = "Incidents reported", value = incidentsReported)
                    Spacer(modifier = Modifier.height(12.dp))
                    ProfileMenuStatRow(label = "Incidents voted", value = incidentsVoted)
                    Spacer(modifier = Modifier.height(16.dp))
                    OutlinedButton(
                        onClick = {
                            profileExpanded = false
                            onLogout()
                        },
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(10.dp),
                        border = BorderStroke(1.dp, Color(0xFFFFB9C5)),
                        colors = ButtonDefaults.outlinedButtonColors(
                            containerColor = Color(0xFFFFF0F2),
                            contentColor = Color(0xFFE61B45)
                        )
                    ) {
                        Text("Logout", fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

@Composable
private fun ProfileMenuStatRow(label: String, value: Int) {
    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
        Text(label, color = Color(0xFF607089), fontSize = 16.sp)
        Text(value.toString(), color = Color(0xFF1D2A44), fontSize = 16.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
fun AccessProtectedScreen(message: String) {
    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally, 
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(32.dp)
        ) {
            Icon(
                imageVector = Icons.Outlined.Lock, 
                contentDescription = "Locked", 
                modifier = Modifier.size(64.dp), 
                tint = androidx.compose.material3.MaterialTheme.colorScheme.error
            )
            Text(
                text = message, 
                style = androidx.compose.material3.MaterialTheme.typography.headlineMedium, 
                fontWeight = FontWeight.Bold,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
            Text(
                text = "Sign in with an authorized account to access this section.", 
                color = Color.Gray,
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
        }
    }
}
