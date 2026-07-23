package com.hanseo.noti.notification

import android.app.Notification
import android.service.notification.StatusBarNotification
import com.hanseo.noti.domain.model.NotificationItem

object NotificationParser {

    fun parse(sbn: StatusBarNotification): NotificationItem {
        val notification = sbn.notification
        val extras = notification.extras

        val title = extras
            .getCharSequence(Notification.EXTRA_TITLE)
            ?.toString()

        val body = (
                extras.getCharSequence(Notification.EXTRA_BIG_TEXT)
                    ?: extras.getCharSequence(Notification.EXTRA_TEXT)
                )?.toString()

        return NotificationItem(
            key = sbn.key,
            packageName = sbn.packageName,
            title = title,
            body = body,
            postedAt = sbn.postTime,
            isOngoing = sbn.isOngoing
        )
    }
}