package com.hanseo.noti.domain.importance

data class ImportanceScoreRule(
    val id: String,
    val scoreDelta: Int,
    val description: String,
    val keywords: Set<String> = emptySet(),
    val categories: Set<String> = emptySet()
)