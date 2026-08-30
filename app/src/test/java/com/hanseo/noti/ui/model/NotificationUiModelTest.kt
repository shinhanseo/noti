package com.hanseo.noti.ui.model

import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.feedback.NotificationFeedback
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceResult
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.domain.model.NotificationItem
import com.hanseo.noti.domain.topic.NotificationTopicResult
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class NotificationUiModelTest {

    @Test
    fun importantFeedback_overridesGeneralClassification() {
        val uiModel = createUiModel(
            originalLevel = ImportanceLevel.GENERAL,
            feedbackLabel = FeedbackLabel.IMPORTANT
        )

        assertTrue(uiModel.isEffectivelyImportant)
    }

    @Test
    fun generalFeedback_overridesImportantClassification() {
        val uiModel = createUiModel(
            originalLevel = ImportanceLevel.IMPORTANT,
            feedbackLabel = FeedbackLabel.GENERAL
        )

        assertFalse(uiModel.isEffectivelyImportant)
    }

    @Test
    fun missingFeedback_usesOriginalClassification() {
        val importantUiModel = createUiModel(
            originalLevel = ImportanceLevel.IMPORTANT,
            feedbackLabel = null
        )

        val generalUiModel = createUiModel(
            originalLevel = ImportanceLevel.GENERAL,
            feedbackLabel = null
        )

        assertTrue(importantUiModel.isEffectivelyImportant)
        assertFalse(generalUiModel.isEffectivelyImportant)
    }

    private fun createUiModel(
        originalLevel: ImportanceLevel,
        feedbackLabel: FeedbackLabel?
    ): NotificationUiModel {
        val notification = NotificationItem(
            key = "notification-key",
            packageName = "com.example.app",
            title = "알림 제목",
            body = "알림 본문",
            postedAt = 1_000L,
            category = null,
            channelId = null,
            isOngoing = false,
            isGroupSummary = false
        )

        val importance = ImportanceResult(
            score = if (
                originalLevel == ImportanceLevel.IMPORTANT
            ) {
                40
            } else {
                0
            },
            level = originalLevel,
            reasons = emptyList(),
            isForced = false,
            policyVersion = "test-policy",
            evaluatedAtMillis = 1_000L
        )

        return NotificationUiModel(
            classifiedNotification =
                ClassifiedNotification(
                    notification = notification,
                    importance = importance,
                    topicResult =
                        NotificationTopicResult.unknown(
                            policyVersion = "test-topic-policy"
                        )
                ),
            appName = "테스트 앱",
            appIcon = null,
            feedback = feedbackLabel?.let { label ->
                NotificationFeedback(
                    label = label,
                    reasonCode = null,
                    reasonText = null
                )
            }
        )
    }
}
