package com.hanseo.noti.domain.importance

data class ImportanceSettings(
    val importantApps: Set<String> = emptySet(), // 사용자가 선택한 중요 앱
    val exclusionKeywordsByPackage: Map<String, Set<String>> = emptyMap(), // 중요한 앱마다 제거할 키워드
    val globalImportantKeywords: Set<String> = emptySet(), // 앱 종류와 관계없이 중요하게 처리할 키워드
)