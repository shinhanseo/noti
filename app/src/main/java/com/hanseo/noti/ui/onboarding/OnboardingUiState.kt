package com.hanseo.noti.ui.onboarding

enum class OnboardingStage {
    INTRO,
    NOTIFICATION_ACCESS
}

data class OnboardingUiState(
    val stage: OnboardingStage = OnboardingStage.INTRO,
    val hasNotificationAccess: Boolean = false
)