package com.hanseo.noti.ui.onboarding

import android.content.Intent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.data.preferences.ImportanceSettingsPreferences
import com.hanseo.noti.data.preferences.OnboardingPreferences
import com.hanseo.noti.notification.NotificationAccessManager
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject
import com.hanseo.noti.data.apps.InstalledAppProvider
import kotlinx.coroutines.CancellationException

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val notificationAccessManager:
    NotificationAccessManager,
    private val onboardingPreferences:
    OnboardingPreferences,
    private val importanceSettingsPreferences:
    ImportanceSettingsPreferences,
    private val installedAppProvider:
    InstalledAppProvider
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

    init {
        loadInstalledApps()
    }

    private fun loadInstalledApps() {
        if (_uiState.value.isLoadingApps) {
            return
        }

        _uiState.update { currentState ->
            currentState.copy(
                isLoadingApps = true,
                hasAppLoadError = false
            )
        }

        viewModelScope.launch {
            try {
                val installedApps =
                    installedAppProvider
                        .getLaunchableApps()

                _uiState.update { currentState ->
                    currentState.copy(
                        installedApps = installedApps,
                        isLoadingApps = false,
                        hasAppLoadError = false
                    )
                }
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                _uiState.update { currentState ->
                    currentState.copy(
                        installedApps = emptyList(),
                        isLoadingApps = false,
                        hasAppLoadError = true
                    )
                }
            }
        }
    }

    fun onIntroCompleted() {
        _uiState.update { currentState ->
            val nextStage =
                if (currentState.hasNotificationAccess) {
                    OnboardingStage.IMPORTANT_APPS
                } else {
                    OnboardingStage.NOTIFICATION_ACCESS
                }

            currentState.copy(
                stage = nextStage
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
            notificationAccessManager
                .hasNotificationAccess()

        _uiState.update { currentState ->
            currentState.copy(
                hasNotificationAccess = hasAccess,
                stage =
                    if (hasAccess) {
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

    fun onBackToNotificationAccess() {
        _uiState.update { currentState ->
            currentState.copy(
                stage = OnboardingStage.NOTIFICATION_ACCESS
            )
        }
    }

    fun onImportantAppToggled(
        packageName: String
    ) {
        val normalizedPackageName =
            packageName.trim()

        if (normalizedPackageName.isEmpty()) {
            return
        }

        _uiState.update { currentState ->
            val selectedPackages =
                currentState.selectedAppPackages

            val updatedPackages =
                if (
                    normalizedPackageName in
                    selectedPackages
                ) {
                    selectedPackages -
                            normalizedPackageName
                } else {
                    selectedPackages +
                            normalizedPackageName
                }

            currentState.copy(
                selectedAppPackages = updatedPackages
            )
        }
    }

    fun onImportantAppsCompleted() {
        _uiState.update { currentState ->
            currentState.copy(
                stage =
                    OnboardingStage.IMPORTANT_KEYWORDS
            )
        }
    }

    fun onBackToImportantApps() {
        _uiState.update { currentState ->
            currentState.copy(
                stage = OnboardingStage.IMPORTANT_APPS
            )
        }
    }

    fun onKeywordInputChanged(
        value: String
    ) {
        _uiState.update { currentState ->
            currentState.copy(
                keywordInput = value
            )
        }
    }

    fun onKeywordAdded() {
        _uiState.update { currentState ->
            val keyword =
                currentState.keywordInput.trim()

            if (keyword.isEmpty()) {
                return@update currentState
            }

            val alreadyExists =
                currentState
                    .globalImportantKeywords
                    .any { savedKeyword ->
                        savedKeyword.equals(
                            other = keyword,
                            ignoreCase = true
                        )
                    }

            if (alreadyExists) {
                return@update currentState.copy(
                    keywordInput = ""
                )
            }

            currentState.copy(
                globalImportantKeywords =
                    currentState
                        .globalImportantKeywords +
                            keyword,
                keywordInput = ""
            )
        }
    }

    fun onKeywordRemoved(
        keyword: String
    ) {
        _uiState.update { currentState ->
            currentState.copy(
                globalImportantKeywords =
                    currentState
                        .globalImportantKeywords -
                            keyword
            )
        }
    }

    fun onSetupCompleted() {
        val currentState = _uiState.value

        viewModelScope.launch {
            importanceSettingsPreferences
                .saveInitialSettings(
                    importantAppPackages =
                        currentState
                            .selectedAppPackages,
                    globalImportantKeywords =
                        currentState
                            .globalImportantKeywords
                )

            onboardingPreferences
                .setOnboardingCompleted(true)
        }
    }
}