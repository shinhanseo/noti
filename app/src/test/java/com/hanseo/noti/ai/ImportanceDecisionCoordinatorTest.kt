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
                actionabilityClassifier =
                    fakeAiClassifier
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
                actionabilityClassifier =
                    fakeAiClassifier
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
        val fakeAiClassifier =
            ActionabilityClassifier {
                error(
                    "IMPORTANT에서는 AI가 실행되면 안 됩니다"
                )
            }

        val coordinator =
            ImportanceDecisionCoordinator(
                actionabilityClassifier =
                    fakeAiClassifier
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
