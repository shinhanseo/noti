package com.hanseo.noti.ui.criteria

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.data.apps.InstalledAppProvider
import com.hanseo.noti.data.preferences.ImportanceSettingsPreferences
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class MyCriteriaViewModel @Inject constructor(
    private val importanceSettingsPreferences:
        ImportanceSettingsPreferences,
    private val installedAppProvider:
        InstalledAppProvider
) : ViewModel() {

    private val _uiState =
        MutableStateFlow(
            MyCriteriaUiState(
                isLoadingApps = true
            )
        )

    val uiState: StateFlow<MyCriteriaUiState> =
        _uiState.asStateFlow()

    init {
        observeSettings()
        loadInstalledApps()
    }

    private fun observeSettings() {
        viewModelScope.launch {
            importanceSettingsPreferences
                .settings
                .collect { settings ->
                    _uiState.update { currentState ->
                        val currentSelection =
                            currentState
                                .selectedExclusionAppPackage
                                ?.takeIf { packageName ->
                                    packageName in
                                        settings.importantApps
                                }

                        currentState.copy(
                            importantAppPackages =
                                settings.importantApps,
                            globalImportantKeywords =
                                settings.globalImportantKeywords,
                            exclusionKeywordsByPackage =
                                settings.exclusionKeywordsByPackage,
                            selectedExclusionAppPackage =
                                currentSelection
                                    ?: settings
                                        .importantApps
                                        .firstOrNull(),
                            isLoadingSettings = false,
                            hasSaveError = false
                        )
                    }
                }
        }
    }

    private fun loadInstalledApps() {
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

    fun onAppSearchQueryChanged(query: String) {
        _uiState.update { currentState ->
            currentState.copy(
                appSearchQuery = query
            )
        }
    }

    fun onImportantAppToggled(packageName: String) {
        val currentState = _uiState.value
        val updatedPackages =
            if (
                packageName in
                    currentState.importantAppPackages
            ) {
                currentState.importantAppPackages -
                    packageName
            } else {
                currentState.importantAppPackages +
                    packageName
            }

        _uiState.update { state ->
            state.copy(
                importantAppPackages = updatedPackages,
                selectedExclusionAppPackage =
                    state.selectedExclusionAppPackage
                        ?.takeIf { selectedPackage ->
                            selectedPackage in
                                updatedPackages
                        },
                exclusionKeywordsByPackage =
                    state.exclusionKeywordsByPackage
                        .filterKeys { savedPackage ->
                            savedPackage in updatedPackages
                        }
            )
        }

        saveSettings {
            importanceSettingsPreferences
                .updateImportantApps(
                    updatedPackages
                )
        }
    }

    fun onKeywordInputChanged(value: String) {
        _uiState.update { currentState ->
            currentState.copy(
                keywordInput = value
            )
        }
    }

    fun onKeywordAdded() {
        val currentState = _uiState.value
        val keyword = currentState.keywordInput.trim()

        if (keyword.isEmpty()) {
            return
        }

        val alreadyExists =
            currentState.globalImportantKeywords
                .any { savedKeyword ->
                    savedKeyword.equals(
                        other = keyword,
                        ignoreCase = true
                    )
                }

        if (alreadyExists) {
            _uiState.update { state ->
                state.copy(keywordInput = "")
            }
            return
        }

        val updatedKeywords =
            currentState.globalImportantKeywords +
                keyword

        _uiState.update { state ->
            state.copy(
                globalImportantKeywords =
                    updatedKeywords,
                keywordInput = ""
            )
        }

        saveSettings {
            importanceSettingsPreferences
                .updateGlobalImportantKeywords(
                    updatedKeywords
                )
        }
    }

    fun onKeywordRemoved(keyword: String) {
        val updatedKeywords =
            _uiState.value
                .globalImportantKeywords - keyword

        _uiState.update { currentState ->
            currentState.copy(
                globalImportantKeywords =
                    updatedKeywords
            )
        }

        saveSettings {
            importanceSettingsPreferences
                .updateGlobalImportantKeywords(
                    updatedKeywords
                )
        }
    }

    fun onExclusionAppSelected(packageName: String) {
        if (
            packageName !in
                _uiState.value.importantAppPackages
        ) {
            return
        }

        _uiState.update { currentState ->
            currentState.copy(
                selectedExclusionAppPackage =
                    packageName,
                exclusionKeywordInput = ""
            )
        }
    }

    fun onExclusionKeywordInputChanged(value: String) {
        _uiState.update { currentState ->
            currentState.copy(
                exclusionKeywordInput = value
            )
        }
    }

    fun onExclusionKeywordAdded() {
        val currentState = _uiState.value
        val packageName =
            currentState.selectedExclusionAppPackage
                ?: return
        val keyword =
            currentState.exclusionKeywordInput.trim()

        if (keyword.isEmpty()) {
            return
        }

        val currentKeywords =
            currentState
                .exclusionKeywordsByPackage[packageName]
                ?: emptySet()

        val alreadyExists =
            currentKeywords.any { savedKeyword ->
                savedKeyword.equals(
                    other = keyword,
                    ignoreCase = true
                )
            }

        if (alreadyExists) {
            _uiState.update { state ->
                state.copy(
                    exclusionKeywordInput = ""
                )
            }
            return
        }

        val updatedKeywords =
            currentKeywords + keyword

        updateLocalExclusionKeywords(
            packageName = packageName,
            keywords = updatedKeywords
        )

        saveSettings {
            importanceSettingsPreferences
                .updateExclusionKeywords(
                    packageName = packageName,
                    keywords = updatedKeywords
                )
        }
    }

    fun onExclusionKeywordRemoved(keyword: String) {
        val currentState = _uiState.value
        val packageName =
            currentState.selectedExclusionAppPackage
                ?: return
        val updatedKeywords =
            currentState.selectedExclusionKeywords -
                keyword

        updateLocalExclusionKeywords(
            packageName = packageName,
            keywords = updatedKeywords
        )

        saveSettings {
            importanceSettingsPreferences
                .updateExclusionKeywords(
                    packageName = packageName,
                    keywords = updatedKeywords
                )
        }
    }

    private fun updateLocalExclusionKeywords(
        packageName: String,
        keywords: Set<String>
    ) {
        _uiState.update { currentState ->
            val updatedExclusions =
                currentState
                    .exclusionKeywordsByPackage
                    .toMutableMap()

            if (keywords.isEmpty()) {
                updatedExclusions.remove(packageName)
            } else {
                updatedExclusions[packageName] =
                    keywords
            }

            currentState.copy(
                exclusionKeywordsByPackage =
                    updatedExclusions,
                exclusionKeywordInput = ""
            )
        }
    }

    private fun saveSettings(
        operation: suspend () -> Unit
    ) {
        viewModelScope.launch {
            try {
                operation()
            } catch (error: CancellationException) {
                throw error
            } catch (error: Exception) {
                _uiState.update { currentState ->
                    currentState.copy(
                        hasSaveError = true
                    )
                }
            }
        }
    }
}
