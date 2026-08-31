package com.hanseo.noti.data.local.dao

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import com.hanseo.noti.data.local.entity.NotificationFeedbackEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface NotificationFeedbackDao {

    @Upsert
    suspend fun upsert(
        feedback: NotificationFeedbackEntity
    )

    @Query(
        """
        SELECT *
        FROM notification_feedback
        ORDER BY feedback_at DESC
        """
    )
    fun observeAll():
            Flow<List<NotificationFeedbackEntity>>

    @Query(
        """
    SELECT *
    FROM notification_feedback
    WHERE notification_key = :notificationKey
    LIMIT 1
    """
    )
    suspend fun findByNotificationKey(
        notificationKey: String
    ): NotificationFeedbackEntity?

    @Query(
        """
        SELECT *
        FROM notification_feedback
        WHERE notification_key = :notificationKey
        LIMIT 1
        """
    )
    fun observeByNotificationKey(
        notificationKey: String
    ): Flow<NotificationFeedbackEntity?>

    @Query(
        """
        DELETE FROM notification_feedback
        WHERE notification_key = :notificationKey
        """
    )
    suspend fun deleteByNotificationKey(
        notificationKey: String
    )
}