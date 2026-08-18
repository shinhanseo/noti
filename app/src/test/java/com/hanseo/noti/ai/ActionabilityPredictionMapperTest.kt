package com.hanseo.noti.ai

import com.hanseo.noti.domain.importance.AiImportanceLabel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class ActionabilityPredictionMapperTest {

    private val mapper =
        ActionabilityPredictionMapper()

    @Test
    fun map_combinesAttentionAndActionProbabilities() {
        val result = ActionabilityResult(
            label = ActionabilityLabel.ATTENTION_WORTHY,
            probabilities = mapOf(
                ActionabilityLabel.GENERAL to 0.10f,
                ActionabilityLabel.ATTENTION_WORTHY to 0.70f,
                ActionabilityLabel.ACTION_REQUIRED to 0.20f
            )
        )

        val prediction = mapper.map(
            result = result,
            evaluatedAtMillis = 1_000L
        )

        assertEquals(
            AiImportanceLabel.ATTENTION_WORTHY,
            prediction.label
        )
        assertEquals(
            0.90f,
            prediction.importantProbability,
            0.0001f
        )
        assertEquals(15, prediction.scoreDelta)
        assertEquals(
            "noti_koen_e5_tiny_actionability_v1",
            prediction.modelVersion
        )
        assertEquals(
            1_000L,
            prediction.evaluatedAtMillis
        )
    }

    @Test
    fun map_probabilityAtSixtyFivePercent_returnsTen() {
        val result = ActionabilityResult(
            label = ActionabilityLabel.ACTION_REQUIRED,
            probabilities = mapOf(
                ActionabilityLabel.GENERAL to 0.35f,
                ActionabilityLabel.ATTENTION_WORTHY to 0.25f,
                ActionabilityLabel.ACTION_REQUIRED to 0.40f
            )
        )

        val prediction = mapper.map(result)

        assertEquals(
            0.65f,
            prediction.importantProbability,
            0.0001f
        )
        assertEquals(10, prediction.scoreDelta)
    }

    @Test
    fun map_missingActionProbability_throwsException() {
        val result = ActionabilityResult(
            label = ActionabilityLabel.GENERAL,
            probabilities = mapOf(
                ActionabilityLabel.GENERAL to 0.80f,
                ActionabilityLabel.ATTENTION_WORTHY to 0.20f
            )
        )

        assertThrows(IllegalArgumentException::class.java) {
            mapper.map(result)
        }
    }
}
