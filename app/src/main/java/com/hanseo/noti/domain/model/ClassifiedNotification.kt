package com.hanseo.noti.domain.model

import com.hanseo.noti.domain.importance.ImportanceResult

data class ClassifiedNotification(
    val notification: NotificationItem,
    val importance: ImportanceResult
)
