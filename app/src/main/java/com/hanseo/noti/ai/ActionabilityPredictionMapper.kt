package com.hanseo.noti.ai

import com.hanseo.noti.domain.importance.AiImportanceLabel
import com.hanseo.noti.domain.importance.AiImportancePrediction
import com.hanseo.noti.domain.importance.AiImportanceScoreMapper

class ActionabilityPredictionMapper(
    private val scoreMapper: AiImportanceScoreMapper =
        AiImportanceScoreMapper()
) {

    fun map(
        result: ActionabilityResult,
        evaluatedAtMillis: Long = System.currentTimeMillis()
    ): AiImportancePrediction {
        val attentionWorthyProbability =
            requireNotNull(
                result.probabilities[
                    ActionabilityLabel.ATTENTION_WORTHY
                ]
            ) {
                "ATTENTION_WORTHY probability is missing"
            }

        val actionRequiredProbability =
            requireNotNull(
                result.probabilities[
                    ActionabilityLabel.ACTION_REQUIRED
                ]
            ) {
                "ACTION_REQUIRED probability is missing"
            }

        val importantProbability =
            (
                    attentionWorthyProbability +
                            actionRequiredProbability
                    ).coerceIn(0f, 1f)

        return AiImportancePrediction(
            label = result.label.toDomainLabel(),
            importantProbability = importantProbability,
            scoreDelta = scoreMapper.map(importantProbability),
            modelVersion = MODEL_VERSION,
            evaluatedAtMillis = evaluatedAtMillis
        )
    }

    private fun ActionabilityLabel.toDomainLabel():
            AiImportanceLabel {
        return when (this) {
            ActionabilityLabel.GENERAL ->
                AiImportanceLabel.GENERAL

            ActionabilityLabel.ATTENTION_WORTHY ->
                AiImportanceLabel.ATTENTION_WORTHY

            ActionabilityLabel.ACTION_REQUIRED ->
                AiImportanceLabel.ACTION_REQUIRED
        }
    }

    private companion object {
        const val MODEL_VERSION =
            "noti_koen_e5_tiny_actionability_v1_int8"
    }
}
