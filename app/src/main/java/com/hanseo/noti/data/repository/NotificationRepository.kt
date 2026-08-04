package com.hanseo.noti.data.repository

import com.hanseo.noti.data.local.dao.NotificationDao
import com.hanseo.noti.data.mapper.toClassifiedNotification
import com.hanseo.noti.data.mapper.toEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.data.mapper.toReasonEntities
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationRepository @Inject constructor(
    private val notificationDao: NotificationDao
) {
    suspend fun save(
        classifiedNotification: ClassifiedNotification
    ) {
        val notificationEntity =
            classifiedNotification.toEntity()

        val reasonEntities =
            classifiedNotification.toReasonEntities()

        notificationDao.upsertWithReasons(
            notification = notificationEntity,
            reasons = reasonEntities
        )
    }

    fun observeAll(): Flow<List<ClassifiedNotification>> {
        return notificationDao.observeAllWithReasons()
            .map { notificationsWithReasons ->
                notificationsWithReasons.mapNotNull { notificationWithReasons ->
                    notificationWithReasons.toClassifiedNotification()
                }
            }
    }

    suspend fun deleteByKey(notificationKey: String) {
        notificationDao.deleteByKey(notificationKey)
    }

    suspend fun markAsRemoved(
        notificationKey: String,
        removedAt: Long
    ): Boolean {
        val updatedRowCount = notificationDao.markAsRemoved(
            notificationKey = notificationKey,
            removedAt = removedAt
        )

        return updatedRowCount > 0
    }

    suspend fun markAsRead(
        notificationKey: String,
        readAt: Long = System.currentTimeMillis()
    ): Boolean {
        val updatedRowCount = notificationDao.markAsRead(
            notificationKey = notificationKey,
            readAt = readAt
        )

        return updatedRowCount > 0
    }

    suspend fun markAsUnread(
        notificationKey: String
    ): Boolean {
        val updatedRowCount = notificationDao.markAsUnread(
            notificationKey = notificationKey
        )

        return updatedRowCount > 0
    }

    suspend fun markAllAsReadBetween(
        startMillis: Long,
        endMillis: Long,
        readAt: Long = System.currentTimeMillis()
    ): Int {
        return notificationDao.markAllAsReadBetween(
            startMillis = startMillis,
            endMillis = endMillis,
            readAt = readAt
        )
    }

    suspend fun deleteRemovedBefore(
        cutoffTime: Long
    ): Int {
        return notificationDao.deleteRemovedBefore(
            cutoffTime = cutoffTime
        )
    }
}
