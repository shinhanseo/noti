package com.hanseo.noti.ui.notifications

import com.hanseo.noti.ui.model.NotificationUiModel

data class NotificationsUiState(
    val notifications: List<NotificationUiModel> = emptyList(),
    val selectedFilter: NotificationFilter = NotificationFilter.ALL,
    val unreadCount: Int = 0,
    val totalCount: Int = 0,
    val importantCount: Int = 0
)
