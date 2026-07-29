package com.hanseo.noti.domain.importance

data class ImportanceScoreRule(
    val id: String,
    val scoreDelta: Int,
    val description: String,
    val keywords: Set<String> = emptySet(), // 하나라도 일치하면 적용
    val keywordGroups: List<Set<String>> = emptyList(), // 모든 그룹에서 최소 하나씩 일치해야 적용
    val patterns: List<Regex> = emptyList(), // 날짜, 시간 같은 정규식 패턴
    val categories: Set<String> = emptySet(), // Android에서 주는 카테고리
    val requiresOngoing: Boolean? = null, // isOngoing 여부
    val blockedByRuleIds: Set<String> = emptySet() // 부정 규칙 용
)