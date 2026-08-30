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
class DatabaseMigration9To10Test {

    @Test
    fun migration9To10_preservesDataAndAddsTopicColumns() {
        val context =
            InstrumentationRegistry
                .getInstrumentation()
                .targetContext

        context.deleteDatabase(DATABASE_NAME)
        createVersion9Database(context)

        val version10Helper =
            FrameworkSQLiteOpenHelperFactory().create(
                SupportSQLiteOpenHelper.Configuration
                    .builder(context)
                    .name(DATABASE_NAME)
                    .callback(
                        object :
                            SupportSQLiteOpenHelper.Callback(10) {

                            override fun onCreate(
                                db: SupportSQLiteDatabase
                            ) = Unit

                            override fun onUpgrade(
                                db: SupportSQLiteDatabase,
                                oldVersion: Int,
                                newVersion: Int
                            ) {
                                assertEquals(9, oldVersion)
                                assertEquals(10, newVersion)
                                MIGRATION_9_10.migrate(db)
                            }
                        }
                    )
                    .build()
            )

        try {
            val database =
                version10Helper.writableDatabase

            database.query(
                """
                SELECT
                    notification_key,
                    channel_id,
                    primary_topic,
                    topic_names,
                    topic_policy_version
                FROM notifications
                WHERE notification_key = ?
                """.trimIndent(),
                arrayOf(NOTIFICATION_KEY)
            ).use { cursor ->
                assertTrue(cursor.moveToFirst())
                assertEquals(
                    NOTIFICATION_KEY,
                    cursor.getString(0)
                )
                assertEquals(
                    "delivery",
                    cursor.getString(1)
                )
                assertTrue(cursor.isNull(2))
                assertTrue(cursor.isNull(3))
                assertTrue(cursor.isNull(4))
            }

            database.query(
                """
                SELECT
                    notification_key,
                    user_label,
                    package_name,
                    channel_id,
                    primary_topic,
                    topic_policy_version
                FROM notification_feedback
                WHERE notification_key = ?
                """.trimIndent(),
                arrayOf(NOTIFICATION_KEY)
            ).use { cursor ->
                assertTrue(cursor.moveToFirst())
                assertEquals(
                    NOTIFICATION_KEY,
                    cursor.getString(0)
                )
                assertEquals("IMPORTANT", cursor.getString(1))
                assertTrue(cursor.isNull(2))
                assertTrue(cursor.isNull(3))
                assertTrue(cursor.isNull(4))
                assertTrue(cursor.isNull(5))
            }
        } finally {
            version10Helper.close()
            context.deleteDatabase(DATABASE_NAME)
        }
    }

    private fun createVersion9Database(
        context: Context
    ) {
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
                            ) {
                                createVersion9Schema(db)
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

        version9Helper.writableDatabase.apply {
            execSQL(
                """
                INSERT INTO notifications (
                    notification_key,
                    package_name,
                    title,
                    body,
                    posted_at,
                    category,
                    channel_id,
                    is_ongoing
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """.trimIndent(),
                arrayOf<Any?>(
                    NOTIFICATION_KEY,
                    "com.example.shopping",
                    "배송 안내",
                    "배송이 출발했습니다",
                    1_000L,
                    null,
                    "delivery",
                    0
                )
            )

            execSQL(
                """
                INSERT INTO notification_feedback (
                    notification_key,
                    user_label,
                    original_level,
                    original_score,
                    policy_version,
                    feedback_at,
                    reason_code,
                    reason_text
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """.trimIndent(),
                arrayOf<Any?>(
                    NOTIFICATION_KEY,
                    "IMPORTANT",
                    "GENERAL",
                    10,
                    "1",
                    2_000L,
                    "DELIVERY_RESERVATION",
                    null
                )
            )
        }

        version9Helper.close()
    }

    private fun createVersion9Schema(
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
                channel_id TEXT DEFAULT NULL,
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
            CREATE TABLE notification_feedback (
                notification_key TEXT NOT NULL PRIMARY KEY,
                user_label TEXT NOT NULL,
                original_level TEXT NOT NULL,
                original_score INTEGER NOT NULL,
                policy_version TEXT NOT NULL,
                feedback_at INTEGER NOT NULL,
                reason_code TEXT,
                reason_text TEXT,
                FOREIGN KEY(notification_key)
                    REFERENCES notifications(notification_key)
                    ON UPDATE NO ACTION
                    ON DELETE CASCADE
            )
            """.trimIndent()
        )
    }

    private companion object {
        const val DATABASE_NAME =
            "migration-9-10-test.db"

        const val NOTIFICATION_KEY =
            "migration-notification-key"
    }
}
