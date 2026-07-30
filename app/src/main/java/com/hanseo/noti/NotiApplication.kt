package com.hanseo.noti

import android.app.Application
import androidx.room.Room
import com.hanseo.noti.data.local.NotiDatabase
import com.hanseo.noti.data.repository.NotificationRepository
import com.hanseo.noti.data.local.migration.MIGRATION_1_2
import com.hanseo.noti.data.local.migration.MIGRATION_2_3

class NotiApplication : Application() {
    val database: NotiDatabase by lazy {
        Room.databaseBuilder(
            this,
            NotiDatabase::class.java,
            DATABASE_NAME
        )
            .addMigrations(
                MIGRATION_1_2,
                MIGRATION_2_3
            )
            .build()
    }

    val notificationRepository: NotificationRepository by lazy {
        NotificationRepository(
            notificationDao = database.notificationDao()
        )
    }

    companion object {
        private const val DATABASE_NAME = "noti.db"
    }
}