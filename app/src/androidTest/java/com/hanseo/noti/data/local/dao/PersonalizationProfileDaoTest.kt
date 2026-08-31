package com.hanseo.noti.data.local.dao

import android.content.Context
import androidx.room.Room
import androidx.test.core.app.ApplicationProvider
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.hanseo.noti.data.local.NotiDatabase
import com.hanseo.noti.data.local.entity.PersonalizationProfileEntity
import kotlinx.coroutines.runBlocking
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class PersonalizationProfileDaoTest {

    private lateinit var database: NotiDatabase
    private lateinit var dao: PersonalizationProfileDao

    @Before
    fun setUp() {
        val context =
            ApplicationProvider.getApplicationContext<Context>()

        database =
            Room.inMemoryDatabaseBuilder(
                context,
                NotiDatabase::class.java
            ).build()

        dao = database.personalizationProfileDao()
    }

    @After
    fun tearDown() {
        database.close()
    }

    @Test
    fun addFeedback_accumulatesImportantCount() = runBlocking {
        val contribution = createImportantContribution()

        dao.addFeedback(contribution)
        dao.addFeedback(
            contribution.copy(
                lastFeedbackAt = 2_000L
            )
        )

        val stored =
            dao.findExact(
                scope = contribution.scope,
                packageName = contribution.packageName,
                channelKey = contribution.channelKey,
                topicKey = contribution.topicKey
            )

        assertEquals(2, stored?.importantCount)
        assertEquals(0, stored?.generalCount)
        assertEquals(2_000L, stored?.lastFeedbackAt)
    }

    @Test
    fun removeFeedback_deletesProfileWhenCountsBecomeZero() =
        runBlocking {
            val contribution = createImportantContribution()

            dao.addFeedback(contribution)
            dao.removeFeedback(
                contribution.copy(
                    lastFeedbackAt = 2_000L
                )
            )

            val stored =
                dao.findExact(
                    scope = contribution.scope,
                    packageName = contribution.packageName,
                    channelKey = contribution.channelKey,
                    topicKey = contribution.topicKey
                )

            assertNull(stored)
        }

    private fun createImportantContribution():
            PersonalizationProfileEntity {
        return PersonalizationProfileEntity(
            scope = "APP_CHANNEL_TOPIC",
            packageName = "com.example.shopping",
            channelKey = "delivery",
            topicKey = "DELIVERY",
            importantCount = 1,
            generalCount = 0,
            lastFeedbackAt = 1_000L,
            profileVersion = "1"
        )
    }
}
