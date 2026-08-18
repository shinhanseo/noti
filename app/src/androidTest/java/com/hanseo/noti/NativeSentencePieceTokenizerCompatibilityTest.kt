package com.hanseo.noti

import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.hanseo.noti.ai.OnDeviceActionabilityClassifier
import com.hanseo.noti.ai.tokenizer.NativeSentencePieceTokenizer
import org.junit.Assert.assertArrayEquals
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NativeSentencePieceTokenizerCompatibilityTest {

    @Test
    fun tokenize_matchesKoEnE5TinyPythonGoldenCase() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        val tokenizerBytes = context.assets
            .open(OnDeviceActionabilityClassifier.TOKENIZER_ASSET_PATH)
            .use { stream -> stream.readBytes() }
        NativeSentencePieceTokenizer(
            modelBytes = tokenizerBytes,
            bosTokenId = 0,
            eosTokenId = 2,
            padTokenId = 1,
        ).use { tokenizer ->
            val result = tokenizer.tokenize(CLASSIFICATION_TEXT)

            assertArrayEquals(EXPECTED_INPUT_IDS, result.inputIds)
            assertArrayEquals(EXPECTED_ATTENTION_MASK, result.attentionMask)
        }
    }

    private companion object {
        const val CLASSIFICATION_TEXT =
            "query: 배송 출발 주문하신 상품이 오늘 오후 도착할 예정입니다."

        val EXPECTED_INPUT_IDS = intArrayOf(
            0, 37, 832, 12, 27791, 26292, 20524, 21282,
            10396, 354, 14084, 17468, 25509, 1410, 23062, 2865,
            5, 2,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
        )
        val EXPECTED_ATTENTION_MASK = IntArray(64) { index ->
            if (index < 18) 1 else 0
        }
    }
}
