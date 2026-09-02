package com.hanseo.noti.ai

import com.hanseo.noti.domain.importance.ImportanceInput
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceReasonType
import com.hanseo.noti.domain.importance.ImportanceSettings
import com.hanseo.noti.domain.personalization.PersonalizationProfile
import com.hanseo.noti.domain.personalization.PersonalizationProfileProvider
import com.hanseo.noti.domain.personalization.PersonalizationScope
import com.hanseo.noti.domain.personalization.PersonalizationScoreCalculator
import com.hanseo.noti.domain.topic.NotificationTopic
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ImportanceDecisionCoordinatorTest {

    @Test
    fun forcedImportantApp_skipsPersonalizationAndAi() = runBlocking {
        val coordinator = createCoordinator(
            aiProvider = ActionabilityClassifierProvider {
                error("강제 판정에서는 AI가 실행되면 안 됩니다")
            },
            personalizationProvider =
                PersonalizationProfileProvider { _, _, _ ->
                    error("강제 판정에서는 개인화를 조회하면 안 됩니다")
                }
        )

        val decision = coordinator.evaluate(
            input = ImportanceInput(
                packageName = "com.example.shopping",
                title = "배송 안내",
                body = "주문한 상품의 배송이 출발했습니다",
                category = null,
                isOngoing = false
            ),
            settings = ImportanceSettings(
                importantApps = setOf("com.example.shopping")
            ),
            evaluatedAtMillis = 500L
        )

        assertEquals(100, decision.importance.score)
        assertEquals(ImportanceLevel.IMPORTANT, decision.importance.level)
        assertTrue(decision.importance.isForced)
        assertNull(decision.aiPrediction)
        assertEquals(0, decision.personalizationAdjustment.scoreDelta)
        assertEquals(
            NotificationTopic.DELIVERY,
            decision.topicResult.primaryTopic
        )
    }

    @Test
    fun firstImportantFeedback_changesActualScoreImmediately() =
        runBlocking {
            val coordinator = createCoordinator(
                aiProvider = ActionabilityClassifierProvider {
                    error("GENERAL에서는 AI가 실행되면 안 됩니다")
                },
                personalizationProvider = providerOf(
                    personalizationProfile(
                        topic = NotificationTopic.DELIVERY,
                        channelId = "delivery",
                        importantCount = 1,
                        generalCount = 0
                    )
                )
            )

            val decision = coordinator.evaluate(
                input = ImportanceInput(
                    packageName = "com.example.shopping",
                    title = "배송 안내",
                    body = "주문한 상품의 배송이 출발했습니다",
                    category = null,
                    isOngoing = false,
                    channelId = "delivery"
                ),
                settings = ImportanceSettings(),
                evaluatedAtMillis = 750L
            )

            assertEquals(15, decision.importance.score)
            assertEquals(ImportanceLevel.GENERAL, decision.importance.level)
            assertEquals(5, decision.personalizationAdjustment.scoreDelta)
            assertEquals(
                ImportanceReasonType.USER_FEEDBACK,
                decision.importance.reasons.last().type
            )
            assertEquals(5, decision.importance.reasons.last().scoreDelta)
            assertNull(decision.aiPrediction)
        }

    @Test
    fun generalFeedback_movesReviewToGeneralAndSkipsAi() = runBlocking {
        val coordinator = createCoordinator(
            aiProvider = ActionabilityClassifierProvider {
                error("개인화 후 GENERAL이면 AI가 실행되면 안 됩니다")
            },
            personalizationProvider = providerOf(
                personalizationProfile(
                    packageName = "com.example.app",
                    topic = NotificationTopic.SCHEDULE,
                    channelId = "schedule",
                    importantCount = 0,
                    generalCount = 1
                )
            )
        )

        val decision = coordinator.evaluate(
            input = createReviewInput(channelId = "schedule"),
            settings = ImportanceSettings(),
            evaluatedAtMillis = 900L
        )

        assertEquals(20, decision.importance.score)
        assertEquals(ImportanceLevel.GENERAL, decision.importance.level)
        assertEquals(-5, decision.personalizationAdjustment.scoreDelta)
        assertNull(decision.aiPrediction)
    }

    @Test
    fun reviewWithPositiveAiScore_becomesImportant() = runBlocking {
        val coordinator = createCoordinator(
            aiProvider = successfulProvider(
                classifier(
                    general = 0.10f,
                    attention = 0.80f,
                    action = 0.10f
                )
            )
        )

        val decision = coordinator.evaluate(
            input = createReviewInput(),
            settings = ImportanceSettings(),
            evaluatedAtMillis = 1_000L
        )

        assertEquals(40, decision.importance.score)
        assertEquals(ImportanceLevel.IMPORTANT, decision.importance.level)
        assertNotNull(decision.aiPrediction)
        assertEquals(15, decision.aiPrediction?.scoreDelta)
        assertEquals(0, decision.personalizationAdjustment.scoreDelta)
    }

    @Test
    fun reviewWithNegativeAiScore_becomesGeneral() = runBlocking {
        val coordinator = createCoordinator(
            aiProvider = successfulProvider(
                classifier(
                    general = 0.90f,
                    attention = 0.05f,
                    action = 0.05f
                )
            )
        )

        val decision = coordinator.evaluate(
            input = createReviewInput(),
            settings = ImportanceSettings(),
            evaluatedAtMillis = 2_000L
        )

        assertEquals(10, decision.importance.score)
        assertEquals(ImportanceLevel.GENERAL, decision.importance.level)
        assertNotNull(decision.aiPrediction)
        assertEquals(-15, decision.aiPrediction?.scoreDelta)
    }

    @Test
    fun importantResult_doesNotRunAi() = runBlocking {
        val coordinator = createCoordinator(
            aiProvider = ActionabilityClassifierProvider {
                error("IMPORTANT에서는 AI가 실행되면 안 됩니다")
            }
        )

        val decision = coordinator.evaluate(
            input = ImportanceInput(
                packageName = "com.example.app",
                title = "테스트",
                body = "내용",
                category = "alarm",
                isOngoing = false
            ),
            settings = ImportanceSettings(),
            evaluatedAtMillis = 3_000L
        )

        assertEquals(40, decision.importance.score)
        assertEquals(ImportanceLevel.IMPORTANT, decision.importance.level)
        assertNull(decision.aiPrediction)
    }

    @Test
    fun modelLoadingFailure_keepsReviewResult() = runBlocking {
        val coordinator = createCoordinator(
            aiProvider = ActionabilityClassifierProvider {
                Result.failure(IllegalStateException("모델 로딩 실패"))
            }
        )

        val decision = coordinator.evaluate(
            input = createReviewInput(),
            settings = ImportanceSettings(),
            evaluatedAtMillis = 4_000L
        )

        assertEquals(25, decision.importance.score)
        assertEquals(ImportanceLevel.REVIEW, decision.importance.level)
        assertNull(decision.aiPrediction)
    }

    @Test
    fun inferenceFailure_keepsReviewResult() = runBlocking {
        val coordinator = createCoordinator(
            aiProvider = successfulProvider(
                ActionabilityClassifier {
                    error("ONNX 추론 실패")
                }
            )
        )

        val decision = coordinator.evaluate(
            input = createReviewInput(),
            settings = ImportanceSettings(),
            evaluatedAtMillis = 5_000L
        )

        assertEquals(25, decision.importance.score)
        assertEquals(ImportanceLevel.REVIEW, decision.importance.level)
        assertNull(decision.aiPrediction)
    }

    @Test
    fun personalizationFailure_keepsBaseAndContinuesAi() = runBlocking {
        val coordinator = createCoordinator(
            aiProvider = successfulProvider(
                classifier(
                    general = 0.10f,
                    attention = 0.80f,
                    action = 0.10f
                )
            ),
            personalizationProvider =
                PersonalizationProfileProvider { _, _, _ ->
                    error("Room 조회 실패")
                }
        )

        val decision = coordinator.evaluate(
            input = createReviewInput(),
            settings = ImportanceSettings(),
            evaluatedAtMillis = 6_000L
        )

        assertEquals(40, decision.importance.score)
        assertEquals(0, decision.personalizationAdjustment.scoreDelta)
        assertNotNull(decision.aiPrediction)
    }

    private fun createCoordinator(
        aiProvider: ActionabilityClassifierProvider,
        personalizationProvider: PersonalizationProfileProvider =
            providerOf()
    ): ImportanceDecisionCoordinator {
        return ImportanceDecisionCoordinator(
            actionabilityClassifierProvider = aiProvider,
            personalizationProfileProvider = personalizationProvider,
            personalizationScoreCalculator =
                PersonalizationScoreCalculator()
        )
    }

    private fun providerOf(
        vararg profiles: PersonalizationProfile
    ): PersonalizationProfileProvider {
        return PersonalizationProfileProvider { _, _, _ ->
            profiles.toList()
        }
    }

    private fun successfulProvider(
        classifier: ActionabilityClassifier
    ): ActionabilityClassifierProvider {
        return ActionabilityClassifierProvider {
            Result.success(classifier)
        }
    }

    private fun classifier(
        general: Float,
        attention: Float,
        action: Float
    ): ActionabilityClassifier {
        return ActionabilityClassifier {
            ActionabilityResult(
                label = if (general >= attention && general >= action) {
                    ActionabilityLabel.GENERAL
                } else {
                    ActionabilityLabel.ATTENTION_WORTHY
                },
                probabilities = mapOf(
                    ActionabilityLabel.GENERAL to general,
                    ActionabilityLabel.ATTENTION_WORTHY to attention,
                    ActionabilityLabel.ACTION_REQUIRED to action
                )
            )
        }
    }

    private fun createReviewInput(
        channelId: String? = null
    ): ImportanceInput {
        return ImportanceInput(
            packageName = "com.example.app",
            title = "테스트",
            body = "내용",
            category = "event",
            isOngoing = false,
            channelId = channelId
        )
    }

    private fun personalizationProfile(
        packageName: String = "com.example.shopping",
        topic: NotificationTopic,
        channelId: String,
        importantCount: Int,
        generalCount: Int
    ): PersonalizationProfile {
        return PersonalizationProfile(
            scope = PersonalizationScope.APP_CHANNEL_TOPIC,
            packageName = packageName,
            channelId = channelId,
            topic = topic,
            importantCount = importantCount,
            generalCount = generalCount,
            profileVersion = "1"
        )
    }
}
