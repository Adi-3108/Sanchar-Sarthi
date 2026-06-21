package com.namangulati.sancharsarthi.feature.learning

import androidx.compose.runtime.Composable
import com.namangulati.sancharsarthi.design.BulletList
import com.namangulati.sancharsarthi.design.PlatformSectionCard

@Composable
fun LearningScopeCard() {
    PlatformSectionCard(
        title = "After-action learning stays dossier-based",
        subtitle = "Mobile should reuse event dossiers and post-event reports rather than inventing a new review model.",
    ) {
        BulletList(
            items = listOf(
                "Read GET /api/events/{event_id} for recap context.",
                "Trigger post-event report generation through FastAPI only.",
                "Keep recommendations, lessons, and hindsight explicitly dataset-backed or simulated.",
            ),
        )
    }
}

