package com.hanseo.noti.ui.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.hanseo.noti.data.apps.InstalledAppProvider
import com.hanseo.noti.data.repository.NotificationFeedbackRepository
import com.hanseo.noti.data.repository.NotificationRepository
import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.importance.ImportanceLevel
import com.hanseo.noti.domain.model.ClassifiedNotification
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
            feedbackRepository.observeAllLabels()
        ) {
                notifications,
                appsByPackage,
                feedbackLabels ->

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

            val importantNotifications =
                todayNotifications
                    .filter { classifiedNotification ->
                        val notificationKey =
                            classifiedNotification
                                .notification
                                .key

                        val feedbackLabel =
                            feedbackLabels[
                                notificationKey
                            ]

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
                    .map { classifiedNotification ->
                        val packageName =
                            classifiedNotification
                                .notification
                                .packageName

                        val installedApp =
                            appsByPackage[packageName]

                        HomeNotificationUiModel(
                            classifiedNotification =
                                classifiedNotification,

                            appName =
                                installedApp?.displayName
                                    ?: packageName,

                            appIcon =
                                installedApp?.icon
                        )
                    }

            HomeUiState(
                importantNotifications =
                    importantNotifications,

                todayTotalNotificationCount =
                    todayNotifications.size
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

    fun markAsGeneral(
        classifiedNotification:
        ClassifiedNotification
    ) {
        saveFeedback(
            classifiedNotification =
                classifiedNotification,
            label = FeedbackLabel.GENERAL
        )
    }

    fun markAsImportant(
        classifiedNotification:
        ClassifiedNotification
    ) {
        saveFeedback(
            classifiedNotification =
                classifiedNotification,
            label = FeedbackLabel.IMPORTANT
        )
    }

    private fun saveFeedback(
        classifiedNotification:
        ClassifiedNotification,
        label: FeedbackLabel
    ) {
        viewModelScope.launch {
            feedbackRepository.save(
                classifiedNotification =
                    classifiedNotification,
                label = label
            )
        }
    }
}