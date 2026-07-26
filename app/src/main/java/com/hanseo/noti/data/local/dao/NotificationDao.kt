package com.hanseo.noti.data.local.dao

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import com.hanseo.noti.data.local.entity.NotificationEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface NotificationDao {
    @Upsert
    suspend fun upsert(notification: NotificationEntity)

    @Query(
        """
        SELECT *
        FROM notifications
        ORDER BY posted_at DESC
        """
    )
    fun observeAll(): Flow<List<NotificationEntity>>

    @Query(
        """
        DELETE FROM notifications
        WHERE notification_key = :notificationKey
        """
    )
    suspend fun deleteByKey(notificationKey: String)

    @Query(
        """
    UPDATE notifications
    SET is_removed = 1,
        removed_at = :removedAt
    WHERE notification_key = :notificationKey
    """
    )
    suspend fun markAsRemoved(
        notificationKey: String,
        removedAt: Long
    ): Int
}