package com.hanseo.noti.data.mapper

import com.hanseo.noti.data.local.entity.NotificationEntity
import com.hanseo.noti.domain.model.NotificationItem

fun NotificationItem.toEntity() : NotificationEntity {
    return NotificationEntity(
        notificationKey = key,
        packageName = packageName,
        title = title,
        body = body,
        postedAt = postedAt,
        category = category,
        isOngoing = isOngoing,
    )
}

fun NotificationEntity.toDomain(): NotificationItem {
    return NotificationItem(
        key = notificationKey,
        packageName = packageName,
        title = title,
        body = body,
        postedAt = postedAt,
        category = category,
        isOngoing = isOngoing,
        isGroupSummary = false
    )
}