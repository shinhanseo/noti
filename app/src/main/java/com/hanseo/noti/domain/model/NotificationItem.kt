package com.hanseo.noti.domain.model

data class NotificationItem (
    val key: String,
    val packageName: String,
    val title: String?,
    val body: String?,
    val postedAt: Long,
    val isOngoing: Boolean,
)