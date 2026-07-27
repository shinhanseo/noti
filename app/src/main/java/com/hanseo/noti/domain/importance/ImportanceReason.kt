package com.hanseo.noti.domain.importance

enum class ImportanceReasonType {
    USER_FEEDBACK,
    APP_EXCLUSION_KEYWORD,
    GLOBAL_IMPORTANT_KEYWORD,
    IMPORTANT_APP,
    AUTOMATIC_RULE
}

data class ImportanceReason(
    val type: ImportanceReasonType,
    val scoreDelta: Int,
    val ruleId: String? = null,
    val description: String
)