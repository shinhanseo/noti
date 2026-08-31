package com.hanseo.noti.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import com.hanseo.noti.data.local.entity.PersonalizationProfileEntity

@Dao
interface PersonalizationProfileDao {

    @Query(
        """
        SELECT *
        FROM personalization_profiles
        WHERE scope = :scope
          AND package_name = :packageName
          AND channel_key = :channelKey
          AND topic_key = :topicKey
        LIMIT 1
        """
    )
    suspend fun findExact(
        scope: String,
        packageName: String,
        channelKey: String,
        topicKey: String
    ): PersonalizationProfileEntity?

    @Query(
        """
        SELECT *
        FROM personalization_profiles
        WHERE package_name = :packageName
        """
    )
    suspend fun findByPackageName(
        packageName: String
    ): List<PersonalizationProfileEntity>

    @Query(
        """
        UPDATE personalization_profiles
        SET important_count =
                MAX(0, important_count + :importantDelta),
            general_count =
                MAX(0, general_count + :generalDelta),
            last_feedback_at = :feedbackAt,
            profile_version = :profileVersion
        WHERE scope = :scope
          AND package_name = :packageName
          AND channel_key = :channelKey
          AND topic_key = :topicKey
        """
    )
    suspend fun applyDelta(
        scope: String,
        packageName: String,
        channelKey: String,
        topicKey: String,
        importantDelta: Int,
        generalDelta: Int,
        feedbackAt: Long,
        profileVersion: String
    ): Int

    @Insert(
        onConflict = OnConflictStrategy.IGNORE
    )
    suspend fun insertIfAbsent(
        profile: PersonalizationProfileEntity
    ): Long

    @Query(
        """
        DELETE FROM personalization_profiles
        WHERE important_count = 0
          AND general_count = 0
        """
    )
    suspend fun deleteEmptyProfiles()

    @Transaction
    suspend fun addFeedback(
        profile: PersonalizationProfileEntity
    ) {
        val updatedRowCount =
            applyDelta(
                scope = profile.scope,
                packageName = profile.packageName,
                channelKey = profile.channelKey,
                topicKey = profile.topicKey,
                importantDelta = profile.importantCount,
                generalDelta = profile.generalCount,
                feedbackAt = profile.lastFeedbackAt,
                profileVersion = profile.profileVersion
            )

        if (updatedRowCount > 0) {
            return
        }

        val insertedRowId =
            insertIfAbsent(profile)

        if (insertedRowId == INSERT_FAILED) {
            applyDelta(
                scope = profile.scope,
                packageName = profile.packageName,
                channelKey = profile.channelKey,
                topicKey = profile.topicKey,
                importantDelta = profile.importantCount,
                generalDelta = profile.generalCount,
                feedbackAt = profile.lastFeedbackAt,
                profileVersion = profile.profileVersion
            )
        }
    }

    @Transaction
    suspend fun removeFeedback(
        profile: PersonalizationProfileEntity
    ) {
        applyDelta(
            scope = profile.scope,
            packageName = profile.packageName,
            channelKey = profile.channelKey,
            topicKey = profile.topicKey,
            importantDelta = -profile.importantCount,
            generalDelta = -profile.generalCount,
            feedbackAt = profile.lastFeedbackAt,
            profileVersion = profile.profileVersion
        )

        deleteEmptyProfiles()
    }

    private companion object {
        const val INSERT_FAILED = -1L
    }
}