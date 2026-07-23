package com.hanseo.noti.notification

import android.service.notification.NotificationListenerService
import android.util.Log
import android.service.notification.StatusBarNotification

class NotiNotificationListenerService :
    NotificationListenerService() {

    override fun onListenerConnected() { // 서비스 연결 함수
        super.onListenerConnected()

        Log.d(TAG, "Notification listener connected")
    }

    override fun onNotificationPosted( // 알림 도착 시 콜백 확인 함수
        sbn: StatusBarNotification?
    ) {
        if (sbn == null) return // 알람이 없으면 return
        if (sbn.packageName == packageName) return // noti. 자기 앱일 경우 return

        Log.d(TAG, "Notification received")
    }

    companion object {
        private const val TAG = "NotiListener"
    }
}