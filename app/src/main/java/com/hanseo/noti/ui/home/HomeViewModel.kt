package com.hanseo.noti.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.data.repository.NotificationRepository
import com.hanseo.noti.domain.importance.ImportanceLevel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val notificationRepository: NotificationRepository
) : ViewModel() {

    val uiState: StateFlow<HomeUiState> =
        notificationRepository.observeAll()
            .map { notifications ->
                val importantNotifications =
                    notifications.filter { classifiedNotification ->
                        classifiedNotification.importance.level ==
                                ImportanceLevel.IMPORTANT &&
                                !classifiedNotification.notification.isRemoved
                    }

                HomeUiState(
                    importantNotifications = importantNotifications
                )
            }
            .stateIn(
                scope = viewModelScope,
                started = SharingStarted.WhileSubscribed(
                    stopTimeoutMillis = 5_000
                ),
                initialValue = HomeUiState()
            )
}