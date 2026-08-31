package com.hanseo.noti.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index

@Entity(
    tableName = "personalization_profiles",
    primaryKeys = [
        "scope",
        "package_name",
        "channel_key",
        "topic_key"
    ],
    indices = [
        Index(
            value = ["package_name"]
        )
    ]
)
data class PersonalizationProfileEntity(

    @ColumnInfo(name = "scope")
    val scope: String,

    @ColumnInfo(name = "package_name")
    val packageName: String,

    @ColumnInfo(name = "channel_key")
    val channelKey: String,

    @ColumnInfo(name = "topic_key")
    val topicKey: String,

    @ColumnInfo(name = "important_count")
    val importantCount: Int,

    @ColumnInfo(name = "general_count")
    val generalCount: Int,

    @ColumnInfo(name = "last_feedback_at")
    val lastFeedbackAt: Long,

    @ColumnInfo(name = "profile_version")
    val profileVersion: String
)