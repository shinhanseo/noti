package com.hanseo.noti.ai

import android.content.Context
import com.hanseo.noti.domain.importance.AiImportancePrediction
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class OnDeviceActionabilityPredictor @Inject constructor(
    @param:ApplicationContext private val context: Context,
) {
    private val classifier: OnDeviceActionabilityClassifier by lazy(
        LazyThreadSafetyMode.SYNCHRONIZED
    ) {
        OnDeviceActionabilityClassifier.fromAssets(context)
    }
    private val mapper = ActionabilityPredictionMapper()

    fun predict(normalizedText: String): AiImportancePrediction {
        return mapper.map(classifier.classify(normalizedText))
    }
}
