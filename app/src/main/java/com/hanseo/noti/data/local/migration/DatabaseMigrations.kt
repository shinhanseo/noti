package com.hanseo.noti.data.local.migration

import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase

val MIGRATION_1_2 = object : Migration(1, 2) {

    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """
        ALTER TABLE notifications
        ADD COLUMN is_removed INTEGER NOT NULL DEFAULT 0
        """.trimIndent()
        )

        db.execSQL(
            """
        ALTER TABLE notifications
        ADD COLUMN removed_at INTEGER DEFAULT NULL
        """.trimIndent()
        )
    }
}

val MIGRATION_2_3 = object : Migration(2, 3) {

    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN importance_score INTEGER
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN importance_level TEXT
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN importance_forced INTEGER
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN importance_policy_version TEXT
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN importance_evaluated_at INTEGER
            """.trimIndent()
        )
    }
}