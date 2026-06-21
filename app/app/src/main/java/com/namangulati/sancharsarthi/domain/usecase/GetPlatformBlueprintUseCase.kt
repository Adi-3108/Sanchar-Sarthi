package com.namangulati.sancharsarthi.domain.usecase

import com.namangulati.sancharsarthi.data.repository.PlatformBlueprintRepository
import com.namangulati.sancharsarthi.domain.model.PlatformBlueprint

class GetPlatformBlueprintUseCase(
    private val repository: PlatformBlueprintRepository,
) {
    operator fun invoke(): PlatformBlueprint = repository.getBlueprint()
}

