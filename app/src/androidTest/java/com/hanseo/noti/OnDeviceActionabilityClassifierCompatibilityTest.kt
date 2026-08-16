package com.hanseo.noti

import androidx.test.ext.junit.runners.AndroidJUnit4
import com.hanseo.noti.ai.ActionabilityLabel
import com.hanseo.noti.ai.OnDeviceActionabilityClassifier
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class OnDeviceActionabilityClassifierCompatibilityTest {

    @Test
    fun classify_matchesPythonGoldenCase() {
        OnDeviceActionabilityClassifier(MODEL_PATH, TOKENIZER_PATH).use { classifier ->
            val result = classifier.classify(NORMALIZED_TEXT)

            assertEquals(ActionabilityLabel.ATTENTION_WORTHY, result.label)
            EXPECTED_PROBABILITIES.forEach { (label, expected) ->
                val actual = requireNotNull(result.probabilities[label])
                assertTrue(
                    "$label expected=$expected actual=$actual",
                    kotlin.math.abs(expected - actual) < PROBABILITY_TOLERANCE,
                )
            }
        }
    }

    private companion object {
        const val MODEL_PATH =
            "/data/local/tmp/noti_embeddinggemma_actionability_v1_int8.tflite"
        const val TOKENIZER_PATH = "/data/local/tmp/tokenizer.model"
        const val NORMALIZED_TEXT =
            "배송 출발 주문하신 상품이 오늘 오후 도착할 예정입니다."
        const val PROBABILITY_TOLERANCE = 0.0001f

        val EXPECTED_PROBABILITIES = mapOf(
            ActionabilityLabel.GENERAL to 0.00046770604f,
            ActionabilityLabel.ATTENTION_WORTHY to 0.9988201f,
            ActionabilityLabel.ACTION_REQUIRED to 0.0007121688f,
        )
    }
}
