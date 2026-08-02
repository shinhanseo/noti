package com.hanseo.noti.ui.main

import android.content.Intent
import androidx.lifecycle.ViewModel
import com.hanseo.noti.notification.NotificationAccessManager
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

@HiltViewModel
class MainViewModel @Inject constructor(
    private val notificationAccessManager:
        NotificationAccessManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(
        MainUiState(
            hasNotificationAccess =
                notificationAccessManager
                    .hasNotificationAccess()
        )
    )

    val uiState: StateFlow<MainUiState> =
        _uiState.asStateFlow()

    fun refreshNotificationAccess() {
        val hasNotificationAccess =
            notificationAccessManager
                .hasNotificationAccess()

        _uiState.update { currentState ->
            currentState.copy(
                hasNotificationAccess =
                    hasNotificationAccess
            )
        }
    }

    fun createNotificationAccessSettingsIntent():
        Intent {
        return notificationAccessManager
            .createNotificationAccessSettingsIntent()
    }
}
