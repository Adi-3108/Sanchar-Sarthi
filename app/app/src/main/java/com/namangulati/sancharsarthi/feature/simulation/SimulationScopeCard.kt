package com.namangulati.sancharsarthi.feature.simulation

import androidx.compose.runtime.Composable
import com.namangulati.sancharsarthi.design.BulletList
import com.namangulati.sancharsarthi.design.ChipRow
import com.namangulati.sancharsarthi.design.PlatformSectionCard

@Composable
fun SimulationScopeCard() {
    PlatformSectionCard(
        title = "Simulation and planning remain internal",
        subtitle = "Phase 22A only sets the product boundary. Actual simulation workflows come later.",
    ) {
        ChipRow(values = listOf("simulated", "estimated", "recommended"))
        BulletList(
            items = listOf(
                "Mirror POST /api/events/simulate and POST /api/recommendations/event-plan.",
                "Keep citizen-facing UX separate from internal planning surfaces.",
                "Do not overstate confidence beyond backend outputs.",
            ),
        )
    }
}

