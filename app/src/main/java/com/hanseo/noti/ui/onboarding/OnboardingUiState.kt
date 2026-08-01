package com.hanseo.noti.ui.onboarding


enum class OnboardingStage {
    INTRO,
    NOTIFICATION_ACCESS,
    IMPORTANT_APPS,
    IMPORTANT_KEYWORDS
}

data class OnboardingUiState(
    val stage: OnboardingStage = OnboardingStage.INTRO,
    val hasNotificationAccess: Boolean = false
)