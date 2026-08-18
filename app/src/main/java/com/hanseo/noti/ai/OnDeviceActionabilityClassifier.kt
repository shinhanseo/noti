package com.hanseo.noti.ai

import com.hanseo.noti.ai.tokenizer.NativeSentencePieceTokenizer
import java.io.Closeable
import java.io.File
import org.tensorflow.lite.Interpreter

enum class ActionabilityLabel {
    GENERAL,
    ATTENTION_WORTHY,
    ACTION_REQUIRED,
}

data class ActionabilityResult(
    val label: ActionabilityLabel,
    val probabilities: Map<ActionabilityLabel, Float>,
)

class OnDeviceActionabilityClassifier(
    modelPath: String,
    tokenizerModelPath: String,
    numberOfThreads: Int = DEFAULT_THREAD_COUNT,
) : Closeable {

    private val tokenizer = NativeSentencePieceTokenizer(tokenizerModelPath)
    private val interpreter = Interpreter(
        File(modelPath),
        Interpreter.Options().apply { setNumThreads(numberOfThreads) },
    )

    @Synchronized
    fun classify(normalizedText: String): ActionabilityResult {
        val classificationText = CLASSIFICATION_PREFIX + normalizedText.trim()
        val tokenized = tokenizer.tokenize(classificationText, SEQUENCE_LENGTH)

        val inputIds = arrayOf(tokenized.inputIds.map(Int::toLong).toLongArray())
        val attentionMask = arrayOf(tokenized.attentionMask.map(Int::toLong).toLongArray())
        val output = Array(1) { FloatArray(ActionabilityLabel.entries.size) }

        interpreter.runForMultipleInputsOutputs(
            arrayOf(inputIds, attentionMask),
            mutableMapOf<Int, Any>(0 to output),
        )

        val probabilities = ActionabilityLabel.entries
            .mapIndexed { index, label -> label to output[0][index] }
            .toMap()
        val label = probabilities.maxBy { it.value }.key

        return ActionabilityResult(label, probabilities)
    }

    @Synchronized
    override fun close() {
        interpreter.close()
        tokenizer.close()
    }

    private companion object {
        const val CLASSIFICATION_PREFIX = "task: classification | query: "
        const val SEQUENCE_LENGTH = 64
        const val DEFAULT_THREAD_COUNT = 4
    }
}
