package com.hanseo.noti.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.hanseo.noti.ui.criteria.MyCriteriaScreen
import com.hanseo.noti.ui.home.HomeScreen
import com.hanseo.noti.ui.home.HomeViewModel
import com.hanseo.noti.ui.notifications.NotificationsScreen

@Composable
fun MainNavHost(
    navController: NavHostController,
    hasNotificationAccess: Boolean,
    onRequestNotificationAccess: () -> Unit,
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
                onRequestNotificationAccess =
                    onRequestNotificationAccess,
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
            NotificationsScreen()
        }

        composable(NotiRoutes.MY_CRITERIA) {
            MyCriteriaScreen()
        }
    }
}

@Composable
private fun HomeRoute(
    hasNotificationAccess: Boolean,
    onRequestNotificationAccess: () -> Unit,
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

        onRequestNotificationAccess =
            onRequestNotificationAccess,

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
