package com.hanseo.noti.domain.importance

data class ImportanceClassification(
    val result: ImportanceResult,
    val automaticReasons: List<ImportanceReason>
)