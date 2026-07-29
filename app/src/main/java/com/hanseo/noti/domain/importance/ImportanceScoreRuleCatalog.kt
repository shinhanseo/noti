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
            scoreDelta = 25,
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
                "비밀번호가 변경",
                "의심스러운 활동",
                "OTP",
                "2단계 인증",
                "본인 인증",
                "비정상 로그인",
                "해외 로그인",
                "접속 시도",
                "비밀번호 재설정",
                "계정 보호",
                "부정 사용",
                "이상 거래"
            )
        ),

        ImportanceScoreRule(
            id = "critical_status_change",
            scoreDelta = 25,
            description = "결제·계정·예약 상태가 중요하게 변경됐어요",
            keywordGroups = listOf(
                setOf(
                    "결제",
                    "계정",
                    "예약",
                    "카드",
                    "송금",
                    "이체",
                    "출금",
                    "입금",
                    "계정",
                    "예약",
                    "예매",
                    "구독"
                ),
                setOf(
                    "승인",
                    "실패",
                    "거절",
                    "취소",
                    "잠김",
                    "정지",
                    "변경",
                    "환불",
                    "잠김",
                    "정지",
                    "제한",
                    "변경",
                    "만료",
                    "해지"
                )
            )
        ),


        ImportanceScoreRule(
            id = "urgent_attention",
            scoreDelta = 20,
            description = "빠르게 확인해야 할 표현이 포함되어 있어요",
            keywords = setOf(
                "긴급",
                "즉시 확인",
                "즉시 처리",
                "마감 임박",
                "지금 바로",
                "조치 필요",
                "응답 필요",
                "마감 임박",
                "기한 임박",
                "오늘 마감",
                "곧 종료",
                "지금 바로 확인"
            )
        ),

        ImportanceScoreRule(
            id = "date_or_time",
            scoreDelta = 20,
            description = "일정이나 마감 시간이 함께 있어요",
            keywords = setOf(
                "오늘까지",
                "내일까지",
                "마감",
                "기한",
                "예정",
                "시작합니다",
                "이번 주까지",
                "종료됩니다",
                "분 후",
                "시간 후"
            ),
            patterns = listOf(
                Regex("""\d{1,2}월\s*\d{1,2}일"""),
                Regex("""\d{1,2}\s*시(?:\s*\d{1,2}\s*분)?"""),
                Regex("""(?:[01]?\d|2[0-3]):[0-5]\d"""),
                Regex("""\d+\s*분\s*후"""),
                Regex("""d-\s*\d+""")
            )
        ),

        ImportanceScoreRule(
            id = "action_request",
            scoreDelta = 20,
            description = "확인하거나 처리할 요청이 있어요",
            keywords = setOf(
                "제출해주세요",
                "제출해 주세요",
                "확인해주세요",
                "확인해 주세요",
                "답변해주세요",
                "답변해 주세요",
                "회신 바랍니다",
                "승인이 필요",
                "서명해주세요",
                "서명해 주세요",
                "납부해주세요",
                "납부해 주세요"
            )
        ),

        ImportanceScoreRule(
            id = "delivery_status_change",
            scoreDelta = 10,
            description = "배송 상태가 변경됐어요",
            keywordGroups = listOf(
                setOf(
                    "배송",
                    "택배",
                    "주문"
                ),
                setOf(
                    "출발",
                    "도착",
                    "완료",
                    "지연",
                    "실패",
                    "분실",
                    "반송"
                )
            )
        )
    )

    val allRules: List<ImportanceScoreRule> =
        categoryRules + keywordRules
}
