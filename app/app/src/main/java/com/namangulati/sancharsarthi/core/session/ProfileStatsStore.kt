package com.namangulati.sancharsarthi.core.session

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

data class ProfileStats(
    val incidentsReported: Int = 0,
    val incidentsVoted: Int = 0,
)

object ProfileStatsStore {
    private val _stats = MutableStateFlow(ProfileStats())
    val stats = _stats.asStateFlow()

    fun recordIncidentReported() {
        _stats.update { it.copy(incidentsReported = it.incidentsReported + 1) }
    }

    fun recordIncidentVoted() {
        _stats.update { it.copy(incidentsVoted = it.incidentsVoted + 1) }
    }

    fun reset() {
        _stats.value = ProfileStats()
    }
}
