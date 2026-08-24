package com.hanseo.noti.ui.main

import android.content.Intent
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.notification.NotificationAccessManager
import com.hanseo.noti.notification.NotificationListenerConnectionStatus
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

@HiltViewModel
class MainViewModel @Inject constructor(
    private val notificationAccessManager:
        NotificationAccessManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(
        MainUiState(
            hasNotificationAccess =
                notificationAccessManager
                    .hasNotificationAccess(),
            listenerConnectionStatus =
                notificationAccessManager
                    .connectionStatus
                    .value
        )
    )

    val uiState: StateFlow<MainUiState> =
        _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            notificationAccessManager
                .connectionStatus
                .collect { connectionStatus ->
                    _uiState.update { currentState ->
                        currentState.copy(
                            hasNotificationAccess =
                                connectionStatus !=
                                NotificationListenerConnectionStatus
                                    .ACCESS_REQUIRED,
                            listenerConnectionStatus =
                                connectionStatus
                        )
                    }
                }
        }
    }

    fun refreshNotificationAccess() {
        notificationAccessManager
            .refreshConnectionStatus()

        notificationAccessManager
            .requestRebindIfNeeded()
    }

    fun createNotificationAccessSettingsIntent():
        Intent {
        return notificationAccessManager
            .createNotificationAccessSettingsIntent()
    }
}
