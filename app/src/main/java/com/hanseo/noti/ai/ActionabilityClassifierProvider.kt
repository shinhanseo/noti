package com.hanseo.noti.ai

interface ActionabilityClassifierProvider {

    fun get():
        Result<ActionabilityClassifier>
}
