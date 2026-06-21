package com.namangulati.sancharsarthi.core.location

data class MapPolicy(
    val primaryProvider: String,
    val fallbackProvider: String,
    val honestyNotes: List<String>,
)

