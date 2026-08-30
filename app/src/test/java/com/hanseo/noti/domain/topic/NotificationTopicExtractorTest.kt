package com.hanseo.noti.domain.topic

import com.hanseo.noti.domain.importance.ImportanceReason
import com.hanseo.noti.domain.importance.ImportanceReasonType
import org.junit.Assert.assertEquals
import org.junit.Test

class NotificationTopicExtractorTest {

    private val extractor = NotificationTopicExtractor()

    @Test
    fun deliveryAndDateRules_returnsDeliveryAsPrimaryTopic() {
        val result =
            extractor.extract(
                reasons = listOf(
                    automaticReason("delivery_status_change"),
                    automaticReason("date_or_time")
                )
            )

        assertEquals(
            NotificationTopic.DELIVERY,
            result.primaryTopic
        )
        assertEquals(
            setOf(
                NotificationTopic.DELIVERY,
                NotificationTopic.SCHEDULE
            ),
            result.topics
        )
        assertEquals("1", result.policyVersion)
    }

    @Test
    fun promotionalAndDeliveryRules_returnsPromotionalAsPrimaryTopic() {
        val result =
            extractor.extract(
                reasons = listOf(
                    automaticReason("delivery_status_change"),
                    automaticReason("promotional_content")
                )
            )

        assertEquals(
            NotificationTopic.PROMOTIONAL,
            result.primaryTopic
        )
        assertEquals(
            setOf(
                NotificationTopic.DELIVERY,
                NotificationTopic.PROMOTIONAL
            ),
            result.topics
        )
    }

    @Test
    fun userFeedbackReason_isIgnored() {
        val result =
            extractor.extract(
                reasons = listOf(
                    ImportanceReason(
                        type = ImportanceReasonType.USER_FEEDBACK,
                        scoreDelta = 0,
                        ruleId = "delivery_status_change",
                        description = "사용자 피드백"
                    )
                )
            )

        assertEquals(
            NotificationTopic.UNKNOWN,
            result.primaryTopic
        )
        assertEquals(
            setOf(NotificationTopic.UNKNOWN),
            result.topics
        )
    }

    @Test
    fun unknownRule_returnsUnknownTopic() {
        val result =
            extractor.extract(
                reasons = listOf(
                    automaticReason("unknown_rule")
                )
            )

        assertEquals(
            NotificationTopic.UNKNOWN,
            result.primaryTopic
        )
        assertEquals(
            setOf(NotificationTopic.UNKNOWN),
            result.topics
        )
    }

    @Test
    fun duplicatedRules_returnsTopicOnlyOnce() {
        val result =
            extractor.extract(
                reasons = listOf(
                    automaticReason("action_request"),
                    automaticReason("action_request"),
                    automaticReason("urgent_attention")
                )
            )

        assertEquals(
            NotificationTopic.ACTION_REQUEST,
            result.primaryTopic
        )
        assertEquals(
            setOf(NotificationTopic.ACTION_REQUEST),
            result.topics
        )
    }

    private fun automaticReason(
        ruleId: String
    ): ImportanceReason {
        return ImportanceReason(
            type = ImportanceReasonType.AUTOMATIC_RULE,
            scoreDelta = 0,
            ruleId = ruleId,
            description = "테스트 규칙"
        )
    }
}
