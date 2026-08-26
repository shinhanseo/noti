package com.hanseo.noti.notification.work

import android.content.Context
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.work.WorkManager
import androidx.work.testing.TestWorkerBuilder
import com.hanseo.noti.NotiApplication
import java.util.concurrent.Executor
import java.util.concurrent.TimeUnit
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NotificationListenerRecoveryWorkTest {

    private lateinit var context: Context
    private lateinit var workManager: WorkManager

    @Before
    fun setUp() {
        context = ApplicationProvider.getApplicationContext()
        workManager = WorkManager.getInstance(context)

        workManager
            .cancelUniqueWork(RECOVERY_WORK_NAME)
            .result
            .get(10, TimeUnit.SECONDS)
    }

    @After
    fun tearDown() {
        workManager
            .cancelUniqueWork(RECOVERY_WORK_NAME)
            .result
            .get(10, TimeUnit.SECONDS)
    }

    @Test
    fun hiltWorkerFactory_createsRecoveryWorker() {
        val application =
            ApplicationProvider
                .getApplicationContext<NotiApplication>()

        val worker =
            TestWorkerBuilder<NotificationListenerRecoveryWorker>(
                context = context,
                executor = Executor { command -> command.run() }
            )
                .setWorkerFactory(application.workerFactory)
                .build()

        assertNotNull(worker)
    }

    @Test
    fun schedule_calledTwice_keepsOneActivePeriodicWork() {
        val scheduler =
            NotificationListenerRecoveryScheduler(context)

        scheduler.schedule()
        scheduler.schedule()

        val activeWork =
            workManager
                .getWorkInfosForUniqueWork(RECOVERY_WORK_NAME)
                .get(10, TimeUnit.SECONDS)
                .filterNot { workInfo ->
                    workInfo.state.isFinished
                }

        assertEquals(1, activeWork.size)
        assertEquals(
            setOf(RECOVERY_WORK_TAG),
            activeWork.single().tags
                .filter { tag -> tag == RECOVERY_WORK_TAG }
                .toSet()
        )
    }

    private companion object {
        const val RECOVERY_WORK_NAME =
            "notification_listener_recovery"

        const val RECOVERY_WORK_TAG =
            "notification_listener_recovery"
    }
}
