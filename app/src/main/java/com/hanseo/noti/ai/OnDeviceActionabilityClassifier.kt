package com.hanseo.noti.ai

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import android.content.Context
import com.hanseo.noti.ai.tokenizer.NativeSentencePieceTokenizer
import java.io.Closeable
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.LongBuffer
import java.nio.channels.FileChannel

enum class ActionabilityLabel {
    GENERAL,
    ATTENTION_WORTHY,
    ACTION_REQUIRED,
}

data class ActionabilityResult(
    val label: ActionabilityLabel,
    val probabilities: Map<ActionabilityLabel, Float>,
)

class OnDeviceActionabilityClassifier private constructor(
    private val runtime: Runtime,
    private val tokenizer: NativeSentencePieceTokenizer,
) : Closeable {

    private val environment = runtime.environment
    private val sessionOptions = runtime.sessionOptions
    private val session = runtime.session

    constructor(
        modelPath: String,
        tokenizerModelPath: String,
        numberOfThreads: Int = DEFAULT_THREAD_COUNT,
    ) : this(
        runtime = createRuntime(modelPath, numberOfThreads),
        tokenizer = createTokenizer(tokenizerModelPath),
    )

    @Synchronized
    fun classify(normalizedText: String): ActionabilityResult {
        val classificationText = CLASSIFICATION_PREFIX + normalizedText.trim()
        val tokenized = tokenizer.tokenize(classificationText, SEQUENCE_LENGTH)
        val inputIds = LongArray(SEQUENCE_LENGTH) { tokenized.inputIds[it].toLong() }
        val attentionMask = LongArray(SEQUENCE_LENGTH) {
            tokenized.attentionMask[it].toLong()
        }
        val tokenTypeIds = LongArray(SEQUENCE_LENGTH)
        val shape = longArrayOf(1, SEQUENCE_LENGTH.toLong())
        val output = OnnxTensor.createTensor(
            environment,
            LongBuffer.wrap(inputIds),
            shape,
        ).use { inputIdsTensor ->
            OnnxTensor.createTensor(
                environment,
                LongBuffer.wrap(attentionMask),
                shape,
            ).use { attentionMaskTensor ->
                OnnxTensor.createTensor(
                    environment,
                    LongBuffer.wrap(tokenTypeIds),
                    shape,
                ).use { tokenTypeIdsTensor ->
                    session.run(
                        mapOf(
                            INPUT_IDS to inputIdsTensor,
                            ATTENTION_MASK to attentionMaskTensor,
                            TOKEN_TYPE_IDS to tokenTypeIdsTensor,
                        )
                    ).use { result ->
                        @Suppress("UNCHECKED_CAST")
                        val probabilities = result[0].value as Array<FloatArray>
                        probabilities[0].copyOf()
                    }
                }
            }
        }

        val probabilities = ActionabilityLabel.entries
            .mapIndexed { index, label -> label to output[index] }
            .toMap()
        val label = probabilities.maxBy { it.value }.key

        return ActionabilityResult(label, probabilities)
    }

    @Synchronized
    override fun close() {
        session.close()
        sessionOptions.close()
        tokenizer.close()
    }

    companion object {
        const val MODEL_ASSET_PATH =
            "ai/noti_koen_e5_tiny_actionability_v1_int8.onnx"
        const val TOKENIZER_ASSET_PATH = "ai/tokenizer.model"

        fun fromAssets(
            context: Context,
            numberOfThreads: Int = DEFAULT_THREAD_COUNT,
        ): OnDeviceActionabilityClassifier {
            val modelBuffer = mapAsset(context, MODEL_ASSET_PATH)
            val tokenizerBytes = context.assets
                .open(TOKENIZER_ASSET_PATH)
                .use { stream -> stream.readBytes() }
            return OnDeviceActionabilityClassifier(
                runtime = createRuntime(modelBuffer, numberOfThreads),
                tokenizer = createTokenizer(tokenizerBytes),
            )
        }

        private fun mapAsset(context: Context, path: String): ByteBuffer {
            return context.assets.openFd(path).use { descriptor ->
                FileInputStream(descriptor.fileDescriptor).channel.use { channel ->
                    channel.map(
                        FileChannel.MapMode.READ_ONLY,
                        descriptor.startOffset,
                        descriptor.declaredLength,
                    )
                }
            }
        }

        private fun createRuntime(
            modelPath: String,
            numberOfThreads: Int,
        ): Runtime {
            val environment = OrtEnvironment.getEnvironment()
            val options = createSessionOptions(numberOfThreads)
            return Runtime(
                environment = environment,
                sessionOptions = options,
                session = environment.createSession(modelPath, options),
            )
        }

        private fun createRuntime(
            modelBuffer: ByteBuffer,
            numberOfThreads: Int,
        ): Runtime {
            val environment = OrtEnvironment.getEnvironment()
            val options = createSessionOptions(numberOfThreads)
            return Runtime(
                environment = environment,
                sessionOptions = options,
                session = environment.createSession(modelBuffer, options),
            )
        }

        private fun createSessionOptions(numberOfThreads: Int) =
            OrtSession.SessionOptions().apply {
                setIntraOpNumThreads(numberOfThreads)
            }

        private fun createTokenizer(modelPath: String) =
            NativeSentencePieceTokenizer(
                modelPath = modelPath,
                bosTokenId = BOS_TOKEN_ID,
                eosTokenId = EOS_TOKEN_ID,
                padTokenId = PAD_TOKEN_ID,
            )

        private fun createTokenizer(modelBytes: ByteArray) =
            NativeSentencePieceTokenizer(
                modelBytes = modelBytes,
                bosTokenId = BOS_TOKEN_ID,
                eosTokenId = EOS_TOKEN_ID,
                padTokenId = PAD_TOKEN_ID,
            )

        const val CLASSIFICATION_PREFIX = "query: "
        const val SEQUENCE_LENGTH = 64
        const val DEFAULT_THREAD_COUNT = 4
        const val BOS_TOKEN_ID = 0
        const val PAD_TOKEN_ID = 1
        const val EOS_TOKEN_ID = 2
        const val INPUT_IDS = "input_ids"
        const val ATTENTION_MASK = "attention_mask"
        const val TOKEN_TYPE_IDS = "token_type_ids"
    }

    private data class Runtime(
        val environment: OrtEnvironment,
        val sessionOptions: OrtSession.SessionOptions,
        val session: OrtSession,
    )
}
