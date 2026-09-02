package com.hanseo.noti.domain.personalization

import kotlin.math.abs
import kotlin.math.roundToInt

data class PersonalizationAdjustment(
    val scoreDelta: Int,
    val matchedScope: PersonalizationScope?,
    val importantRatio: Double?,
    val feedbackCount: Int
) {
    val isApplied: Boolean
        get() = scoreDelta != 0

    init {
        require(scoreDelta in -15..15) {
            "scoreDelta must be between -15 and 15"
        }
    }

    companion object {
        fun none(): PersonalizationAdjustment {
            return PersonalizationAdjustment(
                scoreDelta = 0,
                matchedScope = null,
                importantRatio = null,
                feedbackCount = 0
            )
        }
    }
}

class PersonalizationScoreCalculator {

    fun calculate(
        profiles: List<PersonalizationProfile>
    ): PersonalizationAdjustment {
        val sortedProfiles =
            profiles.sortedBy { profile ->
                scopePriority(profile.scope)
            }

        for (profile in sortedProfiles) {
            val feedbackCount =
                profile.totalFeedbackCount

            val importantRatio =
                profile.importantCount.toDouble() /
                        feedbackCount

            val preferenceBalance =
                (
                    profile.importantCount -
                            profile.generalCount
                ).toDouble() / feedbackCount

            if (preferenceBalance == 0.0) {
                return PersonalizationAdjustment(
                    scoreDelta = 0,
                    matchedScope = profile.scope,
                    importantRatio = importantRatio,
                    feedbackCount = feedbackCount
                )
            }

            val confidence =
                feedbackConfidence(feedbackCount)

            val maximumScore =
                maximumScore(profile.scope)

            val scoreMagnitude =
                (
                    maximumScore *
                            confidence *
                            abs(preferenceBalance)
                )
                    .roundToInt()
                    .coerceAtLeast(1)

            val direction =
                if (preferenceBalance > 0.0) {
                    1
                } else {
                    -1
                }

            return PersonalizationAdjustment(
                scoreDelta =
                    scoreMagnitude * direction,

                matchedScope =
                    profile.scope,

                importantRatio =
                    importantRatio,

                feedbackCount =
                    feedbackCount
            )
        }

        return PersonalizationAdjustment.none()
    }

    private fun feedbackConfidence(
        feedbackCount: Int
    ): Double {
        return when (feedbackCount) {
            1 -> 0.35
            2 -> 0.60
            3 -> 0.80
            4 -> 0.90
            else -> 1.00
        }
    }

    private fun maximumScore(
        scope: PersonalizationScope
    ): Int {
        return when (scope) {
            PersonalizationScope.APP_CHANNEL_TOPIC ->
                15

            PersonalizationScope.APP_TOPIC ->
                12

            PersonalizationScope.APP_CHANNEL ->
                9

            PersonalizationScope.APP ->
                6
        }
    }

    private fun scopePriority(
        scope: PersonalizationScope
    ): Int {
        return when (scope) {
            PersonalizationScope.APP_CHANNEL_TOPIC ->
                0

            PersonalizationScope.APP_TOPIC ->
                1

            PersonalizationScope.APP_CHANNEL ->
                2

            PersonalizationScope.APP ->
                3
        }
    }
}
