package com.hanseo.noti

import androidx.test.ext.junit.runners.AndroidJUnit4
import com.hanseo.noti.ai.tokenizer.NativeSentencePieceTokenizer
import org.junit.Assert.assertArrayEquals
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NativeSentencePieceTokenizerCompatibilityTest {

    @Test
    fun tokenize_matchesEmbeddingGemmaPythonGoldenCase() {
        NativeSentencePieceTokenizer(TOKENIZER_DEVICE_PATH).use { tokenizer ->
            val result = tokenizer.tokenize(CLASSIFICATION_TEXT)

            assertArrayEquals(EXPECTED_INPUT_IDS, result.inputIds)
            assertArrayEquals(EXPECTED_ATTENTION_MASK, result.attentionMask)
        }
    }

    private companion object {
        const val TOKENIZER_DEVICE_PATH = "/data/local/tmp/tokenizer.model"
        const val CLASSIFICATION_TEXT =
            "task: classification | query: 배송 출발 주문하신 상품이 오늘 오후 도착할 예정입니다."

        val EXPECTED_INPUT_IDS = intArrayOf(
            2, 8071, 236787, 15241, 1109, 7609, 236787, 26440,
            239917, 172508, 132962, 148009, 104507, 237077, 31694, 133055,
            222715, 238221, 110942, 15245, 236761, 1,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
        )
        val EXPECTED_ATTENTION_MASK = intArrayOf(
            1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
            1, 1,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0,
        )
    }
}
