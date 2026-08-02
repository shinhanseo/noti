package com.hanseo.noti.ui.home

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.hanseo.noti.R
import com.hanseo.noti.domain.model.ClassifiedNotification
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale
import androidx.compose.material3.TextButton

@Composable
fun HomeScreen(
    uiState: HomeUiState,
    onShowAllNotifications: () -> Unit,
    modifier: Modifier = Modifier
) {
    val importantNotifications =
        uiState.importantNotifications

    Column(
        modifier = modifier
            .fillMaxSize()
    ) {
        HomeHeader(
            notificationCount =
                importantNotifications.size,
            modifier = Modifier.padding(
                horizontal = 24.dp
            )
        )

        Spacer(
            modifier = Modifier.height(28.dp)
        )

        if (importantNotifications.isEmpty()) {
            HomeEmptyContent(
                todayTotalCount =
                    uiState.todayTotalNotificationCount,

                onShowAllNotifications =
                    onShowAllNotifications,

                modifier = Modifier.weight(1f)
            )
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                contentPadding = PaddingValues(
                    start = 24.dp,
                    end = 24.dp,
                    bottom = 24.dp
                ),
                verticalArrangement =
                    Arrangement.spacedBy(12.dp)
            ) {
                items(
                    items = importantNotifications,
                    key = { classifiedNotification ->
                        classifiedNotification
                            .notification
                            .key
                    }
                ) { classifiedNotification ->
                    NotificationCard(
                        classifiedNotification =
                            classifiedNotification
                    )
                }
            }
        }
    }
}

@Composable
private fun HomeHeader(
    notificationCount: Int,
    modifier: Modifier = Modifier
) {
    val today = LocalDate.now()

    val todayText = remember(today) {
        today.format(
            DateTimeFormatter.ofPattern(
                "M월 d일 EEEE",
                Locale.KOREAN
            )
        )
    }

    val notificationMessage =
        if (notificationCount > 0) {
            "먼저 확인할 알림은\n${notificationCount}개예요."
        } else {
            "아직 확인할 알림이\n없어요."
        }

    Column(
        modifier = modifier.fillMaxWidth()
    ) {
        Text(
            text = "noti.",
            style =
                MaterialTheme.typography.headlineLarge,
            color =
                MaterialTheme.colorScheme.onBackground
        )

        Spacer(
            modifier = Modifier.height(32.dp)
        )

        Text(
            text = todayText,
            style =
                MaterialTheme.typography.bodyLarge,
            color =
                MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(
            modifier = Modifier.height(12.dp)
        )

        Text(
            text = notificationMessage,
            style =
                MaterialTheme.typography.headlineLarge,
            color =
                MaterialTheme.colorScheme.onBackground
        )
    }
}
@Composable
private fun HomeEmptyContent(
    todayTotalCount: Int,
    onShowAllNotifications: () -> Unit,
    modifier: Modifier = Modifier
) {
    val description =
        if (todayTotalCount > 0) {
            "오늘 도착한 ${todayTotalCount}개 알림은\n" +
                    "모두 일반 알림으로 정리했어요."
        } else {
            "아직 오늘 도착한 알림이 없어요.\n" +
                    "새로운 알림이 오면 안전하게 정리할게요."
        }

    Box(
        modifier = modifier.fillMaxWidth(),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment =
                Alignment.CenterHorizontally
        ) {
            Image(
                painter = painterResource(
                    R.drawable.empty_state_visual
                ),
                contentDescription = null,
                modifier = Modifier.size(160.dp)
            )

            Spacer(
                modifier = Modifier.height(28.dp)
            )

            Text(
                text = "지금은 조용하네요",
                style =
                    MaterialTheme.typography.headlineSmall,
                color =
                    MaterialTheme.colorScheme.onBackground
            )

            Spacer(
                modifier = Modifier.height(12.dp)
            )

            Text(
                text = description,
                style =
                    MaterialTheme.typography.bodyLarge,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )

            if (todayTotalCount > 0) {
                Spacer(
                    modifier = Modifier.height(16.dp)
                )

                TextButton(
                    onClick =
                        onShowAllNotifications
                ) {
                    Text(
                        text = "전체 알림 보기",
                        style =
                            MaterialTheme.typography.labelLarge,
                        color =
                            MaterialTheme.colorScheme.primary
                    )
                }
            }
        }
    }
}

@Composable
private fun NotificationCard(
    classifiedNotification:
    ClassifiedNotification,
    modifier: Modifier = Modifier
) {
    val notification =
        classifiedNotification.notification

    val importance =
        classifiedNotification.importance

    Card(
        modifier = modifier.fillMaxWidth()
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement =
                Arrangement.spacedBy(6.dp)
        ) {
            Text(
                text =
                    notification.title
                        ?: "제목 없음",
                style =
                    MaterialTheme.typography.titleMedium,
                color =
                    MaterialTheme.colorScheme.onSurface
            )

            notification.body?.let { body ->
                Text(
                    text = body,
                    style =
                        MaterialTheme.typography.bodyMedium,
                    color =
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Text(
                text =
                    "${importance.level} · " +
                            "${importance.score}점",
                style =
                    MaterialTheme.typography.labelLarge,
                color =
                    MaterialTheme.colorScheme.primary
            )

            importance.reasons
                .take(3)
                .forEach { reason ->
                    Text(
                        text =
                            "• ${reason.description} " +
                                    "(${reason.scoreDelta})",
                        style =
                            MaterialTheme.typography.bodySmall,
                        color =
                            MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
        }
    }
}