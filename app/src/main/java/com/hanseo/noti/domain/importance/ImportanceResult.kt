package com.hanseo.noti.domain.importance

data class ImportanceResult(
    val score: Int, // 최종 중요도 점수
    val level: ImportanceLevel, // 점수 변환 등급
    val reasons: List<ImportanceReason>, // 점수가 결정된 이유 목록
    val isForced: Boolean, // 사용자 설정으로 강제되었는 지(중요한 앱, 중요한 키워드, 뺄 단어)
    val policyVersion: String, // 어떤 정책으로 판정했는 지
    val evaluatedAtMillis: Long // 판정 시각
)
