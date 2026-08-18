package com.hanseo.noti.ai

import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceResult
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ActionabilityShadowPolicyTest {

    @Test
    fun reviewWithoutUserOverride_runsShadowPrediction() {
        assertTrue(
            ActionabilityShadowPolicy.shouldPredict(
                result(level = ImportanceLevel.REVIEW, forced = false)
            )
        )
    }

    @Test
    fun clearRuleResults_doNotRunShadowPrediction() {
        assertFalse(
            ActionabilityShadowPolicy.shouldPredict(
                result(level = ImportanceLevel.GENERAL, forced = false)
            )
        )
        assertFalse(
            ActionabilityShadowPolicy.shouldPredict(
                result(level = ImportanceLevel.IMPORTANT, forced = false)
            )
        )
    }

    @Test
    fun forcedReview_doesNotRunShadowPrediction() {
        assertFalse(
            ActionabilityShadowPolicy.shouldPredict(
                result(level = ImportanceLevel.REVIEW, forced = true)
            )
        )
    }

    private fun result(
        level: ImportanceLevel,
        forced: Boolean,
    ) = ImportanceResult(
        score = 25,
        level = level,
        reasons = emptyList(),
        isForced = forced,
        policyVersion = "1",
        evaluatedAtMillis = 1L,
    )
}
