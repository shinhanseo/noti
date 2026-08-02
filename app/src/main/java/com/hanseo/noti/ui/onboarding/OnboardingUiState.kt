package com.hanseo.noti.ui.onboarding

import com.hanseo.noti.data.apps.InstalledApp

enum class OnboardingStage {
    INTRO,
    NOTIFICATION_ACCESS,
    IMPORTANT_APPS,
    IMPORTANT_KEYWORDS
}

data class OnboardingUiState(
    val stage: OnboardingStage =
        OnboardingStage.INTRO,

    val hasNotificationAccess: Boolean = false,

    val installedApps: List<InstalledApp> =
        emptyList(),

    val selectedAppPackages: Set<String> =
        emptySet(),

    val appSearchQuery: String = "",

    val isLoadingApps: Boolean = false,

    val hasAppLoadError: Boolean = false,

    val globalImportantKeywords: Set<String> =
        emptySet(),

    val keywordInput: String = ""
) {
    val filteredInstalledApps: List<InstalledApp>
        get() {
            val query =
                appSearchQuery.trim()

            if (query.isEmpty()) {
                return installedApps
            }

            return installedApps.filter { installedApp ->
                installedApp.displayName.contains(
                    other = query,
                    ignoreCase = true
                ) ||
                        installedApp.packageName.contains(
                            other = query,
                            ignoreCase = true
                        )
            }
        }
}