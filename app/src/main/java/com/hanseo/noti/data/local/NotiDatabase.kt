package com.hanseo.noti.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.hanseo.noti.data.local.dao.NotificationDao
import com.hanseo.noti.data.local.entity.NotificationEntity
import com.hanseo.noti.data.local.entity.ImportanceReasonEntity

@Database(
    entities = [
        NotificationEntity::class,
        ImportanceReasonEntity::class
    ],
    version = 4,
    exportSchema = false
)
abstract class NotiDatabase : RoomDatabase() {

    abstract fun notificationDao(): NotificationDao
}