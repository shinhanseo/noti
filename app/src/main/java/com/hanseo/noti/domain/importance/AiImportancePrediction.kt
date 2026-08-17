package com.hanseo.noti.domain.importance

enum class AiImportanceLabel {
    GENERAL,
    ATTENTION_WORTHY,
    ACTION_REQUIRED
}

data class AiImportancePrediction(
    val label: AiImportanceLabel,
    val importantProbability: Float,
    val scoreDelta: Int,
    val modelVersion: String,
    val evaluatedAtMillis: Long
) {
    init {
        require(importantProbability in 0f..1f) {
            "importantProbability must be between 0.0 and 1.0"
        }

        require(scoreDelta in VALID_SCORE_DELTAS) {
            "scoreDelta must follow the AI importance score policy"
        }

        require(modelVersion.isNotBlank()) {
            "modelVersion must not be blank"
        }
    }

    private companion object {
        val VALID_SCORE_DELTAS = setOf(
            -15,
            -10,
            0,
            10,
            15
        )
    }
}