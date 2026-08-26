package com.hanseo.noti.data.local.migration

import android.content.Context
import androidx.sqlite.db.SupportSQLiteDatabase
import androidx.sqlite.db.SupportSQLiteOpenHelper
import androidx.sqlite.db.framework.FrameworkSQLiteOpenHelperFactory
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class DatabaseMigration8To9Test {

    @Test
    fun migration8To9_preservesNotificationAndAddsChannelId() {
        val context = InstrumentationRegistry
            .getInstrumentation()
            .targetContext

        context.deleteDatabase(DATABASE_NAME)
        createVersion8Database(context)

        val version9Helper =
            FrameworkSQLiteOpenHelperFactory().create(
                SupportSQLiteOpenHelper.Configuration
                    .builder(context)
                    .name(DATABASE_NAME)
                    .callback(
                        object :
                            SupportSQLiteOpenHelper.Callback(9) {

                            override fun onCreate(
                                db: SupportSQLiteDatabase
                            ) = Unit

                            override fun onUpgrade(
                                db: SupportSQLiteDatabase,
                                oldVersion: Int,
                                newVersion: Int
                            ) {
                                assertEquals(8, oldVersion)
                                assertEquals(9, newVersion)
                                MIGRATION_8_9.migrate(db)
                            }
                        }
                    )
                    .build()
            )

        try {
            val migratedDatabase =
                version9Helper.writableDatabase

            migratedDatabase.query(
                """
                SELECT
                    notification_key,
                    title,
                    channel_id
                FROM notifications
                WHERE notification_key = ?
                """.trimIndent(),
                arrayOf(NOTIFICATION_KEY)
            ).use { cursor ->
                assertTrue(cursor.moveToFirst())
                assertEquals(
                    NOTIFICATION_KEY,
                    cursor.getString(
                        cursor.getColumnIndexOrThrow(
                            "notification_key"
                        )
                    )
                )
                assertEquals(
                    "기존 알림",
                    cursor.getString(
                        cursor.getColumnIndexOrThrow("title")
                    )
                )
                assertTrue(
                    cursor.isNull(
                        cursor.getColumnIndexOrThrow(
                            "channel_id"
                        )
                    )
                )
            }
        } finally {
            version9Helper.close()
            context.deleteDatabase(DATABASE_NAME)
        }
    }

    private fun createVersion8Database(
        context: Context
    ) {
        val version8Helper =
            FrameworkSQLiteOpenHelperFactory().create(
                SupportSQLiteOpenHelper.Configuration
                    .builder(context)
                    .name(DATABASE_NAME)
                    .callback(
                        object :
                            SupportSQLiteOpenHelper.Callback(8) {

                            override fun onCreate(
                                db: SupportSQLiteDatabase
                            ) {
                                db.execSQL(
                                    """
                                    CREATE TABLE notifications (
                                        notification_key TEXT NOT NULL PRIMARY KEY,
                                        package_name TEXT NOT NULL,
                                        title TEXT,
                                        body TEXT,
                                        posted_at INTEGER NOT NULL,
                                        category TEXT,
                                        is_ongoing INTEGER NOT NULL,
                                        is_removed INTEGER NOT NULL DEFAULT 0,
                                        removed_at INTEGER,
                                        read_at INTEGER,
                                        importance_score INTEGER,
                                        importance_level TEXT,
                                        importance_forced INTEGER,
                                        importance_policy_version TEXT,
                                        importance_evaluated_at INTEGER,
                                        ai_prediction_label TEXT,
                                        ai_important_probability REAL,
                                        ai_score_delta INTEGER,
                                        ai_model_version TEXT,
                                        ai_evaluated_at INTEGER
                                    )
                                    """.trimIndent()
                                )

                                db.execSQL(
                                    """
                                    INSERT INTO notifications (
                                        notification_key,
                                        package_name,
                                        title,
                                        posted_at,
                                        is_ongoing,
                                        is_removed
                                    ) VALUES (?, ?, ?, ?, ?, ?)
                                    """.trimIndent(),
                                    arrayOf<Any>(
                                        NOTIFICATION_KEY,
                                        "com.example.app",
                                        "기존 알림",
                                        1_000L,
                                        0,
                                        0
                                    )
                                )
                            }

                            override fun onUpgrade(
                                db: SupportSQLiteDatabase,
                                oldVersion: Int,
                                newVersion: Int
                            ) = Unit
                        }
                    )
                    .build()
            )

        version8Helper.writableDatabase
        version8Helper.close()
    }

    private companion object {
        const val DATABASE_NAME =
            "migration-8-to-9-test.db"

        const val NOTIFICATION_KEY =
            "existing-notification"
    }
}
