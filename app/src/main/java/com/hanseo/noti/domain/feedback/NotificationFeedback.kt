package com.hanseo.noti.domain.feedback

data class NotificationFeedback(
    val label: FeedbackLabel,
    val reasonCode: FeedbackReasonCode?,
    val reasonText: String?
)
