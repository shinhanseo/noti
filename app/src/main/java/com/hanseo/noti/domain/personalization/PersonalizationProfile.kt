package com.hanseo.noti.domain.personalization

import com.hanseo.noti.domain.topic.NotificationTopic

data class PersonalizationProfile (
    val scope: PersonalizationScope,
    val packageName: String,
    val channelId: String?,
    val topic: NotificationTopic?,
    val importantCount: Int,
    val generalCount: Int,
    val profileVersion: String,
) {
    val totalFeedbackCount: Int
        get() = importantCount + generalCount

    init {
        require(packageName.isNotBlank()) {
            "packageName must not be blank"
        }

        require(importantCount >= 0) {
            "importantCount must not be negative"
        }

        require(generalCount >= 0) {
            "generalCount must not be negative"
        }

        require(totalFeedbackCount > 0) {
            "totalFeedbackCount must be positive"
        }

        require(hasValidDimensions()) {
            "scope and dimensions do not match"
        }
    }

    private fun hasValidDimensions(): Boolean {
        val hasChannel =
            !channelId.isNullOrBlank()

        val hasTopic =
            topic != null &&
                    topic != NotificationTopic.UNKNOWN

        return when (scope) {
            PersonalizationScope.APP_CHANNEL_TOPIC ->
                hasChannel && hasTopic

            PersonalizationScope.APP_TOPIC ->
                !hasChannel && hasTopic

            PersonalizationScope.APP_CHANNEL ->
                hasChannel && !hasTopic

            PersonalizationScope.APP ->
                !hasChannel && !hasTopic
        }
    }
}
