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

    @Test
    fun generalAppWithGlobalImportantKeyword_isForcedToImportant() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "PAYMENT FAILED",
            body = "결제 상태를 확인하세요",
            category = null,
            isOngoing = false
        )

        val settings = ImportanceSettings(
            globalImportantKeywords = setOf("  payment failed  ")
        )

        val result = classifier.classify(
            input = input,
            settings = settings,
            evaluatedAtMillis = 2_000L
        )

        assertEquals(100, result.score)
        assertEquals(ImportanceLevel.IMPORTANT, result.level)
        assertTrue(result.isForced)
        assertEquals(
            ImportanceReasonType.GLOBAL_IMPORTANT_KEYWORD,
            result.reasons.single().type
        )
        assertEquals(2_000L, result.evaluatedAtMillis)
    }

    @Test
    fun appExclusionKeyword_hasPriorityOverGlobalImportantKeyword() {
        val input = ImportanceInput(
            packageName = "com.example.message",
            title = "MEETING EVENT",
            body = "새로운 이벤트를 확인하세요",
            category = null,
            isOngoing = false
        )

        val settings = ImportanceSettings(
            importantApps = setOf("com.example.message"),
            exclusionKeywordsByPackage = mapOf(
                "com.example.message" to setOf("event")
            ),
            globalImportantKeywords = setOf("meeting")
        )

        val result = classifier.classify(
            input = input,
            settings = settings,
            evaluatedAtMillis = 3_000L
        )

        assertEquals(-100, result.score)
        assertEquals(ImportanceLevel.GENERAL, result.level)
        assertTrue(result.isForced)
        assertEquals(
            ImportanceReasonType.APP_EXCLUSION_KEYWORD,
            result.reasons.single().type
        )
    }
}