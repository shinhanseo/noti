package com.hanseo.noti.domain.importance

import com.hanseo.noti.domain.model.NotificationItem

fun NotificationItem.toImportanceInput(): ImportanceInput {
    return ImportanceInput(
        packageName = packageName,
        title = title,
        body = body,
        category = category,
        isOngoing = isOngoing
    )
}