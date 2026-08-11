package com.hanseo.noti.ui.main

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.hanseo.noti.ui.navigation.MainNavHost
import com.hanseo.noti.ui.navigation.MainTab
import com.hanseo.noti.ui.navigation.NotiBottomNavigation
import com.hanseo.noti.ui.navigation.NotiRoutes
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.ui.unit.dp

@Composable
fun MainScreen(
    uiState: MainUiState,
    onRequestNotificationAccess: () -> Unit,
    modifier: Modifier = Modifier
) {
    val navController =
        rememberNavController()

    val backStackEntry by
    navController
        .currentBackStackEntryAsState()

    val currentRoute =
        backStackEntry
            ?.destination
            ?.route

    val showBottomNavigation =
        MainTab.entries.any { tab ->
            tab.route == currentRoute
        }

    Scaffold(
        modifier = modifier,
        containerColor =
            MaterialTheme.colorScheme.background,
        contentWindowInsets = WindowInsets(
            left = 0.dp,
            top = 0.dp,
            right = 0.dp,
            bottom = 0.dp
        ),
        bottomBar = {
            if (showBottomNavigation) {
                NotiBottomNavigation(
                    currentRoute = currentRoute,
                    onTabSelected = { selectedTab ->
                        if (
                            currentRoute !=
                            selectedTab.route
                        ) {
                            navController.navigate(
                                selectedTab.route
                            ) {
                                popUpTo(
                                    NotiRoutes.HOME
                                ) {
                                    inclusive = false
                                }

                                launchSingleTop = true
                            }
                        }
                    }
                )
            }
        }
    ) { innerPadding ->
        MainNavHost(
            navController = navController,
            hasNotificationAccess =
                uiState.hasNotificationAccess,
            onRequestNotificationAccess =
                onRequestNotificationAccess,
            modifier = Modifier.padding(
                innerPadding
            )
        )
    }
}
