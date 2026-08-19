package com.hanseo.noti

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.hanseo.noti.ai.ActionabilityLabel
import com.hanseo.noti.ai.KoenE5ActionabilityClassifier
import com.hanseo.noti.ai.KoenE5AssetLoader
import kotlin.math.abs
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class KoenE5ActionabilityClassifierCompatibilityTest {

    @Test
    fun classify_matchesPythonGoldenCase() {
        val context =
            InstrumentationRegistry
                .getInstrumentation()
                .targetContext

        val assets =
            KoenE5AssetLoader.load(context)

        KoenE5ActionabilityClassifier(
            modelBuffer = assets.modelBuffer,
            tokenizerModelPath =
                assets.tokenizerModelPath,
        ).use { classifier ->
            val result =
                classifier.classify(
                    NORMALIZED_TEXT
                )

            assertEquals(
                ActionabilityLabel.ATTENTION_WORTHY,
                result.label,
            )

            EXPECTED_PROBABILITIES.forEach {
                    (label, expected) ->

                val actual =
                    requireNotNull(
                        result.probabilities[label]
                    )

                assertTrue(
                    "$label expected=$expected actual=$actual",
                    abs(expected - actual) <
                            PROBABILITY_TOLERANCE,
                )
            }
        }
    }

    private companion object {
        const val NORMALIZED_TEXT =
            "배송 출발 주문하신 상품이 오늘 오후 도착할 예정입니다."

        const val PROBABILITY_TOLERANCE =
            0.0001f

        val EXPECTED_PROBABILITIES =
            mapOf(
                ActionabilityLabel.GENERAL to
                        0.00019517202f,

                ActionabilityLabel.ATTENTION_WORTHY to
                        0.99963725f,

                ActionabilityLabel.ACTION_REQUIRED to
                        0.00016751648f,
            )
    }
}