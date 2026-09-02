package com.hanseo.noti.ai

import com.hanseo.noti.domain.importance.AiImportancePrediction
import com.hanseo.noti.domain.importance.ImportanceClassifier
import com.hanseo.noti.domain.importance.ImportanceInput
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceReason
import com.hanseo.noti.domain.importance.ImportanceReasonType
import com.hanseo.noti.domain.importance.ImportanceResult
import com.hanseo.noti.domain.importance.ImportanceSettings
import com.hanseo.noti.domain.importance.ImportanceTextPreprocessor
import com.hanseo.noti.domain.personalization.PersonalizationAdjustment
import com.hanseo.noti.domain.personalization.PersonalizationProfileProvider
import com.hanseo.noti.domain.personalization.PersonalizationScoreCalculator
import com.hanseo.noti.domain.topic.NotificationTopicExtractor
import com.hanseo.noti.domain.topic.NotificationTopicResult
import javax.inject.Inject
import kotlinx.coroutines.CancellationException

data class ImportanceDecision(
    val importance: ImportanceResult,
    val aiPrediction: AiImportancePrediction?,
    val personalizationAdjustment:
    PersonalizationAdjustment,
    val topicResult: NotificationTopicResult
)

class ImportanceDecisionCoordinator
@Inject constructor(
    private val actionabilityClassifierProvider:
    ActionabilityClassifierProvider,

    private val personalizationProfileProvider:
    PersonalizationProfileProvider,

    private val personalizationScoreCalculator:
    PersonalizationScoreCalculator
) {

    private val importanceClassifier =
        ImportanceClassifier()

    private val predictionMapper =
        ActionabilityPredictionMapper()

    private val topicExtractor =
        NotificationTopicExtractor()

    suspend fun evaluate(
        input: ImportanceInput,
        settings: ImportanceSettings,
        evaluatedAtMillis: Long =
            System.currentTimeMillis()
    ): ImportanceDecision {
        val classification =
            importanceClassifier.analyze(
                input = input,
                settings = settings,
                evaluatedAtMillis = evaluatedAtMillis
            )

        val baseResult =
            classification.result

        val topicResult =
            topicExtractor.extract(
                reasons =
                    classification.automaticReasons
            )

        /*
         * 중요 앱, 중요 키워드, 제외 키워드처럼
         * 사용자가 직접 만든 강제 설정은
         * 개인화와 AI가 변경하지 않는다.
         */
        if (baseResult.isForced) {
            return ImportanceDecision(
                importance = baseResult,
                aiPrediction = null,
                personalizationAdjustment =
                    PersonalizationAdjustment.none(),
                topicResult = topicResult
            )
        }

        val personalizationAdjustment =
            calculatePersonalization(
                input = input,
                topicResult = topicResult
            )

        val personalizedResult =
            applyPersonalization(
                baseResult = baseResult,
                adjustment =
                    personalizationAdjustment
            )

        if (
            personalizedResult.level !=
            ImportanceLevel.REVIEW
        ) {
            return ImportanceDecision(
                importance = personalizedResult,
                aiPrediction = null,
                personalizationAdjustment =
                    personalizationAdjustment,
                topicResult = topicResult
            )
        }

        val normalizedText =
            ImportanceTextPreprocessor.normalize(input)

        if (normalizedText.isBlank()) {
            return ImportanceDecision(
                importance = personalizedResult,
                aiPrediction = null,
                personalizationAdjustment =
                    personalizationAdjustment,
                topicResult = topicResult
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
                    evaluatedAtMillis =
                        evaluatedAtMillis
                )
            }.getOrElse {
                return ImportanceDecision(
                    importance = personalizedResult,
                    aiPrediction = null,
                    personalizationAdjustment =
                        personalizationAdjustment,
                    topicResult = topicResult
                )
            }

        val finalScore =
            (
                    personalizedResult.score +
                            aiPrediction.scoreDelta
                    ).coerceIn(
                    minimumValue = -100,
                    maximumValue = 100
                )

        val finalImportance =
            personalizedResult.copy(
                score = finalScore,
                level = convertScoreToLevel(
                    finalScore
                )
            )

        return ImportanceDecision(
            importance = finalImportance,
            aiPrediction = aiPrediction,
            personalizationAdjustment =
                personalizationAdjustment,
            topicResult = topicResult
        )
    }

    private suspend fun calculatePersonalization(
        input: ImportanceInput,
        topicResult: NotificationTopicResult
    ): PersonalizationAdjustment {
        return try {
            val profiles =
                personalizationProfileProvider
                    .findMatchingProfiles(
                        packageName =
                            input.packageName,
                        channelId =
                            input.channelId,
                        topic =
                            topicResult.primaryTopic
                    )

            personalizationScoreCalculator
                .calculate(profiles)

        } catch (error: CancellationException) {
            throw error

        } catch (error: Exception) {
            /*
             * 개인화 조회 실패가 알림 수집 실패로
             * 이어지지 않도록 개인화만 생략한다.
             */
            PersonalizationAdjustment.none()
        }
    }

    private fun applyPersonalization(
        baseResult: ImportanceResult,
        adjustment: PersonalizationAdjustment
    ): ImportanceResult {
        if (!adjustment.isApplied) {
            return baseResult
        }

        val personalizedScore =
            (
                    baseResult.score +
                            adjustment.scoreDelta
                    ).coerceIn(
                    minimumValue = -100,
                    maximumValue = 100
                )

        val personalizationReason =
            ImportanceReason(
                type =
                    ImportanceReasonType.USER_FEEDBACK,

                scoreDelta =
                    adjustment.scoreDelta,

                ruleId =
                    adjustment.matchedScope
                        ?.name
                        ?.lowercase()
                        ?.let { scope ->
                            "personalization_$scope"
                        },

                description =
                    if (adjustment.scoreDelta > 0) {
                        "비슷한 알림을 중요하게 본 기록을 반영했어요"
                    } else {
                        "비슷한 알림을 덜 중요하게 본 기록을 반영했어요"
                    }
            )

        return baseResult.copy(
            score = personalizedScore,
            level = convertScoreToLevel(
                personalizedScore
            ),
            reasons =
                baseResult.reasons +
                        personalizationReason
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