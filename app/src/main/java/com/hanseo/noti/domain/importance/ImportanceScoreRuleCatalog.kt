package com.hanseo.noti.domain.importance

object ImportanceScoreRuleCatalog {

    val categoryRules: List<ImportanceScoreRule> = listOf(
        ImportanceScoreRule(
            id = "call_or_alarm",
            scoreDelta = 40,
            description = "바로 확인할 가능성이 높은 전화나 알람이에요",
            categories = setOf("call", "alarm")
        ),
        ImportanceScoreRule(
            id = "event_or_reminder",
            scoreDelta = 20,
            description = "일정이나 리마인더 알림이에요",
            categories = setOf("event", "reminder")
        ),
        ImportanceScoreRule(
            id = "message_or_email",
            scoreDelta = 5,
            description = "메시지나 이메일 알림이에요",
            categories = setOf("msg", "email")
        )
    )

    val keywordRules: List<ImportanceScoreRule> = listOf(
        ImportanceScoreRule(
            id = "security_authentication",
            scoreDelta = 30,
            description = "인증이나 보안과 관련된 알림이에요",
            keywords = setOf(
                "인증번호",
                "보안 경고",
                "로그인 시도",
                "새로운 기기에서 로그인",
                "비밀번호가 변경"
            )
        )
    )

    val allRules: List<ImportanceScoreRule> =
        categoryRules + keywordRules
}