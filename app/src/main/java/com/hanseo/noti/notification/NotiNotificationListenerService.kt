package com.hanseo.noti.notification

import android.service.notification.NotificationListenerService
import android.util.Log
import android.service.notification.StatusBarNotification
import com.hanseo.noti.NotiApplication
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

class NotiNotificationListenerService :
    NotificationListenerService() {

    private val serviceScope =
        CoroutineScope(SupervisorJob() + Dispatchers.IO) // 코루틴 Scope

    private val notificationRepository by lazy {
        (application as NotiApplication).notificationRepository // 레파지토리
    }

    override fun onListenerConnected() { // 서비스 연결 함수
        super.onListenerConnected()

        Log.d(TAG, "Notification listener connected")
    }

    override fun onNotificationPosted( // 알림 도착 시 콜백 확인 함수
        sbn: StatusBarNotification?
    ) {
        if (sbn == null) return // 알람이 없으면 return
        if (sbn.packageName == packageName) return // noti. 자기 앱일 경우 return

        val notificationItem = NotificationParser.parse(sbn)

        val ignoreReason = NotificationFilter.findIgnoreReason(notificationItem)

        if (ignoreReason != null) {
            Log.d(
                TAG,
                "Notification ignored: reason=$ignoreReason"
            )
            return
        }

        Log.d(
            TAG,
            "Notification accepted: " +
                    "titlePresent=${notificationItem.title != null}, " +
                    "bodyPresent=${notificationItem.body != null}, " +
                    "ongoing=${notificationItem.isOngoing}"
        )

        serviceScope.launch {
            try {
                notificationRepository.save(notificationItem)
                Log.d(TAG, "Notification saved")

            } catch (error: CancellationException) {
                throw error

            } catch (error: Exception) {
                Log.e(
                    TAG,
                    "Notification save failed: ${error.javaClass.simpleName}"
                )
            }
        }
    }

    override fun onDestroy() {
        serviceScope.cancel()
        super.onDestroy()
    }

    companion object {
        private const val TAG = "NotiListener"
    }
}