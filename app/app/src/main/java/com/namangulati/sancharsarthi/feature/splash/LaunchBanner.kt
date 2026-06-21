package com.namangulati.sancharsarthi.feature.splash

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import com.namangulati.sancharsarthi.core.translation.AutoTranslatedText
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.namangulati.sancharsarthi.design.MetricStrip
import com.namangulati.sancharsarthi.design.PlatformSectionCard

@Composable
fun LaunchBanner(
    title: String,
    subtitle: String,
    landingLabel: String,
    metricPairs: List<Pair<String, String>>,
) {
    PlatformSectionCard(
        title = title,
        subtitle = subtitle,
    ) {
        Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
            AutoTranslatedText(
                text = landingLabel,
                style = MaterialTheme.typography.bodyLarge,
                fontWeight = FontWeight.Medium,
            )
            MetricStrip(metricPairs)
        }
    }
}


