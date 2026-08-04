package com.hanseo.noti.ui.notifications

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.data.apps.InstalledAppProvider
import com.hanseo.noti.data.repository.NotificationRepository
import com.hanseo.noti.data.repository.NotificationFeedbackRepository
import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.ui.model.NotificationUiModel
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.ZoneId
import javax.inject.Inject

@HiltViewModel
class NotificationsViewModel @Inject constructor(
    private val notificationRepository:
    NotificationRepository,

    private val feedbackRepository:
    NotificationFeedbackRepository,

    private val installedAppProvider:
    InstalledAppProvider
) : ViewModel() {

    private val selectedFilter =
        MutableStateFlow(NotificationFilter.ALL)

    private val installedAppsByPackage = flow {
        val appsByPackage =
            installedAppProvider
                .getLaunchableApps()
                .associateBy { installedApp ->
                    installedApp.packageName
                }

        emit(appsByPackage)
    }

    val uiState: StateFlow<NotificationsUiState> =
        combine(
            notificationRepository.observeAll(),
            installedAppsByPackage,
            feedbackRepository.observeAllLabels(),
            selectedFilter
        ) {
                notifications,
                appsByPackage,
                feedbackLabels,
                filter ->

            val sortedNotifications =
                notifications.sortedByDescending {
                        classifiedNotification ->

                    classifiedNotification
                        .notification
                        .postedAt
                }

            fun isImportant(
                classifiedNotification:
                ClassifiedNotification
            ): Boolean {
                val notificationKey =
                    classifiedNotification
                        .notification
                        .key

                return when (
                    feedbackLabels[notificationKey]
                ) {
                    FeedbackLabel.IMPORTANT -> true
                    FeedbackLabel.GENERAL -> false
                    null ->
                        classifiedNotification
                            .importance
                            .level ==
                                ImportanceLevel.IMPORTANT
                }
            }

            val unreadCount =
                sortedNotifications.count {
                        classifiedNotification ->

                    classifiedNotification
                        .notification
                        .readAt == null
                }

            val importantCount =
                sortedNotifications.count(::isImportant)

            val filteredNotifications =
                sortedNotifications.filter {
                        classifiedNotification ->

                    when (filter) {
                        NotificationFilter.ALL -> true

                        NotificationFilter.UNREAD ->
                            classifiedNotification
                                .notification
                                .readAt == null

                        NotificationFilter.IMPORTANT ->
                            isImportant(
                                classifiedNotification
                            )
                    }
                }

            val notificationUiModels =
                filteredNotifications
                    .map { classifiedNotification ->
                        val packageName =
                            classifiedNotification
                                .notification
                                .packageName

                        val installedApp =
                            appsByPackage[packageName]

                        NotificationUiModel(
                            classifiedNotification =
                                classifiedNotification,

                            appName =
                                installedApp?.displayName
                                    ?: packageName,

                            appIcon =
                                installedApp?.icon
                        )
                    }

            NotificationsUiState(
                notifications =
                    notificationUiModels,

                selectedFilter =
                    filter,

                unreadCount =
                    unreadCount,

                totalCount =
                    sortedNotifications.size,

                importantCount =
                    importantCount
            )
        }
            .stateIn(
                scope = viewModelScope,

                started =
                    SharingStarted.WhileSubscribed(
                        stopTimeoutMillis = 5_000
                    ),

                initialValue =
                    NotificationsUiState()
            )

    fun onFilterSelected(filter: NotificationFilter) {
        selectedFilter.value = filter
    }

    fun markAsRead(notificationKey: String) {
        viewModelScope.launch {
            notificationRepository.markAsRead(
                notificationKey = notificationKey
            )
        }
    }

    fun markAllAsRead(date: LocalDate) {
        viewModelScope.launch {
            val zoneId = ZoneId.systemDefault()

            val startMillis =
                date
                    .atStartOfDay(zoneId)
                    .toInstant()
                    .toEpochMilli()

            val endMillis =
                date
                    .plusDays(1)
                    .atStartOfDay(zoneId)
                    .toInstant()
                    .toEpochMilli()

            notificationRepository.markAllAsReadBetween(
                startMillis = startMillis,
                endMillis = endMillis
            )
        }
    }
}
