package com.namangulati.sancharsarthi.core.translation

import androidx.compose.material3.LocalTextStyle
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.TextUnit
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun AutoTranslatedText(
    text: String,
    modifier: Modifier = Modifier,
    color: Color = Color.Unspecified,
    fontSize: TextUnit = TextUnit.Unspecified,
    fontWeight: FontWeight? = null,
    textAlign: TextAlign? = null,
    style: TextStyle = LocalTextStyle.current
) {
    val currentLanguage by TranslationManager.currentLanguage.collectAsStateWithLifecycle()
    var translatedText by remember(text, currentLanguage) { mutableStateOf(text) }

    LaunchedEffect(text, currentLanguage) {
        translatedText = TranslationManager.translate(text, currentLanguage)
    }

    Text(
        text = translatedText,
        modifier = modifier,
        color = color,
        fontSize = fontSize,
        fontWeight = fontWeight,
        textAlign = textAlign,
        style = style
    )
}
