package com.hanseo.noti.domain.personalization

import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.feedback.FeedbackReasonCode
import com.hanseo.noti.domain.topic.NotificationTopic

class PersonalizationContributionFactory {

    fun create(
        packageName: String,
        channelId: String?,
        detectedTopic: NotificationTopic,
        label: FeedbackLabel,
        reasonCode: FeedbackReasonCode,
        feedbackAt: Long
    ): List<PersonalizationContribution> {
        val normalizedPackageName =
            packageName.trim()

        if (normalizedPackageName.isEmpty()) {
            return emptyList()
        }

        val normalizedChannelKey =
            channelId
                ?.trim()
                ?.takeIf { channel ->
                    channel.isNotEmpty()
                }

        val topic =
            resolveTopic(
                detectedTopic = detectedTopic,
                reasonCode = reasonCode
            )

        val dimensions =
            when (reasonCode) {
                FeedbackReasonCode.SCHEDULE_DEADLINE,
                FeedbackReasonCode.ACTION_REQUEST,
                FeedbackReasonCode.FINANCE_SECURITY,
                FeedbackReasonCode.DELIVERY_RESERVATION,
                FeedbackReasonCode.PROMOTIONAL,
                FeedbackReasonCode.INFORMATIONAL ->
                    createTopicDimensions(
                        packageName =
                            normalizedPackageName,
                        channelKey =
                            normalizedChannelKey,
                        topic =
                            topic
                    )

                FeedbackReasonCode.IMPORTANT_SOURCE,
                FeedbackReasonCode.UNIMPORTANT_SOURCE ->
                    createSourceDimensions(
                        packageName =
                            normalizedPackageName,
                        channelKey =
                            normalizedChannelKey
                    )

                FeedbackReasonCode.REPEATED,
                FeedbackReasonCode.NOT_TIME_SENSITIVE,
                FeedbackReasonCode.OTHER ->
                    emptyList()
            }

        val importantDelta =
            if (label == FeedbackLabel.IMPORTANT) {
                1
            } else {
                0
            }

        val generalDelta =
            if (label == FeedbackLabel.GENERAL) {
                1
            } else {
                0
            }

        return dimensions.map { dimension ->
            PersonalizationContribution(
                scope = dimension.scope,
                packageName = dimension.packageName,
                channelKey = dimension.channelKey,
                topicKey = dimension.topicKey,
                importantDelta = importantDelta,
                generalDelta = generalDelta,
                feedbackAt = feedbackAt,
                profileVersion = PROFILE_VERSION
            )
        }
    }

    private fun createTopicDimensions(
        packageName: String,
        channelKey: String?,
        topic: NotificationTopic?
    ): List<ProfileDimension> {
        if (
            topic == null ||
            topic == NotificationTopic.UNKNOWN
        ) {
            return emptyList()
        }

        val dimensions =
            mutableListOf(
                ProfileDimension(
                    scope =
                        PersonalizationScope.APP_TOPIC,
                    packageName =
                        packageName,
                    channelKey =
                        EMPTY_KEY,
                    topicKey =
                        topic.name
                )
            )

        if (channelKey != null) {
            dimensions.add(
                index = 0,
                element =
                    ProfileDimension(
                        scope =
                            PersonalizationScope
                                .APP_CHANNEL_TOPIC,
                        packageName =
                            packageName,
                        channelKey =
                            channelKey,
                        topicKey =
                            topic.name
                    )
            )
        }

        return dimensions
    }

    private fun createSourceDimensions(
        packageName: String,
        channelKey: String?
    ): List<ProfileDimension> {
        val dimensions =
            mutableListOf(
                ProfileDimension(
                    scope =
                        PersonalizationScope.APP,
                    packageName =
                        packageName,
                    channelKey =
                        EMPTY_KEY,
                    topicKey =
                        EMPTY_KEY
                )
            )

        if (channelKey != null) {
            dimensions.add(
                index = 0,
                element =
                    ProfileDimension(
                        scope =
                            PersonalizationScope.APP_CHANNEL,
                        packageName =
                            packageName,
                        channelKey =
                            channelKey,
                        topicKey =
                            EMPTY_KEY
                    )
            )
        }

        return dimensions
    }

    private fun resolveTopic(
        detectedTopic: NotificationTopic,
        reasonCode: FeedbackReasonCode
    ): NotificationTopic? {
        return when (reasonCode) {
            FeedbackReasonCode.SCHEDULE_DEADLINE ->
                NotificationTopic.SCHEDULE

            FeedbackReasonCode.ACTION_REQUEST ->
                NotificationTopic.ACTION_REQUEST

            FeedbackReasonCode.FINANCE_SECURITY ->
                NotificationTopic.FINANCE_SECURITY

            FeedbackReasonCode.PROMOTIONAL ->
                NotificationTopic.PROMOTIONAL

            FeedbackReasonCode.INFORMATIONAL ->
                NotificationTopic.INFORMATIONAL

            FeedbackReasonCode.DELIVERY_RESERVATION ->
                detectedTopic.takeIf { topic ->
                    topic == NotificationTopic.DELIVERY ||
                            topic == NotificationTopic.RESERVATION
                }

            else ->
                null
        }
    }

    private data class ProfileDimension(
        val scope: PersonalizationScope,
        val packageName: String,
        val channelKey: String,
        val topicKey: String
    )

    private companion object {
        const val EMPTY_KEY = ""
        const val PROFILE_VERSION = "1"
    }
}