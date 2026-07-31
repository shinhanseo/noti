package com.hanseo.noti

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Scaffold
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.hanseo.noti.ui.home.HomeScreen
import com.hanseo.noti.ui.home.HomeViewModel
import com.hanseo.noti.ui.home.HomeViewModelFactory
import com.hanseo.noti.ui.theme.NotiTheme

class MainActivity : ComponentActivity() {

    private val homeViewModel: HomeViewModel by lazy {
        val notificationRepository =
            (application as NotiApplication).notificationRepository

        ViewModelProvider(
            this,
            HomeViewModelFactory(
                notificationRepository = notificationRepository
            )
        )[HomeViewModel::class.java]
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        enableEdgeToEdge()

        setContent {
            val uiState by
            homeViewModel.uiState.collectAsStateWithLifecycle()

            NotiTheme {
                Scaffold(
                    modifier = Modifier.fillMaxSize()
                ) { innerPadding ->
                    HomeScreen(
                        uiState = uiState,
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
        }
    }
}