package com.hanseo.noti.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.data.apps.InstalledAppProvider
import com.hanseo.noti.data.repository.NotificationFeedbackRepository
import com.hanseo.noti.data.repository.NotificationRepository
import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.feedback.FeedbackReasonCode
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.ui.model.NotificationUiModel
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val notificationRepository:
    NotificationRepository,

    private val feedbackRepository:
    NotificationFeedbackRepository,

    private val installedAppProvider:
    InstalledAppProvider
) : ViewModel() {

    private val installedAppsByPackage = flow {
        val appsByPackage =
            installedAppProvider
                .getLaunchableApps()
                .associateBy { installedApp ->
                    installedApp.packageName
                }

        emit(appsByPackage)
    }

    val uiState: StateFlow<HomeUiState> =
        combine(
            notificationRepository.observeAll(),
            installedAppsByPackage,
            feedbackRepository.observeAll()
        ) {
                notifications,
                appsByPackage,
                feedbackByKey ->

            val zoneId = ZoneId.systemDefault()
            val today = LocalDate.now(zoneId)

            val todayNotifications =
                notifications.filter {
                        classifiedNotification ->

                    val postedDate =
                        Instant
                            .ofEpochMilli(
                                classifiedNotification
                                    .notification
                                    .postedAt
                            )
                            .atZone(zoneId)
                            .toLocalDate()

                    postedDate == today
                }

            val todayImportantNotifications =
                todayNotifications
                    .filter { classifiedNotification ->
                        val notificationKey =
                            classifiedNotification
                                .notification
                                .key

                        val feedbackLabel =
                            feedbackByKey[
                                notificationKey
                            ]?.label

                        when (feedbackLabel) {
                            FeedbackLabel.IMPORTANT ->
                                true

                            FeedbackLabel.GENERAL ->
                                false

                            null ->
                                classifiedNotification
                                    .importance
                                    .level ==
                                        ImportanceLevel.IMPORTANT
                        }
                    }

            val unreadImportantNotifications =
                todayImportantNotifications.filter {
                        classifiedNotification ->

                    classifiedNotification
                        .notification
                        .readAt == null
                }

            val importantNotifications =
                unreadImportantNotifications
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
                                installedApp?.icon,

                            feedback =
                                feedbackByKey[
                                    classifiedNotification
                                        .notification
                                        .key
                                ]
                        )
                    }

            HomeUiState(
                importantNotifications =
                    importantNotifications,

                todayTotalNotificationCount =
                    todayNotifications.size,

                todayImportantNotificationCount =
                    todayImportantNotifications.size,

                isLoading = false
            )
        }
            .stateIn(
                scope = viewModelScope,
                started =
                    SharingStarted.WhileSubscribed(
                        stopTimeoutMillis = 5_000
                    ),
                initialValue = HomeUiState()
            )

    fun markAsRead(notificationKey: String) {
        viewModelScope.launch {
            notificationRepository.markAsRead(
                notificationKey = notificationKey
            )
        }
    }

    fun markAsUnread(notificationKey: String) {
        viewModelScope.launch {
            notificationRepository.markAsUnread(
                notificationKey = notificationKey
            )
        }
    }

    fun saveFeedback(
        classifiedNotification:
        ClassifiedNotification,
        label: FeedbackLabel,
        reasonCode: FeedbackReasonCode,
        reasonText: String?
    ) {
        viewModelScope.launch {
            feedbackRepository.save(
                classifiedNotification =
                    classifiedNotification,
                label = label,
                reasonCode = reasonCode,
                reasonText = reasonText
            )
        }
    }
}
