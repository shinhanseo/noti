package com.hanseo.noti.domain.model

import com.hanseo.noti.domain.importance.ImportanceResult
import com.hanseo.noti.domain.importance.AiImportancePrediction
import com.hanseo.noti.domain.topic.NotificationTopicResult

data class ClassifiedNotification(
    val notification: NotificationItem,
    val importance: ImportanceResult,
    val aiPrediction: AiImportancePrediction? = null,
    val topicResult: NotificationTopicResult
)
