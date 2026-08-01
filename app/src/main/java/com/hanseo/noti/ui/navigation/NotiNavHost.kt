package com.hanseo.noti.ui.navigation

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.hanseo.noti.ui.app.AppStartDestination
import com.hanseo.noti.ui.home.HomeScreen
import com.hanseo.noti.ui.home.HomeViewModel
import com.hanseo.noti.ui.onboarding.OnboardingScreen
import com.hanseo.noti.ui.onboarding.OnboardingStage
import com.hanseo.noti.ui.onboarding.OnboardingViewModel
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.compose.LifecycleEventEffect
import com.hanseo.noti.ui.onboarding.NotificationAccessScreen

@Composable
fun NotiNavHost(
    startDestination: AppStartDestination,
    modifier: Modifier = Modifier
) {
    val navController = rememberNavController()

    val startRoute =
        when (startDestination) {
            AppStartDestination.ONBOARDING ->
                NotiRoutes.ONBOARDING

            AppStartDestination.HOME ->
                NotiRoutes.HOME

            AppStartDestination.LOADING ->
                error("LOADING 상태에서는 NavHost를 만들 수 없습니다")
        }

    NavHost(
        navController = navController,
        startDestination = startRoute,
        modifier = modifier
    ) {
        composable(NotiRoutes.ONBOARDING) {
            OnboardingRoute()
        }

        composable(NotiRoutes.HOME) {
            HomeRoute()
        }
    }
}

@Composable
private fun OnboardingRoute(
    viewModel: OnboardingViewModel = hiltViewModel()
) {
    val uiState by
    viewModel.uiState.collectAsStateWithLifecycle()

    val context = LocalContext.current

    LifecycleEventEffect(
        event = Lifecycle.Event.ON_RESUME
    ) {
        if (
            uiState.stage ==
            OnboardingStage.NOTIFICATION_ACCESS
        ) {
            viewModel.refreshNotificationAccess()
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
    }
}

@Composable
private fun HomeRoute(
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by
    viewModel.uiState.collectAsStateWithLifecycle()

    HomeScreen(
        uiState = uiState
    )
}

@Composable
private fun NotificationAccessPlaceholder() {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.Center
    ) {
        Text(text = "알림 접근 권한 화면")
    }
}