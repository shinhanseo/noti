package com.hanseo.noti.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "importance_reasons",
    foreignKeys = [
        ForeignKey(
            entity = NotificationEntity::class,
            parentColumns = ["notification_key"],
            childColumns = ["notification_key"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["notification_key"])
    ]
)
data class ImportanceReasonEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    @ColumnInfo(name = "notification_key")
    val notificationKey: String,

    @ColumnInfo(name = "reason_order")
    val reasonOrder: Int,

    val type: String,

    @ColumnInfo(name = "score_delta")
    val scoreDelta: Int,

    @ColumnInfo(name = "rule_id")
    val ruleId: String?,

    val description: String
)