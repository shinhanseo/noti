package com.hanseo.noti.ui.criteria

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.data.preferences.ImportanceSettingsPreferences
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.WhileSubscribed
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

@HiltViewModel
class MyCriteriaViewModel @Inject constructor(
    importanceSettingsPreferences: ImportanceSettingsPreferences
) : ViewModel() {
    val uiState: StateFlow<MyCriteriaUiState> =
        importanceSettingsPreferences
            .settings
            .map { settings ->
                MyCriteriaUiState(
                    importantAppCount = settings.importantApps.size,
                    importantKeywordCount = settings.globalImportantKeywords.size,
                    exclusionKeywordCount =
                        settings
                            .exclusionKeywordsByPackage
                            .values
                            .sumOf { keywords ->
                                keywords.size
                            }
                )
            }
            .stateIn(
                scope = viewModelScope,

                started = SharingStarted.WhileSubscribed(
                    stopTimeoutMillis = 5_000
                ),

                initialValue = MyCriteriaUiState()
            )
}
