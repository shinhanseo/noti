package com.hanseo.noti.ai

fun interface ActionabilityClassifierProvider {

    fun get():
        Result<ActionabilityClassifier>
}
