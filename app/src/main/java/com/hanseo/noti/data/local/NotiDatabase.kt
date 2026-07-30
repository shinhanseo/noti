package com.hanseo.noti.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.hanseo.noti.data.local.dao.NotificationDao
import com.hanseo.noti.data.local.entity.NotificationEntity

@Database(
    entities = [NotificationEntity::class],
    version = 3,
    exportSchema = false
)
abstract class NotiDatabase : RoomDatabase() {

    abstract fun notificationDao(): NotificationDao
}