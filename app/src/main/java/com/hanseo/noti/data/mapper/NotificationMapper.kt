package com.hanseo.noti.data.mapper

import com.hanseo.noti.data.local.entity.NotificationEntity
import com.hanseo.noti.domain.model.NotificationItem
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.data.local.entity.ImportanceReasonEntity

fun NotificationEntity.toDomain(): NotificationItem {
    return NotificationItem(
        key = notificationKey,
        packageName = packageName,
        title = title,
        body = body,
        postedAt = postedAt,
        category = category,
        isOngoing = isOngoing,
        isGroupSummary = false,
        isRemoved = isRemoved,
        removedAt = removedAt
    )
}

fun ClassifiedNotification.toEntity(): NotificationEntity {
    return NotificationEntity(
        notificationKey = notification.key,
        packageName = notification.packageName,
        title = notification.title,
        body = notification.body,
        postedAt = notification.postedAt,
        category = notification.category,
        isOngoing = notification.isOngoing,
        isRemoved = notification.isRemoved,
        removedAt = notification.removedAt,

        importanceScore = importance.score,
        importanceLevel = importance.level.name,
        importanceForced = importance.isForced,
        importancePolicyVersion = importance.policyVersion,
        importanceEvaluatedAt = importance.evaluatedAtMillis
    )
}

fun ClassifiedNotification.toReasonEntities(): List<ImportanceReasonEntity> {
    return importance.reasons.mapIndexed { index, reason ->
        ImportanceReasonEntity(
            notificationKey = notification.key,
            reasonOrder = index,
            type = reason.type.name,
            scoreDelta = reason.scoreDelta,
            ruleId = reason.ruleId,
            description = reason.description
        )
    }
}