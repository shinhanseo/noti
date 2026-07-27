package com.hanseo.noti.domain.importance

class ImportanceClassifier {
    fun classify (
        input: ImportanceInput,
        settings: ImportanceSettings,
        evaluatedAtMillis: Long = System.currentTimeMillis()
    ) : ImportanceResult {
        val normalizedText = ImportanceTextNormalizer.normalize(
            title = input.title,
            body = input.body,
        )

        val exclusionResult = classifyAppExclusion(
            input = input,
            settings = settings,
            normalizedText = normalizedText,
            evaluatedAtMillis = evaluatedAtMillis
        )

        if (exclusionResult != null) {
            return exclusionResult
        }

        return ImportanceResult(
            score = 0,
            level = ImportanceLevel.GENERAL,
            reasons = emptyList(),
            isForced = false,
            policyVersion = POLICY_VERSION,
            evaluatedAtMillis = evaluatedAtMillis
        )
    }

    private fun classifyAppExclusion( // 중요한 앱이지만, 제외할 단어가 있는 알림을 선별
        input: ImportanceInput,
        settings: ImportanceSettings,
        normalizedText: String,
        evaluatedAtMillis: Long
    ) : ImportanceResult? {
        if (input.packageName !in settings.importantApps) {
            return null
        }

        val exclusionKeywords =
            settings.exclusionKeywordsByPackage[input.packageName]
                ?: return null

        val hasMatchedKeyword = exclusionKeywords.any { keyword ->
            val normalizedKeyword =
                ImportanceTextNormalizer.normalizeKeyword(keyword)

            normalizedKeyword.isNotEmpty() &&
                    normalizedText.contains(normalizedKeyword)
        }

        if (!hasMatchedKeyword) {
            return null
        }

        return ImportanceResult(
            score = -100,
            level = ImportanceLevel.GENERAL,
            reasons = listOf(
                ImportanceReason(
                    type = ImportanceReasonType.APP_EXCLUSION_KEYWORD,
                    scoreDelta = -100,
                    description = "이 앱에서 제외하도록 설정한 키워드와 일치해요"
                )
            ),
            isForced = true,
            policyVersion = POLICY_VERSION,
            evaluatedAtMillis = evaluatedAtMillis
        )
    }

    private companion object {
        const val POLICY_VERSION = "1"
    }

}