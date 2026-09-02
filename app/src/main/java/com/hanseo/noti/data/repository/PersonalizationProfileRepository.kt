package com.hanseo.noti.data.repository

import com.hanseo.noti.data.local.dao.PersonalizationProfileDao
import com.hanseo.noti.data.local.entity.PersonalizationProfileEntity
import com.hanseo.noti.domain.personalization.PersonalizationProfile
import com.hanseo.noti.domain.personalization.PersonalizationScope
import com.hanseo.noti.domain.topic.NotificationTopic
import javax.inject.Inject
import javax.inject.Singleton
import com.hanseo.noti.domain.personalization.PersonalizationProfileProvider

@Singleton
class PersonalizationProfileRepository
@Inject constructor(
    private val profileDao: PersonalizationProfileDao
) : PersonalizationProfileProvider {

    override
    suspend fun findMatchingProfiles(
        packageName: String,
        channelId: String?,
        topic: NotificationTopic
    ): List<PersonalizationProfile> {
        val normalizedPackageName =
            packageName.trim()

        if (normalizedPackageName.isEmpty()) {
            return emptyList()
        }

        val normalizedChannelId =
            channelId
                ?.trim()
                ?.takeIf { it.isNotEmpty() }

        val normalizedTopic =
            topic.takeIf {
                it != NotificationTopic.UNKNOWN
            }

        return profileDao
            .findByPackageName(normalizedPackageName)
            .mapNotNull { entity ->
                entity.toDomainOrNull()
            }
            .filter { profile ->
                profile.matches(
                    channelId = normalizedChannelId,
                    topic = normalizedTopic
                )
            }
            .sortedBy { profile ->
                scopePriority(profile.scope)
            }
    }

    private fun PersonalizationProfile.matches(
        channelId: String?,
        topic: NotificationTopic?
    ): Boolean {
        return when (scope) {
            PersonalizationScope.APP_CHANNEL_TOPIC ->
                this.channelId == channelId &&
                        this.topic == topic

            PersonalizationScope.APP_TOPIC ->
                this.topic == topic

            PersonalizationScope.APP_CHANNEL ->
                this.channelId == channelId

            PersonalizationScope.APP ->
                true
        }
    }

    private fun PersonalizationProfileEntity.toDomainOrNull():
            PersonalizationProfile? {

        val parsedScope =
            PersonalizationScope.entries
                .firstOrNull { scope ->
                    scope.name == this.scope
                }
                ?: return null

        val parsedChannelId =
            channelKey.takeIf { it.isNotBlank() }

        val parsedTopic =
            topicKey
                .takeIf { it.isNotBlank() }
                ?.let { topicName ->
                    NotificationTopic.entries
                        .firstOrNull { topic ->
                            topic.name == topicName
                        }
                }

        return runCatching {
            PersonalizationProfile(
                scope = parsedScope,
                packageName = packageName,
                channelId = parsedChannelId,
                topic = parsedTopic,
                importantCount = importantCount,
                generalCount = generalCount,
                profileVersion = profileVersion
            )
        }.getOrNull()
    }

    private fun scopePriority(
        scope: PersonalizationScope
    ): Int {
        return when (scope) {
            PersonalizationScope.APP_CHANNEL_TOPIC -> 0
            PersonalizationScope.APP_TOPIC -> 1
            PersonalizationScope.APP_CHANNEL -> 2
            PersonalizationScope.APP -> 3
        }
    }
}