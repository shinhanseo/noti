package com.hanseo.noti.di

import android.content.Context
import androidx.room.Room
import com.hanseo.noti.data.local.NotiDatabase
import com.hanseo.noti.data.local.dao.NotificationDao
import com.hanseo.noti.data.local.migration.MIGRATION_1_2
import com.hanseo.noti.data.local.migration.MIGRATION_2_3
import com.hanseo.noti.data.local.migration.MIGRATION_3_4
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton
import com.hanseo.noti.data.local.dao.NotificationFeedbackDao
import com.hanseo.noti.data.local.migration.MIGRATION_4_5
import com.hanseo.noti.data.local.migration.MIGRATION_5_6
import com.hanseo.noti.data.local.migration.MIGRATION_6_7
import com.hanseo.noti.data.local.migration.MIGRATION_7_8

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideNotiDatabase(
        @ApplicationContext context: Context
    ): NotiDatabase {
        return Room.databaseBuilder(
            context,
            NotiDatabase::class.java,
            DATABASE_NAME
        )
            .addMigrations(
                MIGRATION_1_2,
                MIGRATION_2_3,
                MIGRATION_3_4,
                MIGRATION_4_5,
                MIGRATION_5_6,
                MIGRATION_6_7,
                MIGRATION_7_8
            )
            .build()
    }

    @Provides
    fun provideNotificationDao(
        database: NotiDatabase
    ): NotificationDao {
        return database.notificationDao()
    }

    @Provides
    fun provideNotificationFeedbackDao(
        database: NotiDatabase
    ): NotificationFeedbackDao {
        return database.notificationFeedbackDao()
    }

    private const val DATABASE_NAME = "noti.db"
}
