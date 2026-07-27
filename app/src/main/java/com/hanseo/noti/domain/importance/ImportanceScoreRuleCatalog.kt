package com.hanseo.noti.domain.importance

object ImportanceScoreRuleCatalog {
    val categoryRules: List<ImportanceScoreRule> = listOf(
        ImportanceScoreRule(
            id = "call_or_alarm",
            scoreDelta = 40,
            description = "바로 확인할 가능성이 높은 전화나 알람이에요",
            categories = setOf(
                "call",
                "alarm"
            )
        ),

        ImportanceScoreRule(
            id = "event_or_reminder",
            scoreDelta = 20,
            description = "일정이나 리마인더 알람이에요",
            categories = setOf(
                "event",
                "reminder"
            )
        ),

        ImportanceScoreRule(
            id = "message_or_email",
            scoreDelta = 5,
            description = "메시지나 이메일 알림이에요",
            categories = setOf(
                "msg",
                "email"
            )
        )


    )
}
