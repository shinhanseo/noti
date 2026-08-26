package com.hanseo.noti.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.PrimaryKey

@Entity(
    tableName = "notification_feedback",
    foreignKeys = [
        ForeignKey(
            entity = NotificationEntity::class,
            parentColumns = ["notification_key"],
            childColumns = ["notification_key"],
            onDelete = ForeignKey.CASCADE
        )
    ]
)
data class NotificationFeedbackEntity(
    @PrimaryKey
    @ColumnInfo(name = "notification_key")
    val notificationKey: String,

    @ColumnInfo(name = "user_label")
    val userLabel: String,

    @ColumnInfo(name = "original_level")
    val originalLevel: String,

    @ColumnInfo(name = "original_score")
    val originalScore: Int,

    @ColumnInfo(name = "policy_version")
    val policyVersion: String,

    @ColumnInfo(name = "feedback_at")
    val feedbackAt: Long,

    @ColumnInfo(name = "reason_code")
    val reasonCode: String? = null,

    @ColumnInfo(name = "reason_text")
    val reasonText: String? = null
)
