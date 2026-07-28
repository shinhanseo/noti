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

        val globalKeywordResult = classifyGlobalImportantKeyword(
            settings = settings,
            normalizedText = normalizedText,
            evaluatedAtMillis = evaluatedAtMillis
        )

        if (globalKeywordResult != null) {
            return globalKeywordResult
        }

        val exclusionResult = classifyAppExclusion(
            input = input,
            settings = settings,
            normalizedText = normalizedText,
            evaluatedAtMillis = evaluatedAtMillis
        )

        if (exclusionResult != null) {
            return exclusionResult
        }

        val importantAppResult = classifyImportantApp(
            input = input,
            settings = settings,
            evaluatedAtMillis = evaluatedAtMillis
        )

        if (importantAppResult != null) {
            return importantAppResult
        }

        return calculateAutomaticScore(
            input = input,
            normalizedText = normalizedText,
            evaluatedAtMillis = evaluatedAtMillis
        )
    }

    private fun classifyAppExclusion( // 중요한 앱이지만, 제외할 단어가 있는 알림을 선별 ( 2순위 )
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

    private fun classifyGlobalImportantKeyword( // 중요앱, 일반앱 구분없이 중요한 키워드 ( 1순위 )
        settings: ImportanceSettings,
        normalizedText: String,
        evaluatedAtMillis: Long
    ) : ImportanceResult? {
        val hasMatchedKeyword = settings.globalImportantKeywords.any { keyword ->
            val normalizedKeyword =
                ImportanceTextNormalizer.normalizeKeyword(keyword)

            normalizedKeyword.isNotEmpty() &&
                    normalizedText.contains(normalizedKeyword)
        }

        if (!hasMatchedKeyword) {
            return null
        }

        return ImportanceResult(
            score = 100,
            level = ImportanceLevel.IMPORTANT,
            reasons = listOf(
                ImportanceReason(
                    type = ImportanceReasonType.GLOBAL_IMPORTANT_KEYWORD,
                    scoreDelta = 100,
                    description = "중요 키워드와 일치해요"
                )
            ),
            isForced = true,
            policyVersion = POLICY_VERSION,
            evaluatedAtMillis = evaluatedAtMillis
        )
    }

    private fun classifyImportantApp( // 중요한 앱에서 온 알림 ( 3순위 )
        input: ImportanceInput,
        settings: ImportanceSettings,
        evaluatedAtMillis: Long
    ): ImportanceResult? {
        if (input.packageName !in settings.importantApps) {
            return null
        }

        return ImportanceResult(
            score = 100,
            level = ImportanceLevel.IMPORTANT,
            reasons = listOf(
                ImportanceReason(
                    type = ImportanceReasonType.IMPORTANT_APP,
                    scoreDelta = 100,
                    description = "중요한 앱에서 온 알림이에요"
                )
            ),
            isForced = true,
            policyVersion = POLICY_VERSION,
            evaluatedAtMillis = evaluatedAtMillis
        )
    }

    private fun calculateAutomaticScore( // 1, 2, 3순위에 걸리지 않은 일반 앱 카테고리 기반 중요도 점수 추출 ( 4순위 )
        input: ImportanceInput,
        normalizedText: String,
        evaluatedAtMillis: Long
    ): ImportanceResult {
        val normalizedCategory = input.category?.lowercase()

        val matchedRules = ImportanceScoreRuleCatalog.allRules.filter { rule ->
            val categoryMatched =
                normalizedCategory != null &&
                        normalizedCategory in rule.categories

            val keywordMatched = rule.keywords.any { keyword ->
                val normalizedKeyword =
                    ImportanceTextNormalizer.normalizeKeyword(keyword)

                normalizedKeyword.isNotEmpty() &&
                        normalizedText.contains(normalizedKeyword)
            }

            val keywordGroupsMatched =
                rule.keywordGroups.isNotEmpty() &&
                        rule.keywordGroups.all { group ->
                            group.any { keyword ->
                                val normalizedKeyword =
                                    ImportanceTextNormalizer.normalizeKeyword(keyword)

                                normalizedKeyword.isNotEmpty() &&
                                        normalizedText.contains(normalizedKeyword)
                            }
                        }

            val patternMatched = rule.patterns.any { pattern ->
                pattern.containsMatchIn(normalizedText)
            }

            categoryMatched ||
                    keywordMatched ||
                    keywordGroupsMatched ||
                    patternMatched
        }

        val score = matchedRules
            .sumOf { rule -> rule.scoreDelta }
            .coerceIn(-100, 100)

        val level = convertScoreToLevel(score)

        val reasons = matchedRules.map { rule ->
            ImportanceReason(
                type = ImportanceReasonType.AUTOMATIC_RULE,
                scoreDelta = rule.scoreDelta,
                ruleId = rule.id,
                description = rule.description
            )
        }

        return ImportanceResult(
            score = score,
            level = level,
            reasons = reasons,
            isForced = false,
            policyVersion = POLICY_VERSION,
            evaluatedAtMillis = evaluatedAtMillis
        )
    }

    private fun convertScoreToLevel(score: Int): ImportanceLevel {
        return when {
            score >= 40 -> ImportanceLevel.IMPORTANT
            score >= 25 -> ImportanceLevel.REVIEW
            else -> ImportanceLevel.GENERAL
        }
    }

    private companion object {
        const val POLICY_VERSION = "1"
    }

}
