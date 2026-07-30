package com.hanseo.noti.data.local.relation

import androidx.room.Embedded
import androidx.room.Relation
import com.hanseo.noti.data.local.entity.ImportanceReasonEntity
import com.hanseo.noti.data.local.entity.NotificationEntity

data class NotificationWithReasons(
    @Embedded
    val notification: NotificationEntity,

    @Relation(
        parentColumn = "notification_key",
        entityColumn = "notification_key"
    )
    val reasons: List<ImportanceReasonEntity>
)