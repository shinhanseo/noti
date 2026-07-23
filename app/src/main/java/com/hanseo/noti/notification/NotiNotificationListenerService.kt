package com.hanseo.noti.notification

import android.service.notification.NotificationListenerService
import android.util.Log

class NotiNotificationListenerService :
    NotificationListenerService() {

    override fun onListenerConnected() {
        super.onListenerConnected()

        Log.d(TAG, "Notification listener connected")
    }

    companion object {
        private const val TAG = "NotiListener"
    }
}