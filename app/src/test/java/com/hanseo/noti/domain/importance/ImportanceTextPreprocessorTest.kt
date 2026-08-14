package com.hanseo.noti.domain.importance

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ImportanceTextPreprocessorTest {

    @Test
    fun samsungMms_keepsSubjectAndRemovesTransportMetadata() {
        val input = ImportanceInput(
            packageName = "com.samsung.android.messaging",
            title = "컬리",
            body = """
                <제목: 컬리 쿠폰 당첨 안내>
                메시지 크기: 3KB
                만료: 8월 19일, 오전 11:44
            """.trimIndent(),
            category = "msg",
            isOngoing = false
        )

        val result = ImportanceTextPreprocessor.normalize(input)

        assertEquals(
            "컬리 컬리 쿠폰 당첨 안내",
            result
        )

        assertFalse(result.contains("메시지 크기"))
        assertFalse(result.contains("8월 19일"))
        assertFalse(result.contains("만료"))
    }

    @Test
    fun samsungDeliveryMms_keepsDeliveryCompany() {
        val input = ImportanceInput(
            packageName = "com.samsung.android.messaging",
            title = "010-1234-5678",
            body = """
                <제목: [로젠택배]>
                메시지 크기: 183KB
                만료: 8월 15일, 오전 9:09
            """.trimIndent(),
            category = "msg",
            isOngoing = false
        )

        val result = ImportanceTextPreprocessor.normalize(input)

        assertTrue(result.contains("로젠택배"))
        assertFalse(result.contains("183kb"))
        assertFalse(result.contains("8월 15일"))
    }

    @Test
    fun normalExpirationNotification_keepsExpirationText() {
        val input = ImportanceInput(
            packageName = "com.example.card",
            title = "카드 안내",
            body = "카드 유효기간이 내일 만료됩니다",
            category = "status",
            isOngoing = false
        )

        val result = ImportanceTextPreprocessor.normalize(input)

        assertTrue(result.contains("만료됩니다"))
    }

    @Test
    fun unicodeFormatCharacters_areRemoved() {
        val input = ImportanceInput(
            packageName = "com.samsung.android.messaging",
            title = "컬리",
            body = "<제목: 컬리\u200E 쿠폰\u200E 당첨 안내>",
            category = "msg",
            isOngoing = false
        )

        val result = ImportanceTextPreprocessor.normalize(input)

        assertTrue(result.contains("쿠폰 당첨"))
        assertFalse(result.contains("\u200E"))
    }
}