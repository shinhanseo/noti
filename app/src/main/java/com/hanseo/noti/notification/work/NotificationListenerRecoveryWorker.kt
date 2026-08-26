package com.hanseo.noti.notification.work

import android.content.Context
import android.util.Log
import androidx.hilt.work.HiltWorker
import androidx.work.Worker
import androidx.work.WorkerParameters
import com.hanseo.noti.notification.NotificationAccessManager
import dagger.assisted.Assisted
import dagger.assisted.AssistedInject

@HiltWorker
class NotificationListenerRecoveryWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted workerParameters: WorkerParameters,
    private val notificationAccessManager: NotificationAccessManager
) : Worker (
    appContext,
    workerParameters
) {
    override fun doWork(): Result {
        if (!notificationAccessManager.hasNotificationAccess()){
            Log.w(
                TAG,
                "Recovery skipped: notification access is not granted"
            )

            return Result.success()
        }

        notificationAccessManager.refreshConnectionStatus()

        val rebindRequested = notificationAccessManager.requestRebindIfNeeded()

        Log.d(
            TAG,
            "Notification listener recovery checked: " +
                    "rebindRequested=$rebindRequested"
        )

        return Result.success()
    }

    private companion object {
        const val TAG =
            "ListenerRecoveryWorker"
    }
}
