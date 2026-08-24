package com.hanseo.noti.ui.onboarding

import android.content.Intent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.battery.BatteryOptimizationManager
import com.hanseo.noti.data.apps.InstalledAppProvider
import com.hanseo.noti.data.preferences.ImportanceSettingsPreferences
import com.hanseo.noti.data.preferences.OnboardingPreferences
import com.hanseo.noti.notification.NotificationAccessManager
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class OnboardingViewModel @Inject constructor(
    private val notificationAccessManager:
    NotificationAccessManager,
    private val batteryOptimizationManager:
    BatteryOptimizationManager,
    private val onboardingPreferences:
    OnboardingPreferences,
    private val importanceSettingsPreferences:
    ImportanceSettingsPreferences,
    private val installedAppProvider:
    InstalledAppProvider
) : ViewModel() {

    private val _uiState =
        MutableStateFlow(
            OnboardingUiState(
                hasNotificationAccess =
                    notificationAccessManager
                        .hasNotificationAccess(),
                isBatteryOptimizationExempt =
                    batteryOptimizationManager
                        .isBatteryOptimizationExempt()
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

    fun retryLoadingInstalledApps() {
        loadInstalledApps()
    }

    fun onAppSearchQueryChanged(
        query: String
    ) {
        _uiState.update { currentState ->
            currentState.copy(
                appSearchQuery = query
            )
        }
    }

    fun onIntroCompleted() {
        _uiState.update { currentState ->
            val nextStage =
                when {
                    !currentState.hasNotificationAccess ->
                        OnboardingStage.NOTIFICATION_ACCESS

                    !currentState.isBatteryOptimizationExempt ->
                        OnboardingStage.BATTERY_OPTIMIZATION

                    else ->
                        OnboardingStage.IMPORTANT_APPS
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
                        if (
                            currentState
                                .isBatteryOptimizationExempt
                        ) {
                            OnboardingStage.IMPORTANT_APPS
                        } else {
                            OnboardingStage.BATTERY_OPTIMIZATION
                        }
                    } else {
                        currentState.stage
                    }
            )
        }
    }

    fun onNotificationAccessDeferred() {
        _uiState.update { currentState ->
            currentState.copy(
                stage =
                    OnboardingStage.BATTERY_OPTIMIZATION
            )
        }
    }

    fun createBatterySettingsIntent(): Intent {
        return batteryOptimizationManager
            .createBatterySettingsIntent()
    }

    fun refreshBatteryOptimizationStatus() {
        val isExempt =
            batteryOptimizationManager
                .isBatteryOptimizationExempt()

        _uiState.update { currentState ->
            currentState.copy(
                isBatteryOptimizationExempt = isExempt,
                stage =
                    if (isExempt) {
                        OnboardingStage.IMPORTANT_APPS
                    } else {
                        currentState.stage
                    }
            )
        }
    }

    fun onBatteryOptimizationDeferred() {
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
        if (
            _uiState.value.isSavingSettings ||
            _uiState.value.isSetupCompleted
        ) {
            return
        }

        val currentState = _uiState.value

        _uiState.update { state ->
            state.copy(
                isSavingSettings = true,
                hasSetupSaveError = false
            )
        }

        viewModelScope.launch {
            try {
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

                _uiState.update { state ->
                    state.copy(
                        isSavingSettings = false,
                        isSetupCompleted = true,
                        hasSetupSaveError = false
                    )
                }
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                _uiState.update { state ->
                    state.copy(
                        isSavingSettings = false,
                        hasSetupSaveError = true
                    )
                }
            }
        }
    }
}
