package com.namangulati.sancharsarthi.feature.auth

import androidx.compose.runtime.Composable
import com.namangulati.sancharsarthi.core.auth.AuthAuthority
import com.namangulati.sancharsarthi.design.BulletList
import com.namangulati.sancharsarthi.design.LabelValue
import com.namangulati.sancharsarthi.design.PlatformSectionCard

@Composable
fun AuthBoundaryCard(authority: AuthAuthority) {
    PlatformSectionCard(
        title = "Authority boundary",
        subtitle = "Firebase gets users in. FastAPI still decides what they can actually do.",
    ) {
        LabelValue(label = "Identity provider", value = authority.identityProvider)
        LabelValue(label = "Final authority", value = authority.finalAuthority)
        BulletList(items = authority.notes)
    }
}

