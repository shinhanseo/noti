package com.hanseo.noti.ai.tokenizer

import java.io.Closeable

data class TokenizedText(
    val inputIds: IntArray,
    val attentionMask: IntArray,
)

class NativeSentencePieceTokenizer(
    modelPath: String,
    private val bosTokenId: Int = DEFAULT_BOS_TOKEN_ID,
    private val padTokenId: Int = DEFAULT_PAD_TOKEN_ID,
    private val eosTokenId: Int = DEFAULT_EOS_TOKEN_ID,
) : Closeable {

    private var nativeHandle: Long =
        nativeCreate(modelPath)

    init {
        check(nativeHandle != 0L) {
            "Failed to load SentencePiece model"
        }
    }

    @Synchronized
    fun tokenize(
        text: String,
        maxLength: Int = DEFAULT_MAX_LENGTH,
    ): TokenizedText {
        check(nativeHandle != 0L) {
            "SentencePiece tokenizer is closed"
        }

        require(maxLength >= 2) {
            "maxLength must fit BOS and EOS"
        }

        val pieces =
            nativeEncode(
                nativeHandle,
                text.toByteArray(Charsets.UTF_8),
            )

        val pieceCount =
            minOf(
                pieces.size,
                maxLength - SPECIAL_TOKEN_COUNT,
            )

        val inputIds =
            IntArray(maxLength) {
                padTokenId
            }

        val attentionMask =
            IntArray(maxLength)

        inputIds[0] = bosTokenId

        pieces.copyInto(
            destination = inputIds,
            destinationOffset = 1,
            startIndex = 0,
            endIndex = pieceCount,
        )

        inputIds[pieceCount + 1] =
            eosTokenId

        attentionMask.fill(
            element = 1,
            fromIndex = 0,
            toIndex = pieceCount + SPECIAL_TOKEN_COUNT,
        )

        return TokenizedText(
            inputIds = inputIds,
            attentionMask = attentionMask,
        )
    }

    @Synchronized
    override fun close() {
        if (nativeHandle != 0L) {
            nativeDestroy(nativeHandle)
            nativeHandle = 0L
        }
    }

    private external fun nativeCreate(
        modelPath: String,
    ): Long

    private external fun nativeEncode(
        handle: Long,
        textUtf8: ByteArray,
    ): IntArray

    private external fun nativeDestroy(
        handle: Long,
    )

    private companion object {
        const val DEFAULT_MAX_LENGTH = 64

        const val DEFAULT_BOS_TOKEN_ID = 2
        const val DEFAULT_PAD_TOKEN_ID = 0
        const val DEFAULT_EOS_TOKEN_ID = 1

        const val SPECIAL_TOKEN_COUNT = 2

        init {
            System.loadLibrary("noti_sentencepiece")
        }
    }
}