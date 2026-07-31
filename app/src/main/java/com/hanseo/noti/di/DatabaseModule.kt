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
                MIGRATION_3_4
            )
            .build()
    }

    @Provides
    fun provideNotificationDao(
        database: NotiDatabase
    ): NotificationDao {
        return database.notificationDao()
    }

    private const val DATABASE_NAME = "noti.db"
}