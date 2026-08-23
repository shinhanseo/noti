package com.hanseo.noti.ai

import com.hanseo.noti.domain.importance.ImportanceInput
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceSettings
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class ImportanceDecisionCoordinatorTest {

    @Test
    fun reviewWithPositiveAiScore_becomesImportant() {
        val fakeAiClassifier =
            ActionabilityClassifier {
                ActionabilityResult(
                    label =
                        ActionabilityLabel.ATTENTION_WORTHY,
                    probabilities = mapOf(
                        ActionabilityLabel.GENERAL to
                            0.10f,
                        ActionabilityLabel.ATTENTION_WORTHY to
                            0.80f,
                        ActionabilityLabel.ACTION_REQUIRED to
                            0.10f
                    )
                )
            }

        val coordinator =
            ImportanceDecisionCoordinator(
                actionabilityClassifierProvider =
                    successfulProvider(
                        fakeAiClassifier
                    )
            )

        val decision =
            coordinator.evaluate(
                input = createReviewInput(),
                settings = ImportanceSettings(),
                evaluatedAtMillis = 1_000L
            )

        assertEquals(
            40,
            decision.importance.score
        )
        assertEquals(
            ImportanceLevel.IMPORTANT,
            decision.importance.level
        )
        assertNotNull(decision.aiPrediction)
        assertEquals(
            15,
            decision.aiPrediction?.scoreDelta
        )
    }

    @Test
    fun reviewWithNegativeAiScore_becomesGeneral() {
        val fakeAiClassifier =
            ActionabilityClassifier {
                ActionabilityResult(
                    label = ActionabilityLabel.GENERAL,
                    probabilities = mapOf(
                        ActionabilityLabel.GENERAL to
                            0.90f,
                        ActionabilityLabel.ATTENTION_WORTHY to
                            0.05f,
                        ActionabilityLabel.ACTION_REQUIRED to
                            0.05f
                    )
                )
            }

        val coordinator =
            ImportanceDecisionCoordinator(
                actionabilityClassifierProvider =
                    successfulProvider(
                        fakeAiClassifier
                    )
            )

        val decision =
            coordinator.evaluate(
                input = createReviewInput(),
                settings = ImportanceSettings(),
                evaluatedAtMillis = 2_000L
            )

        assertEquals(
            10,
            decision.importance.score
        )
        assertEquals(
            ImportanceLevel.GENERAL,
            decision.importance.level
        )
        assertNotNull(decision.aiPrediction)
        assertEquals(
            -15,
            decision.aiPrediction?.scoreDelta
        )
    }

    @Test
    fun importantResult_doesNotRunAi() {
        val failingProvider =
            ActionabilityClassifierProvider {
                error(
                    "IMPORTANT에서는 AI가 실행되면 안 됩니다"
                )
            }

        val coordinator =
            ImportanceDecisionCoordinator(
                actionabilityClassifierProvider =
                    failingProvider
            )

        val input =
            ImportanceInput(
                packageName = "com.example.app",
                title = "테스트",
                body = "내용",
                category = "alarm",
                isOngoing = false
            )

        val decision =
            coordinator.evaluate(
                input = input,
                settings = ImportanceSettings(),
                evaluatedAtMillis = 3_000L
            )

        assertEquals(
            40,
            decision.importance.score
        )
        assertEquals(
            ImportanceLevel.IMPORTANT,
            decision.importance.level
        )
        assertNull(decision.aiPrediction)
    }

    @Test
    fun modelLoadingFailure_keepsReviewResult() {
        val loadingError =
            IllegalStateException("모델 로딩 실패")

        val failingProvider =
            ActionabilityClassifierProvider {
                Result.failure(loadingError)
            }

        val coordinator =
            ImportanceDecisionCoordinator(
                actionabilityClassifierProvider =
                    failingProvider
            )

        val decision =
            coordinator.evaluate(
                input = createReviewInput(),
                settings = ImportanceSettings(),
                evaluatedAtMillis = 4_000L
            )

        assertEquals(
            25,
            decision.importance.score
        )
        assertEquals(
            ImportanceLevel.REVIEW,
            decision.importance.level
        )
        assertNull(decision.aiPrediction)
    }

    @Test
    fun inferenceFailure_keepsReviewResult() {
        val failingClassifier =
            ActionabilityClassifier {
                error("ONNX 추론 실패")
            }

        val coordinator =
            ImportanceDecisionCoordinator(
                actionabilityClassifierProvider =
                    successfulProvider(
                        failingClassifier
                    )
            )

        val decision =
            coordinator.evaluate(
                input = createReviewInput(),
                settings = ImportanceSettings(),
                evaluatedAtMillis = 5_000L
            )

        assertEquals(
            25,
            decision.importance.score
        )
        assertEquals(
            ImportanceLevel.REVIEW,
            decision.importance.level
        )
        assertNull(decision.aiPrediction)
    }

    private fun successfulProvider(
        classifier: ActionabilityClassifier
    ): ActionabilityClassifierProvider {
        return ActionabilityClassifierProvider {
            Result.success(classifier)
        }
    }

    private fun createReviewInput():
        ImportanceInput {
        return ImportanceInput(
            packageName = "com.example.app",
            title = "테스트",
            body = "내용",
            category = "event",
            isOngoing = false
        )
    }
}
