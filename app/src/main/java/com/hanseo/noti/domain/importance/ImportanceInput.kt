package com.hanseo.noti.domain.importance

data class ImportanceInput (
    val notificationKey: String,
    val packageName: String,
    val title: String?,
    val body: String?,
    val category: String?,
    val isOngoing: Boolean
)
