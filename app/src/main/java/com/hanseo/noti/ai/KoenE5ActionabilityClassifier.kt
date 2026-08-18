package com.hanseo.noti.ai

import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import com.hanseo.noti.ai.tokenizer.NativeSentencePieceTokenizer
import com.hanseo.noti.ai.tokenizer.TokenizedText
import java.io.Closeable
import ai.onnxruntime.OnnxTensor
import java.nio.LongBuffer

class KoenE5ActionabilityClassifier(
    modelPath: String,
    tokenizerModelPath: String,
    numberOfThreads: Int = DEFAULT_THREAD_COUNT,
) : Closeable {

    private val environment: OrtEnvironment =
        OrtEnvironment.getEnvironment()

    private val sessionOptions: OrtSession.SessionOptions =
        OrtSession.SessionOptions().apply {
            setIntraOpNumThreads(numberOfThreads)
        }

    private val session: OrtSession =
        environment.createSession(
            modelPath,
            sessionOptions,
        )

    private val tokenizer =
        NativeSentencePieceTokenizer(
            modelPath = tokenizerModelPath,
            bosTokenId = BOS_TOKEN_ID,
            padTokenId = PAD_TOKEN_ID,
            eosTokenId = EOS_TOKEN_ID,
        )

    private fun tokenize(
        normalizedText: String,
    ): TokenizedText {
        val classificationText =
            CLASSIFICATION_PREFIX +
                    normalizedText.trim()

        return tokenizer.tokenize(
            text = classificationText,
            maxLength = SEQUENCE_LENGTH,
        )
    }

    private fun createLongTensor(
        values: IntArray,
    ): OnnxTensor {
        require(values.size == SEQUENCE_LENGTH) {
            "Input size must be $SEQUENCE_LENGTH"
        }

        val longValues =
            LongArray(values.size) { index ->
                values[index].toLong()
            }

        val shape =
            longArrayOf(
                1L,
                values.size.toLong(),
            )

        return OnnxTensor.createTensor(
            environment,
            LongBuffer.wrap(longValues),
            shape,
        )
    }

    override fun close() {
        tokenizer.close()
        session.close()
        sessionOptions.close()
    }

    private companion object {
        const val DEFAULT_THREAD_COUNT = 4
        const val SEQUENCE_LENGTH = 64

        const val CLASSIFICATION_PREFIX =
            "query: "

        const val BOS_TOKEN_ID = 0
        const val PAD_TOKEN_ID = 1
        const val EOS_TOKEN_ID = 2
    }
}