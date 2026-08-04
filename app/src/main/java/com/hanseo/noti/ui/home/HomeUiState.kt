package com.hanseo.noti.ui.home

import com.hanseo.noti.ui.model.NotificationUiModel

data class HomeUiState(
    val importantNotifications:
    List<NotificationUiModel> = emptyList(),

    val todayTotalNotificationCount: Int = 0,

    val todayImportantNotificationCount: Int = 0
)
