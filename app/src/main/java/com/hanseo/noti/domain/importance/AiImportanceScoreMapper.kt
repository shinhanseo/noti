package com.hanseo.noti.domain.importance

class AiImportanceScoreMapper {
    fun map(importantProbability: Float) : Int {
        require(importantProbability in 0f..1f) {
            "importantProbability must be between 0.0 and 1.0"
        }

        return when {
            importantProbability >= 0.80f -> 15
            importantProbability >= 0.65f -> 10
            importantProbability >= 0.35f -> 0
            importantProbability >= 0.20f -> -10
            else -> -15
        }
    }
}