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
import android.app.Notification
import java.util.concurrent.TimeUnit
import com.hanseo.noti.data.mapper.toImportanceInput
import com.hanseo.noti.domain.importance.ImportanceClassifier
import com.hanseo.noti.domain.importance.ImportanceSettings
import com.hanseo.noti.domain.model.ClassifiedNotification

class NotiNotificationListenerService :
    NotificationListenerService() {

    private val serviceScope =
        CoroutineScope(SupervisorJob() + Dispatchers.IO) // 코루틴 Scope

    private val notificationRepository by lazy {
        (application as NotiApplication).notificationRepository // 레파지토리
    }

    private val importanceClassifier = ImportanceClassifier()

    private val importanceSettings = ImportanceSettings()

    override fun onListenerConnected() { // 서비스 연결 함수
        super.onListenerConnected()

        Log.d(TAG, "Notification listener connected")

        cleanupOldNotifications()
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
                val importanceResult = importanceClassifier.classify(
                    input = notificationItem.toImportanceInput(),
                    settings = importanceSettings
                )

                val classifiedNotification = ClassifiedNotification(
                    notification = notificationItem,
                    importance = importanceResult
                )

                notificationRepository.save(classifiedNotification)

                Log.d(
                    TAG,
                    "Notification classified and saved: " +
                            "score=${importanceResult.score}, " +
                            "level=${importanceResult.level}, " +
                            "forced=${importanceResult.isForced}"
                )

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

    override fun onNotificationRemoved(
        sbn: StatusBarNotification?
    ) {
        if (sbn == null) return
        if (sbn.packageName == packageName) return

        val isGroupSummary =
            sbn.notification.flags and
                    Notification.FLAG_GROUP_SUMMARY != 0

        if (isGroupSummary) return

        val notificationKey = sbn.key
        val removedAt = System.currentTimeMillis()

        serviceScope.launch {
            try {
                val wasUpdated =
                    notificationRepository.markAsRemoved(
                        notificationKey = notificationKey,
                        removedAt = removedAt
                    )

                if (wasUpdated) {
                    Log.d(TAG, "Notification marked as removed")
                } else {
                    Log.d(TAG, "Removed notification was not stored")
                }

            } catch (error: CancellationException) {
                throw error

            } catch (error: Exception) {
                Log.e(
                    TAG,
                    "Notification removal update failed: " +
                            error.javaClass.simpleName
                )
            }
        }
    }

    private fun cleanupOldNotifications() {
        val retentionMillis =
            TimeUnit.DAYS.toMillis(
                REMOVED_NOTIFICATION_RETENTION_DAYS
            )

        val cutoffTime =
            System.currentTimeMillis() - retentionMillis

        serviceScope.launch {
            try {
                val deletedCount =
                    notificationRepository.deleteRemovedBefore(
                        cutoffTime = cutoffTime
                    )

                Log.d(
                    TAG,
                    "Old notification cleanup completed: " +
                            "deletedCount=$deletedCount"
                )

            } catch (error: CancellationException) {
                throw error

            } catch (error: Exception) {
                Log.e(
                    TAG,
                    "Old notification cleanup failed: " +
                            error.javaClass.simpleName
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
        private const val REMOVED_NOTIFICATION_RETENTION_DAYS = 30L
    }
}