package com.hanseo.noti.ai

import com.hanseo.noti.domain.importance.AiImportancePrediction
import com.hanseo.noti.domain.importance.ImportanceClassifier
import com.hanseo.noti.domain.importance.ImportanceInput
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceResult
import com.hanseo.noti.domain.importance.ImportanceSettings
import com.hanseo.noti.domain.importance.ImportanceTextPreprocessor
import javax.inject.Inject

data class ImportanceDecision(
    val importance: ImportanceResult,
    val aiPrediction: AiImportancePrediction?
)

class ImportanceDecisionCoordinator
@Inject constructor(
    private val actionabilityClassifierProvider:
        ActionabilityClassifierProvider
) {

    private val importanceClassifier =
        ImportanceClassifier()

    private val predictionMapper =
        ActionabilityPredictionMapper()

    fun evaluate(
        input: ImportanceInput,
        settings: ImportanceSettings,
        evaluatedAtMillis: Long = System.currentTimeMillis()
    ): ImportanceDecision {
        val baseResult =
            importanceClassifier.classify(
                input = input,
                settings = settings,
                evaluatedAtMillis = evaluatedAtMillis
            )

        if (
            baseResult.isForced ||
            baseResult.level != ImportanceLevel.REVIEW
        ) {
            return ImportanceDecision(
                importance = baseResult,
                aiPrediction = null
            )
        }

        val normalizedText =
            ImportanceTextPreprocessor.normalize(input)

        if (normalizedText.isBlank()) {
            return ImportanceDecision(
                importance = baseResult,
                aiPrediction = null
            )
        }

        val aiPrediction =
            runCatching {
                val actionabilityClassifier =
                    actionabilityClassifierProvider
                        .get()
                        .getOrThrow()

                val actionabilityResult =
                    actionabilityClassifier.classify(
                        normalizedText = normalizedText
                    )

                predictionMapper.map(
                    result = actionabilityResult,
                    evaluatedAtMillis = evaluatedAtMillis
                )
            }.getOrElse {
                return ImportanceDecision(
                    importance = baseResult,
                    aiPrediction = null
                )
            }

        val finalScore =
            (
                    baseResult.score +
                            aiPrediction.scoreDelta
                    ).coerceIn(
                    minimumValue = -100,
                    maximumValue = 100
                )

        val finalImportance =
            baseResult.copy(
                score = finalScore,
                level = convertScoreToLevel(finalScore)
            )

        return ImportanceDecision(
            importance = finalImportance,
            aiPrediction = aiPrediction
        )
    }

    private fun convertScoreToLevel(
        score: Int
    ): ImportanceLevel {
        return when {
            score >= 40 ->
                ImportanceLevel.IMPORTANT

            score >= 25 ->
                ImportanceLevel.REVIEW

            else ->
                ImportanceLevel.GENERAL
        }
    }
}
