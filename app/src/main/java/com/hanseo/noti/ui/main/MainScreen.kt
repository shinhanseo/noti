package com.hanseo.noti.ui.main

import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.hanseo.noti.ui.navigation.MainNavHost
import com.hanseo.noti.ui.navigation.NotiBottomNavigation

@Composable
fun MainScreen(
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

    Scaffold(
        modifier = modifier,
        containerColor =
            MaterialTheme.colorScheme.background,
        bottomBar = {
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
                                navController
                                    .graph
                                    .findStartDestination()
                                    .id
                            ) {
                                saveState = true
                            }

                            launchSingleTop = true
                            restoreState = true
                        }
                    }
                }
            )
        }
    ) { innerPadding ->
        MainNavHost(
            navController = navController,
            modifier = Modifier.padding(
                innerPadding
            )
        )
    }
}