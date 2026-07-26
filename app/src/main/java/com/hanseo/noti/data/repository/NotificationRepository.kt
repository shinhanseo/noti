package com.hanseo.noti.data.repository

import com.hanseo.noti.data.local.dao.NotificationDao
import com.hanseo.noti.data.mapper.toDomain
import com.hanseo.noti.data.mapper.toEntity
import com.hanseo.noti.domain.model.NotificationItem
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

class NotificationRepository(
    private val notificationDao: NotificationDao
) {
    suspend fun save(notification: NotificationItem) {
        notificationDao.upsert(notification.toEntity())
    }

    fun observeAll(): Flow<List<NotificationItem>> {
        return notificationDao.observeAll()
            .map { entities ->
                entities.map { entity ->
                    entity.toDomain()
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

    suspend fun deleteRemovedBefore(
        cutoffTime: Long
    ): Int {
        return notificationDao.deleteRemovedBefore(
            cutoffTime = cutoffTime
        )
    }
}
