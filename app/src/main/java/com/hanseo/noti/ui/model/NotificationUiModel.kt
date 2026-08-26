package com.hanseo.noti.ui.model

import android.graphics.Bitmap
import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.feedback.NotificationFeedback
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.model.ClassifiedNotification

data class NotificationUiModel(
    val classifiedNotification: ClassifiedNotification,
    val appName: String,
    val appIcon: Bitmap?,
    val feedback: NotificationFeedback? = null
) {
    val feedbackLabel: FeedbackLabel?
        get() = feedback?.label

    val isEffectivelyImportant: Boolean
        get() = when (feedbackLabel) {
            FeedbackLabel.IMPORTANT -> true
            FeedbackLabel.GENERAL -> false
            null ->
                classifiedNotification
                    .importance
                    .level == ImportanceLevel.IMPORTANT
        }
}
