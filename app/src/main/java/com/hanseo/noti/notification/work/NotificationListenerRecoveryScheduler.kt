package com.hanseo.noti.notification.work

import android.content.Context
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import dagger.hilt.android.qualifiers.ApplicationContext
import java.util.concurrent.TimeUnit
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationListenerRecoveryScheduler @Inject constructor(
    @ApplicationContext private val context: Context
) {
    fun schedule() {
        val recoveryWork =
            PeriodicWorkRequestBuilder<
                    NotificationListenerRecoveryWorker
                    >(
                RECOVERY_INTERVAL_MINUTES,
                TimeUnit.MINUTES
            )
                .addTag(RECOVERY_WORK_TAG)
                .build()

        WorkManager
            .getInstance(context)
            .enqueueUniquePeriodicWork(
                RECOVERY_WORK_NAME,
                ExistingPeriodicWorkPolicy.UPDATE,
                recoveryWork
            )
    }

    private companion object {
        const val RECOVERY_INTERVAL_MINUTES = 15L

        const val RECOVERY_WORK_NAME =
            "notification_listener_recovery"

        const val RECOVERY_WORK_TAG =
            "notification_listener_recovery"
    }
}