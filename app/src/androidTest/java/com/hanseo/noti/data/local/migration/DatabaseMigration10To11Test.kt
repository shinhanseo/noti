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
class DatabaseMigration10To11Test {

    @Test
    fun migration10To11_createsPersonalizationProfiles() {
        val context =
            InstrumentationRegistry
                .getInstrumentation()
                .targetContext

        context.deleteDatabase(DATABASE_NAME)
        createVersion10Database(context)

        val version11Helper =
            FrameworkSQLiteOpenHelperFactory().create(
                SupportSQLiteOpenHelper.Configuration
                    .builder(context)
                    .name(DATABASE_NAME)
                    .callback(
                        object :
                            SupportSQLiteOpenHelper.Callback(11) {

                            override fun onCreate(
                                db: SupportSQLiteDatabase
                            ) = Unit

                            override fun onUpgrade(
                                db: SupportSQLiteDatabase,
                                oldVersion: Int,
                                newVersion: Int
                            ) {
                                assertEquals(10, oldVersion)
                                assertEquals(11, newVersion)
                                MIGRATION_10_11.migrate(db)
                            }
                        }
                    )
                    .build()
            )

        try {
            val database =
                version11Helper.writableDatabase

            database.execSQL(
                """
                INSERT INTO personalization_profiles (
                    scope,
                    package_name,
                    channel_key,
                    topic_key,
                    important_count,
                    general_count,
                    last_feedback_at,
                    profile_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """.trimIndent(),
                arrayOf<Any?>(
                    "APP_CHANNEL_TOPIC",
                    "com.example.shopping",
                    "delivery",
                    "DELIVERY",
                    1,
                    0,
                    1_000L,
                    "1"
                )
            )

            database.query(
                """
                SELECT important_count, general_count
                FROM personalization_profiles
                WHERE scope = ?
                  AND package_name = ?
                  AND channel_key = ?
                  AND topic_key = ?
                """.trimIndent(),
                arrayOf(
                    "APP_CHANNEL_TOPIC",
                    "com.example.shopping",
                    "delivery",
                    "DELIVERY"
                )
            ).use { cursor ->
                assertTrue(cursor.moveToFirst())
                assertEquals(1, cursor.getInt(0))
                assertEquals(0, cursor.getInt(1))
            }
        } finally {
            version11Helper.close()
            context.deleteDatabase(DATABASE_NAME)
        }
    }

    private fun createVersion10Database(
        context: Context
    ) {
        val helper =
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
                            ) = Unit
                        }
                    )
                    .build()
            )

        helper.writableDatabase
        helper.close()
    }

    private companion object {
        const val DATABASE_NAME =
            "migration-10-11-test.db"
    }
}
