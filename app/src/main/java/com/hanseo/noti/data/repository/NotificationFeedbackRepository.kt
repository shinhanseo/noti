package com.hanseo.noti.data.repository

import androidx.room.withTransaction
import com.hanseo.noti.data.local.NotiDatabase
import com.hanseo.noti.data.local.dao.NotificationFeedbackDao
import com.hanseo.noti.data.local.dao.PersonalizationProfileDao
import com.hanseo.noti.data.local.entity.NotificationFeedbackEntity
import com.hanseo.noti.data.local.entity.PersonalizationProfileEntity
import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.feedback.FeedbackReasonCode
import com.hanseo.noti.domain.feedback.NotificationFeedback
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.domain.personalization.PersonalizationContribution
import com.hanseo.noti.domain.personalization.PersonalizationContributionFactory
import com.hanseo.noti.domain.topic.NotificationTopic
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class NotificationFeedbackRepository
@Inject constructor(
    private val database: NotiDatabase,
    private val feedbackDao: NotificationFeedbackDao,
    private val profileDao: PersonalizationProfileDao
) {

    private val contributionFactory =
        PersonalizationContributionFactory()

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
                        },

                packageName =
                    notification.packageName,

                channelId =
                    notification.channelId,

                primaryTopic =
                    classifiedNotification
                        .topicResult
                        .primaryTopic
                        .name,

                topicPolicyVersion =
                    classifiedNotification
                        .topicResult
                        .policyVersion
            )

        val newContributions =
            contributionFactory.create(
                packageName =
                    notification.packageName,

                channelId =
                    notification.channelId,

                detectedTopic =
                    classifiedNotification
                        .topicResult
                        .primaryTopic,

                label =
                    label,

                reasonCode =
                    reasonCode,

                feedbackAt =
                    feedbackAt
            )

        database.withTransaction {
            val previousFeedback =
                feedbackDao.findByNotificationKey(
                    notificationKey = notification.key
                )

            if (previousFeedback != null) {
                val previousContributions =
                    createContributions(
                        feedback = previousFeedback
                    )

                previousContributions.forEach { contribution ->
                    profileDao.removeFeedback(
                        profile =
                            contribution.toProfileEntity()
                    )
                }
            }

            feedbackDao.upsert(
                feedback = feedbackEntity
            )

            newContributions.forEach { contribution ->
                profileDao.addFeedback(
                    profile =
                        contribution.toProfileEntity()
                )
            }
        }
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
        database.withTransaction {
            val previousFeedback =
                feedbackDao.findByNotificationKey(
                    notificationKey = notificationKey
                )

            if (previousFeedback != null) {
                val previousContributions =
                    createContributions(
                        feedback = previousFeedback
                    )

                previousContributions.forEach { contribution ->
                    profileDao.removeFeedback(
                        profile =
                            contribution.toProfileEntity()
                    )
                }
            }

            feedbackDao.deleteByNotificationKey(
                notificationKey = notificationKey
            )
        }
    }

    private fun createContributions(
        feedback: NotificationFeedbackEntity
    ): List<PersonalizationContribution> {
        val packageName =
            feedback.packageName
                ?: return emptyList()

        val label =
            FeedbackLabel.entries
                .firstOrNull { label ->
                    label.name == feedback.userLabel
                }
                ?: return emptyList()

        val reasonCode =
            feedback.reasonCode?.let { code ->
                FeedbackReasonCode.entries
                    .firstOrNull { reason ->
                        reason.name == code
                    }
            }
                ?: return emptyList()

        val detectedTopic =
            feedback.primaryTopic?.let { topicName ->
                NotificationTopic.entries
                    .firstOrNull { topic ->
                        topic.name == topicName
                    }
            }
                ?: NotificationTopic.UNKNOWN

        return contributionFactory.create(
            packageName = packageName,
            channelId = feedback.channelId,
            detectedTopic = detectedTopic,
            label = label,
            reasonCode = reasonCode,
            feedbackAt = feedback.feedbackAt
        )
    }

    private fun PersonalizationContribution
            .toProfileEntity():
            PersonalizationProfileEntity {

        return PersonalizationProfileEntity(
            scope = scope.name,
            packageName = packageName,
            channelKey = channelKey,
            topicKey = topicKey,
            importantCount = importantDelta,
            generalCount = generalDelta,
            lastFeedbackAt = feedbackAt,
            profileVersion = profileVersion
        )
    }
}