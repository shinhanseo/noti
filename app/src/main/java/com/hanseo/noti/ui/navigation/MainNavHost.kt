package com.hanseo.noti.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.hanseo.noti.ui.criteria.ExclusionKeywordsSettingsScreen
import com.hanseo.noti.ui.criteria.ImportantAppsSettingsScreen
import com.hanseo.noti.ui.criteria.ImportantKeywordsSettingsScreen
import com.hanseo.noti.ui.criteria.MyCriteriaScreen
import com.hanseo.noti.ui.criteria.MyCriteriaViewModel
import com.hanseo.noti.ui.home.HomeScreen
import com.hanseo.noti.ui.home.HomeViewModel
import com.hanseo.noti.ui.notifications.NotificationsScreen
import com.hanseo.noti.ui.notifications.NotificationsViewModel
import com.hanseo.noti.notification.NotificationListenerConnectionStatus

@Composable
fun MainNavHost(
    navController: NavHostController,
    hasNotificationAccess: Boolean,

    listenerConnectionStatus:
    NotificationListenerConnectionStatus,

    isBatteryOptimizationExempt: Boolean,
    onRequestNotificationAccess: () -> Unit,
    onRequestBatterySettings: () -> Unit,
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = NotiRoutes.HOME,
        modifier = modifier
    ) {
        composable(NotiRoutes.HOME) {
            HomeRoute(
                hasNotificationAccess =
                    hasNotificationAccess,

                listenerConnectionStatus =
                    listenerConnectionStatus,

                isBatteryOptimizationExempt =
                    isBatteryOptimizationExempt,

                onRequestNotificationAccess =
                    onRequestNotificationAccess,

                onRequestBatterySettings =
                    onRequestBatterySettings,

                onShowAllNotifications = {
                    navController.navigate(
                        NotiRoutes.NOTIFICATIONS
                    ) {
                        launchSingleTop = true
                    }
                },

                onEditCriteria = {
                    navController.navigate(
                        NotiRoutes.MY_CRITERIA
                    ) {
                        launchSingleTop = true
                    }
                }
            )
        }

        composable(NotiRoutes.NOTIFICATIONS) {
            NotificationsRoute()
        }

        composable(NotiRoutes.MY_CRITERIA) {
            MyCriteriaRoute(
                hasNotificationAccess =
                    hasNotificationAccess,
                isBatteryOptimizationExempt =
                    isBatteryOptimizationExempt,
                onRequestNotificationAccess =
                    onRequestNotificationAccess,
                onRequestBatterySettings =
                    onRequestBatterySettings,
                onImportantAppsClick = {
                    navController.navigate(
                        NotiRoutes.IMPORTANT_APPS_SETTINGS
                    )
                },
                onImportantKeywordsClick = {
                    navController.navigate(
                        NotiRoutes.IMPORTANT_KEYWORDS_SETTINGS
                    )
                },
                onExclusionKeywordsClick = {
                    navController.navigate(
                        NotiRoutes.EXCLUSION_KEYWORDS_SETTINGS
                    )
                }
            )
        }

        composable(
            NotiRoutes.IMPORTANT_APPS_SETTINGS
        ) {
            ImportantAppsSettingsRoute(
                onBackClick = {
                    navController.popBackStack()
                }
            )
        }

        composable(
            NotiRoutes.IMPORTANT_KEYWORDS_SETTINGS
        ) {
            ImportantKeywordsSettingsRoute(
                onBackClick = {
                    navController.popBackStack()
                }
            )
        }

        composable(
            NotiRoutes.EXCLUSION_KEYWORDS_SETTINGS
        ) {
            ExclusionKeywordsSettingsRoute(
                onBackClick = {
                    navController.popBackStack()
                }
            )
        }
    }
}

@Composable
private fun MyCriteriaRoute(
    hasNotificationAccess: Boolean,
    isBatteryOptimizationExempt: Boolean,
    onRequestNotificationAccess: () -> Unit,
    onRequestBatterySettings: () -> Unit,
    onImportantAppsClick: () -> Unit,
    onImportantKeywordsClick: () -> Unit,
    onExclusionKeywordsClick: () -> Unit,
    viewModel: MyCriteriaViewModel = hiltViewModel()
) {
    val uiState by
        viewModel.uiState
            .collectAsStateWithLifecycle()

    MyCriteriaScreen(
        importantAppCount =
            uiState.importantAppCount,
        importantKeywordCount =
            uiState.importantKeywordCount,
        exclusionKeywordCount =
            uiState.exclusionKeywordCount,
        hasNotificationAccess =
            hasNotificationAccess,
        isBatteryOptimizationExempt =
            isBatteryOptimizationExempt,
        onImportantAppsClick =
            onImportantAppsClick,
        onImportantKeywordsClick =
            onImportantKeywordsClick,
        onExclusionKeywordsClick =
            onExclusionKeywordsClick,
        onNotificationAccessClick =
            onRequestNotificationAccess,
        onBatterySettingsClick =
            onRequestBatterySettings
    )
}

@Composable
private fun ImportantAppsSettingsRoute(
    onBackClick: () -> Unit,
    viewModel: MyCriteriaViewModel = hiltViewModel()
) {
    val uiState by
        viewModel.uiState
            .collectAsStateWithLifecycle()

    ImportantAppsSettingsScreen(
        uiState = uiState,
        onBackClick = onBackClick,
        onSearchQueryChanged =
            viewModel::onAppSearchQueryChanged,
        onAppToggled =
            viewModel::onImportantAppToggled,
        onRetryClick =
            viewModel::retryLoadingInstalledApps
    )
}

@Composable
private fun ImportantKeywordsSettingsRoute(
    onBackClick: () -> Unit,
    viewModel: MyCriteriaViewModel = hiltViewModel()
) {
    val uiState by
        viewModel.uiState
            .collectAsStateWithLifecycle()

    ImportantKeywordsSettingsScreen(
        uiState = uiState,
        onBackClick = onBackClick,
        onKeywordInputChanged =
            viewModel::onKeywordInputChanged,
        onKeywordAdded =
            viewModel::onKeywordAdded,
        onKeywordRemoved =
            viewModel::onKeywordRemoved
    )
}

@Composable
private fun ExclusionKeywordsSettingsRoute(
    onBackClick: () -> Unit,
    viewModel: MyCriteriaViewModel = hiltViewModel()
) {
    val uiState by
        viewModel.uiState
            .collectAsStateWithLifecycle()

    ExclusionKeywordsSettingsScreen(
        uiState = uiState,
        onBackClick = onBackClick,
        onAppSelected =
            viewModel::onExclusionAppSelected,
        onKeywordInputChanged =
            viewModel::onExclusionKeywordInputChanged,
        onKeywordAdded =
            viewModel::onExclusionKeywordAdded,
        onKeywordRemoved =
            viewModel::onExclusionKeywordRemoved
    )
}

@Composable
private fun NotificationsRoute(
    viewModel: NotificationsViewModel = hiltViewModel()
) {
    val uiState by
    viewModel.uiState
        .collectAsStateWithLifecycle()

    NotificationsScreen(
        uiState = uiState,
        onFilterSelected =
            viewModel::onFilterSelected,
        onMarkAsRead =
            viewModel::markAsRead,
        onMarkAllAsRead =
            viewModel::markAllAsRead
    )
}

@Composable
private fun HomeRoute(
    hasNotificationAccess: Boolean,

    listenerConnectionStatus:
    NotificationListenerConnectionStatus,

    isBatteryOptimizationExempt: Boolean,
    onRequestNotificationAccess: () -> Unit,
    onRequestBatterySettings: () -> Unit,
    onShowAllNotifications: () -> Unit,
    onEditCriteria: () -> Unit,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by
    viewModel.uiState
        .collectAsStateWithLifecycle()

    HomeScreen(
        uiState = uiState,

        hasNotificationAccess =
            hasNotificationAccess,

        listenerConnectionStatus =
            listenerConnectionStatus,

        isBatteryOptimizationExempt =
            isBatteryOptimizationExempt,

        onRequestNotificationAccess =
            onRequestNotificationAccess,

        onRequestBatterySettings =
            onRequestBatterySettings,

        onShowAllNotifications =
            onShowAllNotifications,

        onLessImportant =
            viewModel::markAsGeneral,

        onMarkAsRead =
            viewModel::markAsRead,

        onMarkAsUnread =
            viewModel::markAsUnread,

        onEditCriteria =
            onEditCriteria
    )
}
