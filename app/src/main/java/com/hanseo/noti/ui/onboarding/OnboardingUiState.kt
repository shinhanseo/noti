package com.hanseo.noti.ui.onboarding

data class OnboardingUiState(
    val currentPage: Int = 0,
    val isPermissionStep: Boolean = false,
    val hasNotificationAccess: Boolean = false
)