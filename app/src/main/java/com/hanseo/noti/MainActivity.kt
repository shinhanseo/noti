package com.hanseo.noti

import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.windowInsetsBottomHeight
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.getValue
import androidx.compose.runtime.key
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.hanseo.noti.ui.app.AppStartDestination
import com.hanseo.noti.ui.app.AppViewModel
import com.hanseo.noti.ui.navigation.NotiNavHost
import com.hanseo.noti.ui.theme.NotiTheme
import com.hanseo.noti.notification.NotificationAccessManager
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject
    lateinit var notificationAccessManager:
        NotificationAccessManager

    private val appViewModel: AppViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enableEdgeToEdge()

        setContent {
            val appUiState by
            appViewModel.uiState
                .collectAsStateWithLifecycle()

            NotiTheme {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(
                            MaterialTheme.colorScheme.background
                        )
                ) {
                    Scaffold(
                        modifier = Modifier.fillMaxSize(),
                        containerColor =
                            MaterialTheme.colorScheme.background
                    ) { innerPadding ->
                        when (appUiState.startDestination) {
                            AppStartDestination.LOADING -> {
                                Box(
                                    modifier = Modifier
                                        .fillMaxSize()
                                        .padding(innerPadding),
                                    contentAlignment = Alignment.Center
                                ) {
                                    CircularProgressIndicator()
                                }
                            }

                            AppStartDestination.ONBOARDING,
                            AppStartDestination.HOME -> {
                                key(appUiState.startDestination) {
                                    NotiNavHost(
                                        startDestination =
                                            appUiState.startDestination,
                                        modifier = Modifier
                                            .fillMaxSize()
                                            .padding(innerPadding)
                                    )
                                }
                            }
                        }
                    }

                    if (
                        appUiState.startDestination ==
                        AppStartDestination.HOME
                    ) {
                        Box(
                            modifier = Modifier
                                .align(Alignment.BottomCenter)
                                .fillMaxWidth()
                                .windowInsetsBottomHeight(
                                    WindowInsets.navigationBars
                                )
                                .background(
                                    MaterialTheme.colorScheme.surface
                                )
                        )
                    }
                }
            }
        }
    }

    override fun onResume() {
        super.onResume()

        val rebindRequested =
            notificationAccessManager
                .requestRebindIfNeeded()

        if (rebindRequested) {
            Log.d(
                TAG,
                "Notification listener rebind requested"
            )
        }
    }

    private companion object {
        const val TAG = "MainActivity"
    }
}
