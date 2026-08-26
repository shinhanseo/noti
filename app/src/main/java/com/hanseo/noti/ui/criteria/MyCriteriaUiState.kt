package com.hanseo.noti.ui.criteria

import com.hanseo.noti.data.apps.InstalledApp

data class MyCriteriaUiState(
    val installedApps: List<InstalledApp> = emptyList(),
    val importantAppPackages: Set<String> = emptySet(),
    val globalImportantKeywords: Set<String> = emptySet(),
    val exclusionKeywordsByPackage: Map<String, Set<String>> =
        emptyMap(),
    val appSearchQuery: String = "",
    val keywordInput: String = "",
    val exclusionKeywordInput: String = "",
    val selectedExclusionAppPackage: String? = null,
    val isLoadingSettings: Boolean = true,
    val isLoadingApps: Boolean = false,
    val hasAppLoadError: Boolean = false,
    val hasSaveError: Boolean = false
) {
    val importantAppCount: Int
        get() = importantAppPackages.size

    val importantKeywordCount: Int
        get() = globalImportantKeywords.size

    val exclusionKeywordCount: Int
        get() = exclusionKeywordsByPackage
            .values
            .sumOf { keywords -> keywords.size }

    val filteredInstalledApps: List<InstalledApp>
        get() {
            val query = appSearchQuery.trim()

            if (query.isEmpty()) {
                return installedApps
            }

            return installedApps.filter { app ->
                app.displayName.contains(
                    other = query,
                    ignoreCase = true
                ) ||
                    app.packageName.contains(
                        other = query,
                        ignoreCase = true
                    )
            }
        }

    val importantApps: List<InstalledApp>
        get() = installedApps.filter { app ->
            app.packageName in importantAppPackages
        }

    val selectedExclusionKeywords: Set<String>
        get() = selectedExclusionAppPackage
            ?.let { packageName ->
                exclusionKeywordsByPackage[packageName]
            }
            ?: emptySet()
}
