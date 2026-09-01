package com.hanseo.noti.data.repository

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.hanseo.noti.data.local.NotiDatabase
import com.hanseo.noti.data.mapper.toEntity
import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.feedback.FeedbackReasonCode
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceResult
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.domain.model.NotificationItem
import com.hanseo.noti.domain.personalization.PersonalizationScope
import com.hanseo.noti.domain.topic.NotificationTopic
import com.hanseo.noti.domain.topic.NotificationTopicResult
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class NotificationFeedbackRepositoryTest {

    private lateinit var database: NotiDatabase
    private lateinit var repository:
            NotificationFeedbackRepository

    @Before
    fun setUp() {
        val context =
            ApplicationProvider.getApplicationContext<Context>()

        database =
            Room.inMemoryDatabaseBuilder(
                context,
                NotiDatabase::class.java
            ).build()

        repository =
            NotificationFeedbackRepository(
                database = database,
                feedbackDao =
                    database.notificationFeedbackDao(),
                profileDao =
                    database.personalizationProfileDao()
            )
    }

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun saveChangeAndDeleteFeedback_updatesProfilesConsistently() =
        runBlocking {
            val classifiedNotification =
                createClassifiedNotification()

            database.notificationDao().upsert(
                notification =
                    classifiedNotification.toEntity()
            )

            repository.save(
                classifiedNotification =
                    classifiedNotification,
                label = FeedbackLabel.IMPORTANT,
                reasonCode =
                    FeedbackReasonCode.IMPORTANT_SOURCE,
                feedbackAt = 1_000L
            )

            assertSourceProfiles(
                expectedImportantCount = 1,
                expectedGeneralCount = 0
            )
            assertEquals(
                FeedbackLabel.IMPORTANT.name,
                database.notificationFeedbackDao()
                    .findByNotificationKey(NOTIFICATION_KEY)
                    ?.userLabel
            )

            repository.save(
                classifiedNotification =
                    classifiedNotification,
                label = FeedbackLabel.GENERAL,
                reasonCode =
                    FeedbackReasonCode.UNIMPORTANT_SOURCE,
                feedbackAt = 2_000L
            )

            assertSourceProfiles(
                expectedImportantCount = 0,
                expectedGeneralCount = 1
            )
            assertEquals(
                FeedbackLabel.GENERAL.name,
                database.notificationFeedbackDao()
                    .findByNotificationKey(NOTIFICATION_KEY)
                    ?.userLabel
            )

            repository.delete(
                notificationKey = NOTIFICATION_KEY
            )

            assertNull(
                findProfile(
                    scope = PersonalizationScope.APP_CHANNEL
                )
            )
            assertNull(
                findProfile(
                    scope = PersonalizationScope.APP
                )
            )
            assertNull(
                database.notificationFeedbackDao()
                    .findByNotificationKey(NOTIFICATION_KEY)
            )
        }

    private suspend fun assertSourceProfiles(
        expectedImportantCount: Int,
        expectedGeneralCount: Int
    ) {
        val channelProfile =
            findProfile(
                scope = PersonalizationScope.APP_CHANNEL
            )

        val appProfile =
            findProfile(
                scope = PersonalizationScope.APP
            )

        assertEquals(
            expectedImportantCount,
            channelProfile?.importantCount
        )
        assertEquals(
            expectedGeneralCount,
            channelProfile?.generalCount
        )
        assertEquals(
            expectedImportantCount,
            appProfile?.importantCount
        )
        assertEquals(
            expectedGeneralCount,
            appProfile?.generalCount
        )
    }

    private suspend fun findProfile(
        scope: PersonalizationScope
    ) = database.personalizationProfileDao()
        .findExact(
            scope = scope.name,
            packageName = PACKAGE_NAME,
            channelKey =
                if (
                    scope == PersonalizationScope.APP_CHANNEL
                ) {
                    CHANNEL_ID
                } else {
                    ""
                },
            topicKey = ""
        )

    private fun createClassifiedNotification():
            ClassifiedNotification {
        return ClassifiedNotification(
            notification = NotificationItem(
                key = NOTIFICATION_KEY,
                packageName = PACKAGE_NAME,
                title = "할인 안내",
                body = "오늘 사용할 수 있는 쿠폰이 도착했어요",
                postedAt = 500L,
                category = null,
                channelId = CHANNEL_ID,
                isOngoing = false,
                isGroupSummary = false
            ),
            importance = ImportanceResult(
                score = 0,
                level = ImportanceLevel.GENERAL,
                reasons = emptyList(),
                isForced = false,
                policyVersion = "1",
                evaluatedAtMillis = 500L
            ),
            topicResult = NotificationTopicResult(
                primaryTopic =
                    NotificationTopic.PROMOTIONAL,
                topics =
                    setOf(NotificationTopic.PROMOTIONAL),
                policyVersion = "1"
            )
        )
    }

    private companion object {
        const val NOTIFICATION_KEY =
            "feedback-repository-test-key"

        const val PACKAGE_NAME =
            "com.example.shopping"

        const val CHANNEL_ID =
            "promotion"
    }
}
