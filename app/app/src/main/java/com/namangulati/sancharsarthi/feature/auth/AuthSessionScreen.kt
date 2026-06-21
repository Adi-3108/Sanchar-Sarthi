package com.namangulati.sancharsarthi.feature.auth

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp
import com.namangulati.sancharsarthi.core.auth.AuthBootstrapRoute
import com.namangulati.sancharsarthi.core.session.SessionBootstrapResult
import com.namangulati.sancharsarthi.design.BulletList
import com.namangulati.sancharsarthi.design.ChipRow
import com.namangulati.sancharsarthi.design.LabelValue
import com.namangulati.sancharsarthi.design.PlatformSectionCard
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState

@Composable
fun AuthSessionScreen(
    state: PlatformFoundationUiState,
) {
    LazyColumn(
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            SessionPreviewCard(result = state.sessionBootstrapResult)
        }
        item {
            PlatformSectionCard(
                title = "Bootstrap rules",
                subtitle = "Firebase signs users in. FastAPI confirms role, officer profile, and scope.",
            ) {
                BulletList(items = state.blueprint.authBootstrapPolicy.rules)
            }
        }
        items(state.blueprint.authBootstrapPolicy.routes) { route ->
            BootstrapRouteCard(route = route)
        }
        item {
            PlatformSectionCard(
                title = "Handled auth states",
                subtitle = "Android keeps public-safe flows available while blocking unverified internal access.",
            ) {
                state.blueprint.authErrorStates.forEach { error ->
                    LabelValue(
                        label = error.kind.label,
                        value = "${error.userMessage} ${error.recoveryHint}",
                    )
                }
            }
        }
    }
}

@Composable
private fun SessionPreviewCard(result: SessionBootstrapResult) {
    when (result) {
        is SessionBootstrapResult.Authorized -> {
            PlatformSectionCard(
                title = "Backend-confirmed session",
                subtitle = result.landingLabel,
            ) {
                LabelValue(label = "Access level", value = result.session.accessLevel.displayName)
                LabelValue(label = "Backend role", value = result.session.backendRole ?: "guest")
                LabelValue(label = "Officer id", value = result.session.officerId ?: "not applicable")
                LabelValue(label = "Police station", value = result.session.policeStation ?: "not applicable")
                ChipRow(values = result.notes)
            }
        }
        is SessionBootstrapResult.Blocked -> {
            PlatformSectionCard(
                title = "Protected access blocked",
                subtitle = result.error.kind.label,
            ) {
                LabelValue(label = "Message", value = result.error.userMessage)
                LabelValue(label = "Recovery", value = result.error.recoveryHint)
                LabelValue(label = "Fallback", value = result.fallbackSession.accessLevel.displayName)
            }
        }
    }
}

@Composable
private fun BootstrapRouteCard(route: AuthBootstrapRoute) {
    PlatformSectionCard(
        title = route.accessLevel.displayName,
        subtitle = route.purpose,
    ) {
        LabelValue(label = "Route", value = route.path ?: "No backend bootstrap route required")
        LabelValue(label = "Method", value = route.method)
        LabelValue(label = "Firebase token", value = if (route.tokenRequired) "Required" else "Not required")
    }
}
