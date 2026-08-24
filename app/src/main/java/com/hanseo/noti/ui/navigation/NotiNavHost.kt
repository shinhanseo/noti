package com.hanseo.noti.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.hanseo.noti.ui.app.AppStartDestination
import com.hanseo.noti.ui.main.MainScreen
import com.hanseo.noti.ui.main.MainViewModel
import com.hanseo.noti.ui.onboarding.ImportantAppsScreen
import com.hanseo.noti.ui.onboarding.ImportantKeywordsScreen
import com.hanseo.noti.ui.onboarding.BatteryOptimizationScreen
import com.hanseo.noti.ui.onboarding.NotificationAccessScreen
import com.hanseo.noti.ui.onboarding.OnboardingScreen
import com.hanseo.noti.ui.onboarding.OnboardingStage
import com.hanseo.noti.ui.onboarding.OnboardingViewModel

@Composable
fun NotiNavHost(
    startDestination: AppStartDestination,
    modifier: Modifier = Modifier
) {
    val navController = rememberNavController()

    val startRoute =
        when (startDestination) {
            AppStartDestination.ONBOARDING -> {
                NotiRoutes.ONBOARDING
            }

            AppStartDestination.HOME -> {
                NotiRoutes.MAIN
            }

            AppStartDestination.LOADING -> {
                error(
                    "LOADING 상태에서는 NavHost를 만들 수 없습니다"
                )
            }
        }

    NavHost(
        navController = navController,
        startDestination = startRoute,
        modifier = modifier
    ) {
        composable(NotiRoutes.ONBOARDING) {
            OnboardingRoute(
                onSetupCompleted = {
                    navController.navigate(NotiRoutes.MAIN) {
                        popUpTo(NotiRoutes.ONBOARDING) {
                            inclusive = true
                        }

                        launchSingleTop = true
                    }
                }
            )
        }

        composable(NotiRoutes.MAIN) {
            MainRoute()
        }
    }
}

@Composable
private fun MainRoute(
    viewModel: MainViewModel = hiltViewModel()
) {
    val uiState by
        viewModel.uiState.collectAsStateWithLifecycle()

    val context = LocalContext.current

    LifecycleEventEffect(
        event = Lifecycle.Event.ON_RESUME
    ) {
        viewModel.refreshNotificationAccess()
    }

    MainScreen(
        uiState = uiState,
        onRequestNotificationAccess = {
            context.startActivity(
                viewModel
                    .createNotificationAccessSettingsIntent()
            )
        },
        onRequestBatterySettings = {
            context.startActivity(
                viewModel
                    .createBatterySettingsIntent()
            )
        }
    )
}

@Composable
private fun OnboardingRoute(
    onSetupCompleted: () -> Unit,
    viewModel: OnboardingViewModel = hiltViewModel()
) {
    val uiState by
    viewModel.uiState.collectAsStateWithLifecycle()

    val context = LocalContext.current

    LaunchedEffect(uiState.isSetupCompleted) {
        if (uiState.isSetupCompleted) {
            onSetupCompleted()
        }
    }

    LifecycleEventEffect(
        event = Lifecycle.Event.ON_RESUME
    ) {
        when (uiState.stage) {
            OnboardingStage.NOTIFICATION_ACCESS ->
                viewModel.refreshNotificationAccess()

            OnboardingStage.BATTERY_OPTIMIZATION ->
                viewModel.refreshBatteryOptimizationStatus()

            else -> Unit
        }
    }

    when (uiState.stage) {
        OnboardingStage.INTRO -> {
            OnboardingScreen(
                onIntroCompleted =
                    viewModel::onIntroCompleted
            )
        }

        OnboardingStage.NOTIFICATION_ACCESS -> {
            NotificationAccessScreen(
                onBackClick =
                    viewModel::onBackToIntro,

                onRequestAccess = {
                    val intent =
                        viewModel
                            .createNotificationAccessSettingsIntent()

                    context.startActivity(intent)
                },

                onDefer =
                    viewModel::onNotificationAccessDeferred
            )
        }

        OnboardingStage.BATTERY_OPTIMIZATION -> {
            BatteryOptimizationScreen(
                isExempt =
                    uiState.isBatteryOptimizationExempt,

                onBackClick =
                    viewModel::onBackToNotificationAccess,

                onOpenSettings = {
                    context.startActivity(
                        viewModel
                            .createBatterySettingsIntent()
                    )
                },

                onDefer =
                    viewModel::onBatteryOptimizationDeferred
            )
        }

        OnboardingStage.IMPORTANT_APPS -> {
            ImportantAppsScreen(
                uiState = uiState,

                onSearchQueryChanged =
                    viewModel::onAppSearchQueryChanged,

                onAppToggled =
                    viewModel::onImportantAppToggled,

                onSkipClick =
                    viewModel::onImportantAppsCompleted,

                onNextClick =
                    viewModel::onImportantAppsCompleted,

                onRetryClick =
                    viewModel::retryLoadingInstalledApps
            )
        }

        OnboardingStage.IMPORTANT_KEYWORDS -> {
            ImportantKeywordsScreen(
                uiState = uiState,
                onBackClick =
                    viewModel::onBackToImportantApps,
                onSkipClick =
                    viewModel::onSetupCompleted,
                onKeywordInputChanged =
                    viewModel::onKeywordInputChanged,
                onKeywordAdded =
                    viewModel::onKeywordAdded,
                onKeywordRemoved =
                    viewModel::onKeywordRemoved,
                onCompleteClick =
                    viewModel::onSetupCompleted
            )
        }
    }
}
