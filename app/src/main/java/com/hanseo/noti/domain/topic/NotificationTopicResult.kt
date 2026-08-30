package com.hanseo.noti.domain.topic

data class NotificationTopicResult(
    val primaryTopic: NotificationTopic,
    val topics: Set<NotificationTopic>,
    val policyVersion: String
) {
    init {
        require(topics.isNotEmpty()) {
            "topics must not be empty"
        }

        require(primaryTopic in topics) {
            "primaryTopic must be included in topics"
        }
    }

    companion object {
        fun unknown(
            policyVersion: String
        ): NotificationTopicResult {
            return NotificationTopicResult(
                primaryTopic = NotificationTopic.UNKNOWN,
                topics = setOf(NotificationTopic.UNKNOWN),
                policyVersion = policyVersion
            )
        }
    }
}