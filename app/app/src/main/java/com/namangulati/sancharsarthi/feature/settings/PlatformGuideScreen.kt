package com.namangulati.sancharsarthi.feature.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.unit.dp
import com.namangulati.sancharsarthi.design.BulletList
import com.namangulati.sancharsarthi.design.ChipRow
import com.namangulati.sancharsarthi.design.LabelValue
import com.namangulati.sancharsarthi.design.PlatformSectionCard
import com.namangulati.sancharsarthi.feature.foundation.PlatformFoundationUiState

@Composable
fun PlatformGuideScreen(
    state: PlatformFoundationUiState,
) {
    LazyColumn(
        contentPadding = PaddingValues(horizontal = 20.dp, vertical = 18.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        item {
            PlatformSectionCard(
                title = "Namespace and route alignment",
                subtitle = "Phase 22A keeps the Android app aligned to the real hybrid platform that exists today.",
            ) {
                LabelValue(label = "Namespace", value = state.blueprint.namespace)
                ChipRow(values = state.blueprint.webRoutes)
            }
        }
        items(state.blueprint.architectureLayers) { layer ->
            PlatformSectionCard(
                title = layer.title,
                subtitle = layer.reason,
            ) {
                ChipRow(values = layer.packages)
            }
        }
        item {
            PlatformSectionCard(
                title = "Current platform rules",
                subtitle = "These rules are product behavior, not optional implementation flavor.",
            ) {
                state.blueprint.platformRules.forEach { rule ->
                    LabelValue(label = rule.title, value = rule.detail)
                }
            }
        }
        items(state.blueprint.apiFamilies) { family ->
            PlatformSectionCard(
                title = family.path,
                subtitle = family.audience,
            ) {
                Text(text = family.note)
            }
        }
    }
}

