package com.hanseo.noti.domain.importance

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Assert.assertFalse
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
    fun globalImportantKeyword_hasPriorityOverAppExclusionKeyword() {
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

        assertEquals(100, result.score)
        assertEquals(ImportanceLevel.IMPORTANT, result.level)
        assertTrue(result.isForced)
        assertEquals(
            ImportanceReasonType.GLOBAL_IMPORTANT_KEYWORD,
            result.reasons.single().type
        )
    }

    @Test
    fun importantAppWithoutMatchingExclusion_isForcedToImportant() {
        val input = ImportanceInput(
            packageName = "com.example.message",
            title = "팀 일정 안내",
            body = "내일 일정을 확인하세요",
            category = null,
            isOngoing = false
        )

        val settings = ImportanceSettings(
            importantApps = setOf("com.example.message"),
            exclusionKeywordsByPackage = mapOf(
                "com.example.message" to setOf("광고")
            )
        )

        val result = classifier.classify(
            input = input,
            settings = settings,
            evaluatedAtMillis = 4_000L
        )

        assertEquals(100, result.score)
        assertEquals(ImportanceLevel.IMPORTANT, result.level)
        assertTrue(result.isForced)
        assertEquals(
            ImportanceReasonType.IMPORTANT_APP,
            result.reasons.single().type
        )
        assertEquals(4_000L, result.evaluatedAtMillis)
    }

    @Test
    fun callCategory_isAutomaticallyImportant() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "전화 알림",
            body = "수신 전화가 있습니다",
            category = "CALL",
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 5_000L
        )

        assertEquals(40, result.score)
        assertEquals(ImportanceLevel.IMPORTANT, result.level)
        assertFalse(result.isForced)
        assertEquals(
            ImportanceReasonType.AUTOMATIC_RULE,
            result.reasons.single().type
        )
        assertEquals(
            "call_or_alarm",
            result.reasons.single().ruleId
        )
    }

    @Test
    fun eventCategory_isAutomaticallyReview() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "일정 알림",
            body = "등록된 일정이 있습니다",
            category = "event",
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 6_000L
        )

        assertEquals(25, result.score)
        assertEquals(ImportanceLevel.REVIEW, result.level)
        assertFalse(result.isForced)
        assertEquals(
            "event_or_reminder",
            result.reasons.single().ruleId
        )
    }

    @Test
    fun messageCategory_isAutomaticallyGeneral() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "메시지 알림",
            body = "새 메시지가 있습니다",
            category = "msg",
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 7_000L
        )

        assertEquals(5, result.score)
        assertEquals(ImportanceLevel.GENERAL, result.level)
        assertFalse(result.isForced)
        assertEquals(
            "message_or_email",
            result.reasons.single().ruleId
        )
    }

    @Test
    fun missingCategory_isZeroScoreGeneral() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "일반 상태",
            body = "새로운 상태가 있습니다",
            category = null,
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 8_000L
        )

        assertEquals(0, result.score)
        assertEquals(ImportanceLevel.GENERAL, result.level)
        assertFalse(result.isForced)
        assertTrue(result.reasons.isEmpty())
    }

    @Test
    fun messageWithSecurityKeyword_accumulatesBothScores() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "인증번호 안내",
            body = "본인 확인을 진행해 주세요",
            category = "msg",
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 9_000L
        )

        assertEquals(35, result.score)
        assertEquals(ImportanceLevel.REVIEW, result.level)
        assertFalse(result.isForced)

        assertEquals(
            setOf(
                "message_or_email",
                "security_authentication"
            ),
            result.reasons
                .mapNotNull { reason -> reason.ruleId }
                .toSet()
        )
    }

    @Test
    fun promotionalMessage_combinesPositiveAndNegativeScores() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "[광고] 오늘까지 할인 쿠폰을 확인해 주세요",
            body = null,
            category = "msg",
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 10_000L
        )

        assertEquals(10, result.score)
        assertEquals(ImportanceLevel.GENERAL, result.level)
        assertFalse(result.isForced)

        assertEquals(
            setOf(
                "message_or_email",
                "date_or_time",
                "action_request",
                "promotional_content"
            ),
            result.reasons
                .mapNotNull { reason -> reason.ruleId }
                .toSet()
        )

        assertEquals(
            1,
            result.reasons.count { reason ->
                reason.ruleId == "promotional_content"
            }
        )
    }

    @Test
    fun advertisingConsultingMeeting_isImportantWithoutPromotionalPenalty() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "광고 컨설팅 회의가 7시에 있습니다",
            body = null,
            category = null,
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 11_000L
        )

        assertEquals(40, result.score)
        assertEquals(ImportanceLevel.IMPORTANT, result.level)

        assertEquals(
            setOf(
                "date_or_time",
                "schedule_context"
            ),
            result.reasons
                .mapNotNull { reason -> reason.ruleId }
                .toSet()
        )

        assertFalse(
            result.reasons.any { reason ->
                reason.ruleId == "promotional_content"
            }
        )
    }

    @Test
    fun ongoingProgress_isAutomaticallyReduced() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "파일 다운로드 진행 중",
            body = null,
            category = "progress",
            isOngoing = true
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 12_000L
        )

        assertEquals(-25, result.score)
        assertEquals(ImportanceLevel.GENERAL, result.level)
        assertFalse(result.isForced)
        assertEquals(
            "ongoing_progress",
            result.reasons.single().ruleId
        )
    }

    @Test
    fun nonOngoingProgress_isNotReduced() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "파일 다운로드 안내",
            body = null,
            category = "progress",
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 13_000L
        )

        assertEquals(0, result.score)
        assertEquals(ImportanceLevel.GENERAL, result.level)
        assertTrue(result.reasons.isEmpty())
    }

    @Test
    fun securityRule_blocksOngoingProgressReduction() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "보안 경고",
            body = "새로운 기기에서 로그인했습니다",
            category = "service",
            isOngoing = true
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 14_000L
        )

        assertEquals(30, result.score)
        assertEquals(ImportanceLevel.REVIEW, result.level)

        assertEquals(
            setOf("security_authentication"),
            result.reasons
                .mapNotNull { reason -> reason.ruleId }
                .toSet()
        )
    }

    @Test
    fun passiveStatus_isAutomaticallyReduced() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "백업 완료",
            body = null,
            category = null,
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 15_000L
        )

        assertEquals(-10, result.score)
        assertEquals(ImportanceLevel.GENERAL, result.level)
        assertEquals(
            "passive_status",
            result.reasons.single().ruleId
        )
    }

    @Test
    fun actionRequest_blocksPassiveStatusReduction() {
        val input = ImportanceInput(
            packageName = "com.example.normal",
            title = "업데이트 완료 내용을 확인해 주세요",
            body = null,
            category = null,
            isOngoing = false
        )

        val result = classifier.classify(
            input = input,
            settings = ImportanceSettings(),
            evaluatedAtMillis = 16_000L
        )

        assertEquals(20, result.score)
        assertEquals(ImportanceLevel.GENERAL, result.level)

        assertEquals(
            setOf("action_request"),
            result.reasons
                .mapNotNull { reason -> reason.ruleId }
                .toSet()
        )
    }
}
