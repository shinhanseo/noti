package com.hanseo.noti.data.repository

import com.hanseo.noti.data.local.dao.NotificationDao
import com.hanseo.noti.data.mapper.toClassifiedNotification
import com.hanseo.noti.data.mapper.toEntity
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.data.mapper.toReasonEntities

class NotificationRepository(
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

    suspend fun deleteRemovedBefore(
        cutoffTime: Long
    ): Int {
        return notificationDao.deleteRemovedBefore(
            cutoffTime = cutoffTime
        )
    }
}
