package com.hanseo.noti.notification

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.service.notification.NotificationListenerService
import androidx.core.app.NotificationManagerCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

enum class NotificationListenerConnectionStatus {
    ACCESS_REQUIRED,
    DISCONNECTED,
    REBINDING,
    CONNECTED,
    RECONNECT_REQUIRED
}

@Singleton
class NotificationAccessManager @Inject constructor(
    @param:ApplicationContext
    private val context: Context
) {

    private val mainHandler =
        Handler(Looper.getMainLooper())

    @Volatile
    private var isListenerConnected = false

    private val _connectionStatus =
        MutableStateFlow(
            if (hasNotificationAccess()) {
                NotificationListenerConnectionStatus.DISCONNECTED
            } else {
                NotificationListenerConnectionStatus.ACCESS_REQUIRED
            }
        )

    val connectionStatus:
        StateFlow<NotificationListenerConnectionStatus> =
        _connectionStatus.asStateFlow()

    private val rebindTimeoutRunnable = Runnable {
        markRebindTimedOut()
    }

    fun hasNotificationAccess(): Boolean {
        val enabledPackages =
            NotificationManagerCompat
                .getEnabledListenerPackages(context)

        return context.packageName in enabledPackages
    }

    fun createNotificationAccessSettingsIntent(): Intent {
        return Intent(
            Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS
        )
    }

    @Synchronized
    fun refreshConnectionStatus() {
        if (!hasNotificationAccess()) {
            isListenerConnected = false
            cancelRebindTimeout()
            _connectionStatus.value =
                NotificationListenerConnectionStatus.ACCESS_REQUIRED
            return
        }

        if (isListenerConnected) {
            _connectionStatus.value =
                NotificationListenerConnectionStatus.CONNECTED
            return
        }

        if (
            _connectionStatus.value !=
            NotificationListenerConnectionStatus.REBINDING &&
            _connectionStatus.value !=
            NotificationListenerConnectionStatus.RECONNECT_REQUIRED
        ) {
            _connectionStatus.value =
                NotificationListenerConnectionStatus.DISCONNECTED
        }
    }

    @Synchronized
    fun markListenerConnected() {
        isListenerConnected = true
        cancelRebindTimeout()
        _connectionStatus.value =
            NotificationListenerConnectionStatus.CONNECTED
    }

    @Synchronized
    fun markListenerDisconnected() {
        isListenerConnected = false
        _connectionStatus.value =
            if (hasNotificationAccess()) {
                NotificationListenerConnectionStatus.DISCONNECTED
            } else {
                NotificationListenerConnectionStatus.ACCESS_REQUIRED
            }
    }

    @Synchronized
    fun requestRebindIfNeeded(): Boolean {
        if (!hasNotificationAccess()) {
            isListenerConnected = false
            cancelRebindTimeout()
            _connectionStatus.value =
                NotificationListenerConnectionStatus.ACCESS_REQUIRED
            return false
        }

        if (isListenerConnected) {
            cancelRebindTimeout()
            _connectionStatus.value =
                NotificationListenerConnectionStatus.CONNECTED
            return false
        }

        val listenerComponent =
            ComponentName(
                context,
                NotiNotificationListenerService::class.java
            )

        return runCatching {
            _connectionStatus.value =
                NotificationListenerConnectionStatus.REBINDING

            NotificationListenerService.requestRebind(
                listenerComponent
            )

            scheduleRebindTimeout()
            true
        }.getOrElse {
            cancelRebindTimeout()
            _connectionStatus.value =
                NotificationListenerConnectionStatus.RECONNECT_REQUIRED
            false
        }
    }

    @Synchronized
    private fun markRebindTimedOut() {
        if (
            !isListenerConnected &&
            hasNotificationAccess() &&
            _connectionStatus.value ==
            NotificationListenerConnectionStatus.REBINDING
        ) {
            _connectionStatus.value =
                NotificationListenerConnectionStatus.RECONNECT_REQUIRED
        }
    }

    private fun scheduleRebindTimeout() {
        cancelRebindTimeout()
        mainHandler.postDelayed(
            rebindTimeoutRunnable,
            REBIND_TIMEOUT_MILLIS
        )
    }

    private fun cancelRebindTimeout() {
        mainHandler.removeCallbacks(
            rebindTimeoutRunnable
        )
    }

    private companion object {
        const val REBIND_TIMEOUT_MILLIS = 5_000L
    }
}
