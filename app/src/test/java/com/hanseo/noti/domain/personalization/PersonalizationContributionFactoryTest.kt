package com.hanseo.noti.domain.personalization

import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.feedback.FeedbackReasonCode
import com.hanseo.noti.domain.topic.NotificationTopic
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PersonalizationContributionFactoryTest {

    private val factory =
        PersonalizationContributionFactory()

    @Test
    fun importantDeliveryWithChannel_createsTwoTopicContributions() {
        val contributions =
            factory.create(
                packageName = "com.coupang.mobile",
                channelId = "delivery",
                detectedTopic =
                    NotificationTopic.DELIVERY,
                label = FeedbackLabel.IMPORTANT,
                reasonCode =
                    FeedbackReasonCode
                        .DELIVERY_RESERVATION,
                feedbackAt = 1_000L
            )

        assertEquals(2, contributions.size)
        assertEquals(
            listOf(
                PersonalizationScope.APP_CHANNEL_TOPIC,
                PersonalizationScope.APP_TOPIC
            ),
            contributions.map { contribution ->
                contribution.scope
            }
        )

        contributions.forEach { contribution ->
            assertEquals(
                "com.coupang.mobile",
                contribution.packageName
            )
            assertEquals("DELIVERY", contribution.topicKey)
            assertEquals(1, contribution.importantDelta)
            assertEquals(0, contribution.generalDelta)
        }
    }

    @Test
    fun unimportantSource_createsAppAndChannelContributions() {
        val contributions =
            factory.create(
                packageName = "com.example.shopping",
                channelId = "promotion",
                detectedTopic =
                    NotificationTopic.PROMOTIONAL,
                label = FeedbackLabel.GENERAL,
                reasonCode =
                    FeedbackReasonCode.UNIMPORTANT_SOURCE,
                feedbackAt = 2_000L
            )

        assertEquals(
            listOf(
                PersonalizationScope.APP_CHANNEL,
                PersonalizationScope.APP
            ),
            contributions.map { contribution ->
                contribution.scope
            }
        )

        contributions.forEach { contribution ->
            assertEquals(0, contribution.importantDelta)
            assertEquals(1, contribution.generalDelta)
            assertEquals("", contribution.topicKey)
        }
    }

    @Test
    fun scheduleReason_usesScheduleEvenWhenDetectedTopicIsUnknown() {
        val contributions =
            factory.create(
                packageName = "com.example.calendar",
                channelId = null,
                detectedTopic =
                    NotificationTopic.UNKNOWN,
                label = FeedbackLabel.IMPORTANT,
                reasonCode =
                    FeedbackReasonCode.SCHEDULE_DEADLINE,
                feedbackAt = 3_000L
            )

        assertEquals(1, contributions.size)
        assertEquals(
            PersonalizationScope.APP_TOPIC,
            contributions.single().scope
        )
        assertEquals(
            "SCHEDULE",
            contributions.single().topicKey
        )
    }

    @Test
    fun otherReason_createsNoContribution() {
        val contributions =
            factory.create(
                packageName = "com.example.app",
                channelId = "default",
                detectedTopic =
                    NotificationTopic.INFORMATIONAL,
                label = FeedbackLabel.GENERAL,
                reasonCode = FeedbackReasonCode.OTHER,
                feedbackAt = 4_000L
            )

        assertTrue(contributions.isEmpty())
    }
}
