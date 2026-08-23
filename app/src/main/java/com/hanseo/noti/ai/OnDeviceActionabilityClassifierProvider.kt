package com.hanseo.noti.ai

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class OnDeviceActionabilityClassifierProvider
@Inject constructor(
    @param:ApplicationContext
    private val context: Context
) : ActionabilityClassifierProvider {

    private val classifierResult:
        Result<ActionabilityClassifier> by lazy(
        mode = LazyThreadSafetyMode.SYNCHRONIZED
    ) {
        runCatching {
            val assets =
                KoenE5AssetLoader.load(context)

            KoenE5ActionabilityClassifier(
                modelBuffer = assets.modelBuffer,
                tokenizerModelPath =
                    assets.tokenizerModelPath
            )
        }
    }

    override fun get():
        Result<ActionabilityClassifier> {
        return classifierResult
    }
}
