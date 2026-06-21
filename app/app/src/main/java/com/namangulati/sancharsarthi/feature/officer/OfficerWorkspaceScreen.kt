package com.namangulati.sancharsarthi.feature.officer

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp
import com.namangulati.sancharsarthi.core.session.AccessLevel
import com.namangulati.sancharsarthi.design.BulletList
import com.namangulati.sancharsarthi.design.ChipRow
import com.namangulati.sancharsarthi.design.LabelValue
import com.namangulati.sancharsarthi.design.PlatformSectionCard
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState

@Composable
fun OfficerWorkspaceScreen(
    state: PlatformFoundationUiState,
) {
    val internalAreas = state.blueprint.mobileAreas.filter { area ->
        area.supportedAccessLevels.any { it == AccessLevel.PoliceOfficer || it == AccessLevel.ControlRoom || it == AccessLevel.Admin }
    }

    LazyColumn(
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            PlatformSectionCard(
                title = "Officer boundary",
                subtitle = "Field access depends on backend profile and assignment scope, not on mobile role labels alone.",
            ) {
                BulletList(
                    items = listOf(
                        "Require an active PoliceOfficerProfile.",
                        "Respect explicit event assignment, assigned corridor, assigned zone, or police-station match.",
                        "Keep live updates queueable offline without pretending they are already command-center state.",
                    ),
                )
            }
        }
        items(internalAreas) { area ->
            PlatformSectionCard(
                title = area.title,
                subtitle = area.currentSourceOfTruth,
            ) {
                LabelValue(label = "Primary access", value = area.primaryAccess.displayName)
                Text(text = area.summary)
                ChipRow(values = area.backendRoutes)
                BulletList(items = area.capabilities)
            }
        }
    }
}

