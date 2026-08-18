package com.hanseo.noti.ai

import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.importance.ImportanceResult

object ActionabilityShadowPolicy {
    fun shouldPredict(importanceResult: ImportanceResult): Boolean {
        return !importanceResult.isForced &&
            importanceResult.level == ImportanceLevel.REVIEW
    }
}
