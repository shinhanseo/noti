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
    modifier: Modifier = Modifier
) {
    NavHost(
        navController = navController,
        startDestination = NotiRoutes.HOME,
        modifier = modifier
    ) {
        composable(NotiRoutes.HOME) {
            HomeRoute()
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
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by
    viewModel.uiState
        .collectAsStateWithLifecycle()

    HomeScreen(
        uiState = uiState
    )
}