package com.hanseo.noti.ui.onboarding

import androidx.lifecycle.ViewModel
import com.hanseo.noti.notification.NotificationAccessManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import javax.inject.Inject

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val notificationAccessManager:
    NotificationAccessManager
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

    fun refreshNotificationAccess() {
        val hasAccess =
            notificationAccessManager
                .hasNotificationAccess()

        _uiState.update { currentState ->
            currentState.copy(
                hasNotificationAccess = hasAccess,
                isOnboardingCompleted =
                    currentState.isOnboardingCompleted ||
                            hasAccess
            )
        }
    }

    fun onNotificationAccessDeferred() {
        _uiState.update { currentState ->
            currentState.copy(
                isOnboardingCompleted = true
            )
        }
    }
}