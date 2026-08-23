package com.hanseo.noti.notification

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.provider.Settings
import android.service.notification.NotificationListenerService
import androidx.core.app.NotificationManagerCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationAccessManager @Inject constructor(
    @param:ApplicationContext
    private val context: Context
) {

    @Volatile
    private var isListenerConnected = false

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

    fun markListenerConnected() {
        isListenerConnected = true
    }

    fun markListenerDisconnected() {
        isListenerConnected = false
    }

    @Synchronized
    fun requestRebindIfNeeded(): Boolean {
        if (!hasNotificationAccess()) {
            return false
        }

        if (isListenerConnected) {
            return false
        }

        val listenerComponent =
            ComponentName(
                context,
                NotiNotificationListenerService::class.java
            )

        NotificationListenerService.requestRebind(
            listenerComponent
        )

        return true
    }
}
