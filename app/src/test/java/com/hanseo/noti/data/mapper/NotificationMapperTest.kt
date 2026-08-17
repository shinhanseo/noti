package com.hanseo.noti.data.mapper

import com.hanseo.noti.data.local.entity.NotificationEntity
import com.hanseo.noti.data.local.relation.NotificationWithReasons
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceReason
import com.hanseo.noti.domain.importance.ImportanceReasonType
import com.hanseo.noti.domain.importance.ImportanceResult
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.domain.model.NotificationItem
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import com.hanseo.noti.domain.importance.AiImportanceLabel
import com.hanseo.noti.domain.importance.AiImportancePrediction

class NotificationMapperTest {

    @Test
    fun classifiedNotification_roundTrip_preservesNotificationAndImportance() {
        val source = ClassifiedNotification(
            notification = NotificationItem(
                key = "notification-key",
                packageName = "com.example.calendar",
                title = "일정 알림",
                body = "회의가 7시에 있습니다",
                postedAt = 1_000L,
                category = "event",
                isOngoing = false,
                isGroupSummary = false,
                isRemoved = false,
                removedAt = null
            ),
            importance = ImportanceResult(
                score = 45,
                level = ImportanceLevel.IMPORTANT,
                reasons = listOf(
                    ImportanceReason(
                        type = ImportanceReasonType.AUTOMATIC_RULE,
                        scoreDelta = 25,
                        ruleId = "event_or_reminder",
                        description = "일정이나 리마인더 알림이에요"
                    ),
                    ImportanceReason(
                        type = ImportanceReasonType.AUTOMATIC_RULE,
                        scoreDelta = 20,
                        ruleId = "date_or_time",
                        description = "일정이나 마감 시간이 함께 있어요"
                    )
                ),
                isForced = false,
                policyVersion = "1",
                evaluatedAtMillis = 2_000L
            ),
            aiPrediction = AiImportancePrediction(
                label = AiImportanceLabel.ATTENTION_WORTHY,
                importantProbability = 0.82f,
                scoreDelta = 15,
                modelVersion = "noti_embeddinggemma_actionability_v1",
                evaluatedAtMillis = 2_100L
            )
        )

        val notificationEntity = source.toEntity()
        val reasonEntities = source.toReasonEntities()

        val restored = NotificationWithReasons(
            notification = notificationEntity,
            reasons = reasonEntities.reversed()
        ).toClassifiedNotification()

        assertEquals(source, restored)
    }

    @Test
    fun notificationWithoutImportance_returnsNull() {
        val notificationWithReasons = NotificationWithReasons(
            notification = NotificationEntity(
                notificationKey = "legacy-notification-key",
                packageName = "com.example.legacy",
                title = "기존 알림",
                body = null,
                postedAt = 3_000L,
                category = null,
                isOngoing = false
            ),
            reasons = emptyList()
        )

        val restored =
            notificationWithReasons.toClassifiedNotification()

        assertNull(restored)
    }
}
