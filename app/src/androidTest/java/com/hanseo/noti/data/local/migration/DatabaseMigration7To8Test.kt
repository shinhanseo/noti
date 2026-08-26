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
class DatabaseMigration7To8Test {

    @Test
    fun migration7To8_preservesFeedbackAndAddsReasonColumns() {
        val context = InstrumentationRegistry
            .getInstrumentation()
            .targetContext

        context.deleteDatabase(DATABASE_NAME)
        createVersion7Database(context)

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
                            ) = Unit

                            override fun onUpgrade(
                                db: SupportSQLiteDatabase,
                                oldVersion: Int,
                                newVersion: Int
                            ) {
                                assertEquals(7, oldVersion)
                                assertEquals(8, newVersion)
                                MIGRATION_7_8.migrate(db)
                            }
                        }
                    )
                    .build()
            )

        try {
            val migratedDatabase =
                version8Helper.writableDatabase

            migratedDatabase.query(
                """
                SELECT
                    notification_key,
                    user_label,
                    reason_code,
                    reason_text
                FROM notification_feedback
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
                    "IMPORTANT",
                    cursor.getString(
                        cursor.getColumnIndexOrThrow(
                            "user_label"
                        )
                    )
                )
                assertTrue(
                    cursor.isNull(
                        cursor.getColumnIndexOrThrow(
                            "reason_code"
                        )
                    )
                )
                assertTrue(
                    cursor.isNull(
                        cursor.getColumnIndexOrThrow(
                            "reason_text"
                        )
                    )
                )
            }
        } finally {
            version8Helper.close()
            context.deleteDatabase(DATABASE_NAME)
        }
    }

    private fun createVersion7Database(
        context: Context
    ) {
        val version7Helper =
            FrameworkSQLiteOpenHelperFactory().create(
                SupportSQLiteOpenHelper.Configuration
                    .builder(context)
                    .name(DATABASE_NAME)
                    .callback(
                        object :
                            SupportSQLiteOpenHelper.Callback(7) {

                            override fun onCreate(
                                db: SupportSQLiteDatabase
                            ) {
                                db.execSQL(
                                    """
                                    CREATE TABLE notifications (
                                        notification_key TEXT NOT NULL PRIMARY KEY
                                    )
                                    """.trimIndent()
                                )

                                db.execSQL(
                                    """
                                    CREATE TABLE notification_feedback (
                                        notification_key TEXT NOT NULL PRIMARY KEY,
                                        user_label TEXT NOT NULL,
                                        original_level TEXT NOT NULL,
                                        original_score INTEGER NOT NULL,
                                        policy_version TEXT NOT NULL,
                                        feedback_at INTEGER NOT NULL,
                                        FOREIGN KEY(notification_key)
                                            REFERENCES notifications(notification_key)
                                            ON UPDATE NO ACTION
                                            ON DELETE CASCADE
                                    )
                                    """.trimIndent()
                                )

                                db.execSQL(
                                    """
                                    INSERT INTO notifications (
                                        notification_key
                                    ) VALUES (?)
                                    """.trimIndent(),
                                    arrayOf<Any>(NOTIFICATION_KEY)
                                )

                                db.execSQL(
                                    """
                                    INSERT INTO notification_feedback (
                                        notification_key,
                                        user_label,
                                        original_level,
                                        original_score,
                                        policy_version,
                                        feedback_at
                                    ) VALUES (?, ?, ?, ?, ?, ?)
                                    """.trimIndent(),
                                    arrayOf<Any>(
                                        NOTIFICATION_KEY,
                                        "IMPORTANT",
                                        "GENERAL",
                                        10,
                                        "test-policy",
                                        1_000L
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

        version7Helper.writableDatabase
        version7Helper.close()
    }

    private companion object {
        const val DATABASE_NAME =
            "migration-7-to-8-test.db"

        const val NOTIFICATION_KEY =
            "existing-feedback-notification"
    }
}
