package com.namangulati.sancharsarthi.data.repository

import com.namangulati.sancharsarthi.data.local.PlatformBlueprintLocalDataSource
import com.namangulati.sancharsarthi.domain.model.PlatformBlueprint

interface PlatformBlueprintRepository {
    fun getBlueprint(): PlatformBlueprint
}

class DefaultPlatformBlueprintRepository(
    private val localDataSource: PlatformBlueprintLocalDataSource = PlatformBlueprintLocalDataSource(),
) : PlatformBlueprintRepository {
    override fun getBlueprint(): PlatformBlueprint = localDataSource.load()
}

