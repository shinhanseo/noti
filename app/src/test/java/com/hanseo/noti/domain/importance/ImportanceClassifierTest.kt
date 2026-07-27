package com.hanseo.noti.domain.importance

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ImportanceClassifierTest {

    private val classifier = ImportanceClassifier()

    @Test
    fun importantAppWithExclusionKeyword_isForcedToGeneral() {
        val input = ImportanceInput(
            packageName = "com.example.message",
            title = "SPECIAL EVENT",
            body = "새로운 혜택을 확인하세요",
            category = null,
            isOngoing = false
        )

        val settings = ImportanceSettings(
            importantApps = setOf("com.example.message"),
            exclusionKeywordsByPackage = mapOf(
                "com.example.message" to setOf("  event  ")
            )
        )

        val result = classifier.classify(
            input = input,
            settings = settings,
            evaluatedAtMillis = 1_000L
        )

        assertEquals(-100, result.score)
        assertEquals(ImportanceLevel.GENERAL, result.level)
        assertTrue(result.isForced)
        assertEquals(
            ImportanceReasonType.APP_EXCLUSION_KEYWORD,
            result.reasons.single().type
        )
        assertEquals(1_000L, result.evaluatedAtMillis)
    }
}