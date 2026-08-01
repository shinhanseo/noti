package com.hanseo.noti.ui.app

enum class AppStartDestination {
    LOADING,
    ONBOARDING,
    HOME
}

data class AppUiState(
    val startDestination: AppStartDestination =
        AppStartDestination.LOADING
)