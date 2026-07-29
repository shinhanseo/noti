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

    private fun calculateAutomaticScore(
        input: ImportanceInput,
        normalizedText: String,
        evaluatedAtMillis: Long
    ): ImportanceResult {
        val normalizedCategory = input.category?.lowercase()

        // 1. 카테고리·키워드·문맥·정규식이 일치하는 후보 규칙 찾기
        val candidateRules = ImportanceScoreRuleCatalog.allRules.filter { rule ->
            val categoryMatched = // 카테고리
                normalizedCategory != null &&
                        normalizedCategory in rule.categories

            val keywordMatched = rule.keywords.any { keyword -> // 키워드
                val normalizedKeyword =
                    ImportanceTextNormalizer.normalizeKeyword(keyword)

                normalizedKeyword.isNotEmpty() &&
                        normalizedText.contains(normalizedKeyword)
            }

            val keywordGroupsMatched = // 키워드 그룹
                rule.keywordGroups.isNotEmpty() &&
                        rule.keywordGroups.all { group ->
                            group.any { keyword ->
                                val normalizedKeyword =
                                    ImportanceTextNormalizer.normalizeKeyword(keyword)

                                normalizedKeyword.isNotEmpty() &&
                                        normalizedText.contains(normalizedKeyword)
                            }
                        }

            val patternMatched = rule.patterns.any { pattern -> // 정규식
                pattern.containsMatchIn(normalizedText)
            }

            val contentMatched =
                categoryMatched ||
                        keywordMatched ||
                        keywordGroupsMatched ||
                        patternMatched

            val ongoingRequirementMatched =
                rule.requiresOngoing == null ||
                        rule.requiresOngoing == input.isOngoing

            contentMatched && ongoingRequirementMatched
        }

        // 2. 후보 규칙들 ID
        val candidateRuleIds = candidateRules
            .map { rule -> rule.id }
            .toSet()

        // 3. 다른 규칙 때문에 차단되는 규칙을 제거
        val matchedRules = candidateRules.filter { rule ->
            rule.blockedByRuleIds.none { blockedRuleId ->
                blockedRuleId in candidateRuleIds
            }
        }

        // 4. 긍정 및 부정 규칙 점수 합산
        val score = matchedRules
            .sumOf { rule -> rule.scoreDelta }
            .coerceIn(-100, 100)

        // 5. 최종 점수를 등급으로 변환
        val level = convertScoreToLevel(score)

        // 6. 일치한 규칙을 판정 이유로 변환
        val reasons = matchedRules.map { rule ->
            ImportanceReason(
                type = ImportanceReasonType.AUTOMATIC_RULE,
                scoreDelta = rule.scoreDelta,
                ruleId = rule.id,
                description = rule.description
            )
        }

        // 7. 최종 판정 결과를 반환
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
