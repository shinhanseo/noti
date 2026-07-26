package com.hanseo.noti.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "notifications")
data class NotificationEntity(
    @PrimaryKey
    @ColumnInfo(name = "notification_key")
    val notificationKey: String,

    @ColumnInfo(name = "package_name")
    val packageName: String,

    val title: String?,

    val body: String?,

    @ColumnInfo(name = "posted_at")
    val postedAt: Long,

    val category: String?,

    @ColumnInfo(name = "is_ongoing")
    val isOngoing: Boolean,

    @ColumnInfo(
        name = "is_removed",
        defaultValue = "0"
    )
    val isRemoved: Boolean = false,

    @ColumnInfo(
        name = "removed_at",
        defaultValue = "NULL"
    )
    val removedAt: Long? = null
)