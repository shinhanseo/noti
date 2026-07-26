package com.hanseo.noti

import android.app.Application
import androidx.room.Room
import com.hanseo.noti.data.local.NotiDatabase

class NotiApplication : Application() {
    val database: NotiDatabase by lazy {
        Room.databaseBuilder(
            this,
            NotiDatabase::class.java,
            DATABASE_NAME
        ).build()
    }

    companion object {
        private const val DATABASE_NAME = "noti.db"
    }
}