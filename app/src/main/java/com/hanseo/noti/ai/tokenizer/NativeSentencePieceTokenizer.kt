package com.hanseo.noti.ai.tokenizer

import java.io.Closeable

data class TokenizedText(
    val inputIds: IntArray,
    val attentionMask: IntArray,
)

class NativeSentencePieceTokenizer private constructor(
    private val bosTokenId: Int,
    private val eosTokenId: Int,
    private val padTokenId: Int,
) : Closeable {

    private var nativeHandle: Long = 0L

    constructor(
        modelPath: String,
        bosTokenId: Int = DEFAULT_BOS_TOKEN_ID,
        eosTokenId: Int = DEFAULT_EOS_TOKEN_ID,
        padTokenId: Int = DEFAULT_PAD_TOKEN_ID,
    ) : this(bosTokenId, eosTokenId, padTokenId) {
        nativeHandle = nativeCreate(modelPath)
        validateHandle()
    }

    constructor(
        modelBytes: ByteArray,
        bosTokenId: Int = DEFAULT_BOS_TOKEN_ID,
        eosTokenId: Int = DEFAULT_EOS_TOKEN_ID,
        padTokenId: Int = DEFAULT_PAD_TOKEN_ID,
    ) : this(bosTokenId, eosTokenId, padTokenId) {
        nativeHandle = nativeCreateFromSerialized(modelBytes)
        validateHandle()
    }

    private fun validateHandle() {
        check(nativeHandle != 0L) { "Failed to load SentencePiece model" }
    }

    @Synchronized
    fun tokenize(text: String, maxLength: Int = DEFAULT_MAX_LENGTH): TokenizedText {
        check(nativeHandle != 0L) { "SentencePiece tokenizer is closed" }
        require(maxLength >= 2) { "maxLength must fit BOS and EOS" }

        val pieces = nativeEncode(nativeHandle, text.toByteArray(Charsets.UTF_8))
        val pieceCount = minOf(pieces.size, maxLength - 2)
        val inputIds = IntArray(maxLength)
        val attentionMask = IntArray(maxLength)

        inputIds.fill(padTokenId)
        inputIds[0] = bosTokenId
        pieces.copyInto(
            destination = inputIds,
            destinationOffset = 1,
            startIndex = 0,
            endIndex = pieceCount,
        )
        inputIds[pieceCount + 1] = eosTokenId
        attentionMask.fill(1, fromIndex = 0, toIndex = pieceCount + 2)

        return TokenizedText(inputIds, attentionMask)
    }

    @Synchronized
    override fun close() {
        if (nativeHandle != 0L) {
            nativeDestroy(nativeHandle)
            nativeHandle = 0L
        }
    }

    private external fun nativeCreate(modelPath: String): Long
    private external fun nativeCreateFromSerialized(modelBytes: ByteArray): Long
    private external fun nativeEncode(handle: Long, textUtf8: ByteArray): IntArray
    private external fun nativeDestroy(handle: Long)

    private companion object {
        const val DEFAULT_MAX_LENGTH = 64
        const val DEFAULT_BOS_TOKEN_ID = 2
        const val DEFAULT_EOS_TOKEN_ID = 1
        const val DEFAULT_PAD_TOKEN_ID = 0

        init {
            System.loadLibrary("noti_sentencepiece")
        }
    }
}
