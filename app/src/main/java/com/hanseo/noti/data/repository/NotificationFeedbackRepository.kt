package com.hanseo.noti.data.repository

import com.hanseo.noti.data.local.dao.NotificationFeedbackDao
import com.hanseo.noti.data.local.entity.NotificationFeedbackEntity
import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.feedback.FeedbackReasonCode
import com.hanseo.noti.domain.feedback.NotificationFeedback
import com.hanseo.noti.domain.model.ClassifiedNotification
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationFeedbackRepository @Inject constructor(
    private val feedbackDao: NotificationFeedbackDao
) {

    suspend fun save(
        classifiedNotification: ClassifiedNotification,
        label: FeedbackLabel,
        reasonCode: FeedbackReasonCode,
        reasonText: String? = null,
        feedbackAt: Long = System.currentTimeMillis()
    ) {
        val notification =
            classifiedNotification.notification

        val importance =
            classifiedNotification.importance

        val feedbackEntity =
            NotificationFeedbackEntity(
                notificationKey =
                    notification.key,

                userLabel =
                    label.name,

                originalLevel =
                    importance.level.name,

                originalScore =
                    importance.score,

                policyVersion =
                    importance.policyVersion,

                feedbackAt =
                    feedbackAt,

                reasonCode =
                    reasonCode.name,

                reasonText =
                    reasonText
                        ?.trim()
                        ?.takeIf { text ->
                            text.isNotEmpty()
                        }
            )

        feedbackDao.upsert(
            feedback = feedbackEntity
        )
    }

    fun observeAll():
            Flow<Map<String, NotificationFeedback>> {

        return feedbackDao
            .observeAll()
            .map { feedbackEntities ->
                feedbackEntities.mapNotNull { entity ->
                    val label =
                        FeedbackLabel.entries
                            .firstOrNull { label ->
                                label.name ==
                                        entity.userLabel
                            }
                            ?: return@mapNotNull null

                    val reasonCode =
                        entity.reasonCode?.let { code ->
                            FeedbackReasonCode.entries
                                .firstOrNull { reason ->
                                    reason.name == code
                                }
                        }

                    entity.notificationKey to
                        NotificationFeedback(
                            label = label,
                            reasonCode = reasonCode,
                            reasonText = entity.reasonText
                        )
                }.toMap()
            }
    }

    fun observeAllLabels():
            Flow<Map<String, FeedbackLabel>> {

        return observeAll().map { feedbackByKey ->
            feedbackByKey.mapValues { entry ->
                entry.value.label
            }
        }
    }

    fun observeLabel(
        notificationKey: String
    ): Flow<FeedbackLabel?> {

        return feedbackDao
            .observeByNotificationKey(
                notificationKey = notificationKey
            )
            .map { entity ->
                entity?.let {
                    FeedbackLabel.entries
                        .firstOrNull { label ->
                            label.name ==
                                    it.userLabel
                        }
                }
            }
    }

    suspend fun delete(
        notificationKey: String
    ) {
        feedbackDao.deleteByNotificationKey(
            notificationKey = notificationKey
        )
    }
}
