package com.hanseo.noti.notification

import com.hanseo.noti.domain.model.NotificationItem

enum class NotificationIgnoreReason {
    EMPTY_CONTENT,
    GROUP_SUMMARY,
}

object NotificationFilter {
    fun findIgnoreReason(
        item: NotificationItem
    ): NotificationIgnoreReason? {
        return when {
            item.isGroupSummary ->
                NotificationIgnoreReason.GROUP_SUMMARY
            item.title.isNullOrBlank() && item.body.isNullOrBlank() ->
                NotificationIgnoreReason.EMPTY_CONTENT
            else -> null
        }
    }
}
