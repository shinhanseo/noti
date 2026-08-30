package com.hanseo.noti.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import com.hanseo.noti.data.local.dao.NotificationDao
import com.hanseo.noti.data.local.entity.NotificationEntity
import com.hanseo.noti.data.local.entity.ImportanceReasonEntity
import com.hanseo.noti.data.local.dao.NotificationFeedbackDao
import com.hanseo.noti.data.local.entity.NotificationFeedbackEntity

@Database(
    entities = [
        NotificationEntity::class,
        ImportanceReasonEntity::class,
        NotificationFeedbackEntity::class
    ],
    version = 10,
    exportSchema = false
)
abstract class NotiDatabase : RoomDatabase() {

    abstract fun notificationDao(): NotificationDao

    abstract fun notificationFeedbackDao():
            NotificationFeedbackDao
}
