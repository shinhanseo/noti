package com.hanseo.noti.domain.model

import com.hanseo.noti.domain.importance.ImportanceResult
import com.hanseo.noti.domain.importance.AiImportancePrediction

data class ClassifiedNotification(
    val notification: NotificationItem,
    val importance: ImportanceResult,
    val aiPrediction: AiImportancePrediction? = null
)
