package com.namangulati.sancharsarthi.core.sync

data class OfflinePolicy(
    val citizenQueueEnabled: Boolean,
    val officerQueueEnabled: Boolean,
    val notes: List<String>,
)

