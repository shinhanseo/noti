package com.hanseo.noti

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
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
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        OnDeviceActionabilityClassifier.fromAssets(context).use { classifier ->
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
        const val NORMALIZED_TEXT =
            "배송 출발 주문하신 상품이 오늘 오후 도착할 예정입니다."
        const val PROBABILITY_TOLERANCE = 0.0001f

        val EXPECTED_PROBABILITIES = mapOf(
            ActionabilityLabel.GENERAL to 0.00019517202f,
            ActionabilityLabel.ATTENTION_WORTHY to 0.99963725f,
            ActionabilityLabel.ACTION_REQUIRED to 0.00016751648f,
        )
    }
}
