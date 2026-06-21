package com.namangulati.sancharsarthi.core.translation

import com.google.mlkit.common.model.DownloadConditions
import com.google.mlkit.nl.translate.TranslateLanguage
import com.google.mlkit.nl.translate.Translation
import com.google.mlkit.nl.translate.TranslatorOptions
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.tasks.await

object TranslationManager {
    private val _currentLanguage = MutableStateFlow(TranslateLanguage.ENGLISH)
    val currentLanguage: StateFlow<String> = _currentLanguage.asStateFlow()

    private val translationCache = mutableMapOf<Pair<String, String>, String>()

    fun setLanguage(targetLanguageCode: String) {
        if (_currentLanguage.value == targetLanguageCode) return
        _currentLanguage.value = targetLanguageCode
    }

    suspend fun translate(text: String, targetLanguage: String): String {
        if (targetLanguage == TranslateLanguage.ENGLISH || text.isBlank()) {
            return text
        }

        val cacheKey = Pair(text, targetLanguage)
        translationCache[cacheKey]?.let { return it }

        val options = TranslatorOptions.Builder()
            .setSourceLanguage(TranslateLanguage.ENGLISH)
            .setTargetLanguage(targetLanguage)
            .build()
        
        val translator = Translation.getClient(options)
        
        val conditions = DownloadConditions.Builder()
            .build() // Do not require Wifi for demo purposes, so it downloads instantly over cellular too

        return try {
            translator.downloadModelIfNeeded(conditions).await()
            val translatedText = translator.translate(text).await()
            translationCache[cacheKey] = translatedText
            translatedText
        } catch (e: Exception) {
            e.printStackTrace()
            text // Fallback to original text if download or translation fails
        }
    }
}
