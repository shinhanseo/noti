package com.hanseo.noti.ai

import android.content.Context
import java.io.File
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.channels.FileChannel

data class KoenE5Assets(
    val modelBuffer: ByteBuffer,
    val tokenizerModelPath: String,
)

object KoenE5AssetLoader {

    @Synchronized
    fun load(
        context: Context,
    ): KoenE5Assets {
        val appContext =
            context.applicationContext

        val modelBuffer =
            mapModelAsset(appContext)

        val tokenizerFile =
            copyTokenizerAsset(appContext)

        return KoenE5Assets(
            modelBuffer = modelBuffer,
            tokenizerModelPath =
                tokenizerFile.absolutePath,
        )
    }

    private fun mapModelAsset(
        context: Context,
    ): ByteBuffer {
        return context.assets
            .openFd(MODEL_ASSET_PATH)
            .use { descriptor ->
                FileInputStream(
                    descriptor.fileDescriptor
                ).channel.use { channel ->
                    channel.map(
                        FileChannel.MapMode.READ_ONLY,
                        descriptor.startOffset,
                        descriptor.declaredLength,
                    )
                }
            }
    }

    private fun copyTokenizerAsset(
        context: Context,
    ): File {
        val aiDirectory =
            File(
                context.filesDir,
                AI_DIRECTORY_NAME,
            )

        check(
            aiDirectory.exists() ||
                    aiDirectory.mkdirs()
        ) {
            "Failed to create AI directory"
        }

        val tokenizerFile =
            File(
                aiDirectory,
                TOKENIZER_FILE_NAME,
            )

        if (!tokenizerFile.exists()) {
            context.assets
                .open(TOKENIZER_ASSET_PATH)
                .use { input ->
                    tokenizerFile
                        .outputStream()
                        .use { output ->
                            input.copyTo(output)
                        }
                }
        }

        check(
            tokenizerFile.exists() &&
                    tokenizerFile.length() > 0L
        ) {
            "Failed to copy tokenizer model"
        }

        return tokenizerFile
    }

    private const val MODEL_ASSET_PATH =
        "ai/noti_koen_e5_tiny_actionability_v1_int8.onnx"

    private const val TOKENIZER_ASSET_PATH =
        "ai/tokenizer.model"

    private const val AI_DIRECTORY_NAME =
        "ai"

    private const val TOKENIZER_FILE_NAME =
        "koen_e5_tiny_actionability_v1_tokenizer.model"
}