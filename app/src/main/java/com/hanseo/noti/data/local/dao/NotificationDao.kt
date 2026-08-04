package com.hanseo.noti.data.local.dao

import androidx.room.Dao
import androidx.room.Query
import androidx.room.Upsert
import androidx.room.Insert
import androidx.room.Transaction
import com.hanseo.noti.data.local.entity.ImportanceReasonEntity
import com.hanseo.noti.data.local.entity.NotificationEntity
import kotlinx.coroutines.flow.Flow
import com.hanseo.noti.data.local.relation.NotificationWithReasons

@Dao
interface NotificationDao {
    @Upsert
    suspend fun upsert(notification: NotificationEntity)

    @Insert
    suspend fun insertReasons(
        reasons: List<ImportanceReasonEntity>
    )

    @Query(
        """
    DELETE FROM importance_reasons
    WHERE notification_key = :notificationKey
    """
    )
    suspend fun deleteReasonsByNotificationKey(
        notificationKey: String
    )

    @Transaction
    suspend fun upsertWithReasons(
        notification: NotificationEntity,
        reasons: List<ImportanceReasonEntity>
    ) {
        upsert(notification)

        deleteReasonsByNotificationKey(
            notificationKey = notification.notificationKey
        )

        if (reasons.isNotEmpty()) {
            insertReasons(reasons)
        }
    }

    @Query(
        """
        SELECT *
        FROM notifications
        ORDER BY posted_at DESC
        """
    )
    fun observeAll(): Flow<List<NotificationEntity>>

    @Transaction
    @Query(
        """
    SELECT *
    FROM notifications
    ORDER BY posted_at DESC
    """
    )
    fun observeAllWithReasons(): Flow<List<NotificationWithReasons>>

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
      AND is_removed = 0
    """
    )
    suspend fun markAsRemoved(
        notificationKey: String,
        removedAt: Long
    ): Int

    @Query(
        """
    UPDATE notifications
    SET read_at = :readAt
    WHERE notification_key = :notificationKey
      AND read_at IS NULL
    """
    )
    suspend fun markAsRead(
        notificationKey: String,
        readAt: Long
    ): Int

    @Query(
        """
    UPDATE notifications
    SET read_at = NULL
    WHERE notification_key = :notificationKey
      AND read_at IS NOT NULL
    """
    )
    suspend fun markAsUnread(
        notificationKey: String
    ): Int

    @Query(
        """
    UPDATE notifications
    SET read_at = :readAt
    WHERE posted_at >= :startMillis
      AND posted_at < :endMillis
      AND read_at IS NULL
    """
    )
    suspend fun markAllAsReadBetween(
        startMillis: Long,
        endMillis: Long,
        readAt: Long
    ): Int

    @Query(
        """
    DELETE FROM notifications
    WHERE is_removed = 1
      AND removed_at IS NOT NULL
      AND removed_at < :cutoffTime
    """
    )
    suspend fun deleteRemovedBefore(
        cutoffTime: Long
    ): Int
}
