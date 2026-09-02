package com.hanseo.noti.domain.personalization

import com.hanseo.noti.domain.topic.NotificationTopic
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PersonalizationScoreCalculatorTest {

    private val calculator =
        PersonalizationScoreCalculator()

    @Test
    fun firstImportantFeedback_appliesImmediately() {
        val result = calculator.calculate(
            profiles = listOf(
                profile(
                    scope =
                        PersonalizationScope
                            .APP_CHANNEL_TOPIC,
                    importantCount = 1,
                    generalCount = 0
                )
            )
        )

        assertEquals(5, result.scoreDelta)
        assertEquals(
            PersonalizationScope.APP_CHANNEL_TOPIC,
            result.matchedScope
        )
        assertEquals(1.0, result.importantRatio!!, 0.0)
        assertEquals(1, result.feedbackCount)
        assertTrue(result.isApplied)
    }

    @Test
    fun firstGeneralFeedback_appliesImmediately() {
        val result = calculator.calculate(
            profiles = listOf(
                profile(
                    scope =
                        PersonalizationScope
                            .APP_CHANNEL_TOPIC,
                    importantCount = 0,
                    generalCount = 1
                )
            )
        )

        assertEquals(-5, result.scoreDelta)
        assertEquals(0.0, result.importantRatio!!, 0.0)
        assertTrue(result.isApplied)
    }

    @Test
    fun repeatedConsistentFeedback_increasesScore() {
        val oneFeedback = calculator.calculate(
            profiles = listOf(
                profile(
                    importantCount = 1,
                    generalCount = 0
                )
            )
        )

        val twoFeedbacks = calculator.calculate(
            profiles = listOf(
                profile(
                    importantCount = 2,
                    generalCount = 0
                )
            )
        )

        val threeFeedbacks = calculator.calculate(
            profiles = listOf(
                profile(
                    importantCount = 3,
                    generalCount = 0
                )
            )
        )

        assertEquals(5, oneFeedback.scoreDelta)
        assertEquals(9, twoFeedbacks.scoreDelta)
        assertEquals(12, threeFeedbacks.scoreDelta)
    }

    @Test
    fun conflictingFeedback_reducesScore() {
        val result = calculator.calculate(
            profiles = listOf(
                profile(
                    importantCount = 2,
                    generalCount = 1
                )
            )
        )

        assertEquals(4, result.scoreDelta)
        assertEquals(
            2.0 / 3.0,
            result.importantRatio!!,
            0.0001
        )
    }

    @Test
    fun tiedSpecificProfile_doesNotFallBackToBroadProfile() {
        val result = calculator.calculate(
            profiles = listOf(
                profile(
                    scope = PersonalizationScope.APP,
                    importantCount = 5,
                    generalCount = 0
                ),
                profile(
                    scope =
                        PersonalizationScope
                            .APP_CHANNEL_TOPIC,
                    importantCount = 1,
                    generalCount = 1
                )
            )
        )

        assertEquals(0, result.scoreDelta)
        assertEquals(
            PersonalizationScope.APP_CHANNEL_TOPIC,
            result.matchedScope
        )
        assertFalse(result.isApplied)
    }

    @Test
    fun firstFeedback_usesSmallerScoreForBroaderScope() {
        val result = calculator.calculate(
            profiles = listOf(
                profile(
                    scope = PersonalizationScope.APP,
                    importantCount = 1,
                    generalCount = 0
                )
            )
        )

        assertEquals(2, result.scoreDelta)
    }

    @Test
    fun emptyProfiles_returnsNoAdjustment() {
        val result = calculator.calculate(emptyList())

        assertEquals(0, result.scoreDelta)
        assertEquals(null, result.matchedScope)
        assertEquals(null, result.importantRatio)
        assertEquals(0, result.feedbackCount)
        assertFalse(result.isApplied)
    }

    private fun profile(
        scope: PersonalizationScope =
            PersonalizationScope.APP_CHANNEL_TOPIC,
        importantCount: Int,
        generalCount: Int
    ): PersonalizationProfile {
        val channelId =
            when (scope) {
                PersonalizationScope.APP_CHANNEL_TOPIC,
                PersonalizationScope.APP_CHANNEL ->
                    "delivery"

                else ->
                    null
            }

        val topic =
            when (scope) {
                PersonalizationScope.APP_CHANNEL_TOPIC,
                PersonalizationScope.APP_TOPIC ->
                    NotificationTopic.DELIVERY

                else ->
                    null
            }

        return PersonalizationProfile(
            scope = scope,
            packageName = "com.coupang.mobile",
            channelId = channelId,
            topic = topic,
            importantCount = importantCount,
            generalCount = generalCount,
            profileVersion = "1"
        )
    }
}
