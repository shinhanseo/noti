package com.hanseo.noti.ui.home

data class HomeUiState(
    val importantNotifications:
    List<HomeNotificationUiModel> = emptyList(),

    val todayTotalNotificationCount: Int = 0,

    val todayImportantNotificationCount: Int = 0
)
