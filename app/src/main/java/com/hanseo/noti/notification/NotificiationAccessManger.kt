package com.hanseo.noti.notification

import android.content.Context
import android.content.Intent
import android.provider.Settings
import androidx.core.app.NotificationManagerCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationAccessManager @Inject constructor(
    @param:ApplicationContext
    private val context: Context
) {

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
}