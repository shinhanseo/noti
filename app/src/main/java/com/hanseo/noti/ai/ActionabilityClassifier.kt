package com.hanseo.noti.ai

fun interface ActionabilityClassifier {
    fun classify(
        normalizedText: String
    ) : ActionabilityResult
}