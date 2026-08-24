package com.hanseo.noti.ui.main

import com.hanseo.noti.notification.NotificationListenerConnectionStatus

data class MainUiState(
    val hasNotificationAccess: Boolean = false,

    val listenerConnectionStatus:
        NotificationListenerConnectionStatus =
        NotificationListenerConnectionStatus.ACCESS_REQUIRED,

    val isBatteryOptimizationExempt: Boolean = false
)
