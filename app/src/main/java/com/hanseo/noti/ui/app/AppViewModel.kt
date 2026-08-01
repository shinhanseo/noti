package com.hanseo.noti.ui.app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.data.preferences.OnboardingPreferences
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@HiltViewModel
class AppViewModel @Inject constructor(
    onboardingPreferences: OnboardingPreferences
) : ViewModel() {

    val uiState: StateFlow<AppUiState> =
        onboardingPreferences
            .isOnboardingCompleted
            .map { isCompleted ->
                AppUiState(
                    startDestination =
                        if (isCompleted) {
                            AppStartDestination.HOME
                        } else {
                            AppStartDestination.ONBOARDING
                        }
                )
            }
            .stateIn(
                scope = viewModelScope,
                started = SharingStarted.Eagerly,
                initialValue = AppUiState()
            )
}