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

val MIGRATION_3_4 = object : Migration(3, 4) {

    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS importance_reasons (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                notification_key TEXT NOT NULL,
                reason_order INTEGER NOT NULL,
                type TEXT NOT NULL,
                score_delta INTEGER NOT NULL,
                rule_id TEXT,
                description TEXT NOT NULL,
                FOREIGN KEY(notification_key)
                    REFERENCES notifications(notification_key)
                    ON UPDATE NO ACTION
                    ON DELETE CASCADE
            )
            """.trimIndent()
        )

        db.execSQL(
            """
            CREATE INDEX IF NOT EXISTS
            index_importance_reasons_notification_key
            ON importance_reasons(notification_key)
            """.trimIndent()
        )
    }
}

val MIGRATION_4_5 = object : Migration(4, 5) {

    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS notification_feedback (
                notification_key TEXT NOT NULL,
                user_label TEXT NOT NULL,
                original_level TEXT NOT NULL,
                original_score INTEGER NOT NULL,
                policy_version TEXT NOT NULL,
                feedback_at INTEGER NOT NULL,
                PRIMARY KEY(notification_key),
                FOREIGN KEY(notification_key)
                    REFERENCES notifications(notification_key)
                    ON UPDATE NO ACTION
                    ON DELETE CASCADE
            )
            """.trimIndent()
        )
    }
}

val MIGRATION_5_6 = object : Migration(5, 6) {

    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN read_at INTEGER DEFAULT NULL
            """.trimIndent()
        )
    }
}

val MIGRATION_6_7 = object : Migration(6, 7) {

    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN ai_prediction_label TEXT
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN ai_important_probability REAL
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN ai_score_delta INTEGER
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN ai_model_version TEXT
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN ai_evaluated_at INTEGER
            """.trimIndent()
        )
    }
}

val MIGRATION_7_8 = object : Migration(7, 8) {

    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """
            ALTER TABLE notification_feedback
            ADD COLUMN reason_code TEXT
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notification_feedback
            ADD COLUMN reason_text TEXT
            """.trimIndent()
        )
    }
}

val MIGRATION_8_9 = object : Migration(8, 9) {

    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN channel_id TEXT DEFAULT NULL
            """.trimIndent()
        )
    }
}
