package com.hanseo.noti.domain.personalization

import com.hanseo.noti.domain.topic.NotificationTopic

fun interface PersonalizationProfileProvider {

    suspend fun findMatchingProfiles(
        packageName: String,
        channelId: String?,
        topic: NotificationTopic
    ): List<PersonalizationProfile>
}