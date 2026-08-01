package com.hanseo.noti.ui.onboarding

import android.content.Intent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.data.preferences.OnboardingPreferences
import com.hanseo.noti.notification.NotificationAccessManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val notificationAccessManager: NotificationAccessManager,
    private val onboardingPreferences: OnboardingPreferences
) : ViewModel() {

    private val _uiState = MutableStateFlow(
        OnboardingUiState(
            hasNotificationAccess =
                notificationAccessManager
                    .hasNotificationAccess()
        )
    )

    val uiState: StateFlow<OnboardingUiState> =
        _uiState.asStateFlow()

    fun onIntroCompleted() {
        _uiState.update { currentState ->
            currentState.copy(
                stage = OnboardingStage.NOTIFICATION_ACCESS
            )
        }
    }

    fun onBackToIntro() {
        _uiState.update { currentState ->
            currentState.copy(
                stage = OnboardingStage.INTRO
            )
        }
    }

    fun createNotificationAccessSettingsIntent(): Intent {
        return notificationAccessManager
            .createNotificationAccessSettingsIntent()
    }

    fun refreshNotificationAccess() {
        val hasAccess =
            notificationAccessManager.hasNotificationAccess()

        _uiState.update { currentState ->
            currentState.copy(
                hasNotificationAccess = hasAccess,
                stage = if (hasAccess) {
                    OnboardingStage.IMPORTANT_APPS
                } else {
                    currentState.stage
                }
            )
        }
    }

    fun onNotificationAccessDeferred() {
        _uiState.update { currentState ->
            currentState.copy(
                stage = OnboardingStage.IMPORTANT_APPS
            )
        }
    }

    fun onImportantAppsCompleted() {
        _uiState.update { currentState ->
            currentState.copy(
                stage = OnboardingStage.IMPORTANT_KEYWORDS
            )
        }
    }

    private fun completeOnboarding() {
        viewModelScope.launch {
            onboardingPreferences
                .setOnboardingCompleted(true)
        }
    }
}