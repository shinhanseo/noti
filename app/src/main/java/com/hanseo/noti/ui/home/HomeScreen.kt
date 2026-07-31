package com.hanseo.noti.ui.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.hanseo.noti.domain.model.ClassifiedNotification

@Composable
fun HomeScreen(
    uiState: HomeUiState,
    modifier: Modifier = Modifier
) {
    if (uiState.importantNotifications.isEmpty()) {
        Box(
            modifier = modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            Text(text = "중요한 알림이 없어요")
        }

        return
    }

    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(
            items = uiState.importantNotifications,
            key = { classifiedNotification ->
                classifiedNotification.notification.key
            }
        ) { classifiedNotification ->
            NotificationCard(
                classifiedNotification = classifiedNotification
            )
        }
    }
}

@Composable
private fun NotificationCard(
    classifiedNotification: ClassifiedNotification,
    modifier: Modifier = Modifier
) {
    val notification = classifiedNotification.notification
    val importance = classifiedNotification.importance

    Card(
        modifier = modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            Text(
                text = notification.title ?: "제목 없음"
            )

            notification.body?.let { body ->
                Text(text = body)
            }

            Text(
                text = "${importance.level} · ${importance.score}점"
            )

            importance.reasons
                .take(3)
                .forEach { reason ->
                    Text(
                        text = "• ${reason.description} (${reason.scoreDelta})"
                    )
                }
        }
    }
}