package com.hanseo.noti.ui.home

import androidx.compose.foundation.Image
import androidx.compose.foundation.Canvas
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.background
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.SnackbarDuration
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.SnackbarResult
import androidx.compose.material3.SwipeToDismissBox
import androidx.compose.material3.SwipeToDismissBoxValue
import androidx.compose.material3.rememberSwipeToDismissBoxState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.hanseo.noti.R
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale
import androidx.compose.material3.TextButton
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.width
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import com.hanseo.noti.domain.model.ClassifiedNotification
import com.hanseo.noti.ui.model.NotificationUiModel
import kotlinx.coroutines.launch

@Composable
fun HomeScreen(
    uiState: HomeUiState,
    hasNotificationAccess: Boolean,
    onRequestNotificationAccess: () -> Unit,
    onShowAllNotifications: () -> Unit,
    onLessImportant: (ClassifiedNotification) -> Unit,
    onMarkAsRead: (String) -> Unit,
    onMarkAsUnread: (String) -> Unit,
    onEditCriteria: () -> Unit,
    modifier: Modifier = Modifier
) {
    if (!hasNotificationAccess) {
        NotificationAccessRequiredContent(
            onRequestAccess =
                onRequestNotificationAccess,
            modifier = modifier.fillMaxSize()
        )

        return
    }

    val importantNotifications =
        uiState.importantNotifications

    val snackbarHostState = remember {
        SnackbarHostState()
    }

    val coroutineScope = rememberCoroutineScope()

    var expandedNotificationKey by rememberSaveable {
        mutableStateOf<String?>(null)
    }

    var selectedReasonNotificationKey by rememberSaveable {
        mutableStateOf<String?>(null)
    }

    val selectedReasonNotification =
        importantNotifications.firstOrNull {
            notificationUiModel ->

            notificationUiModel
                .classifiedNotification
                .notification
                .key == selectedReasonNotificationKey
        }

    Box(
        modifier = modifier
            .fillMaxSize()
    ) {
        Column(
            modifier = Modifier.fillMaxSize()
        ) {
            HomeHeader(
                notificationCount =
                    importantNotifications.size,

                totalNotificationCount =
                    uiState.todayTotalNotificationCount,

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

                    todayImportantCount =
                        uiState.todayImportantNotificationCount,

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
                        key = { notificationUiModel ->
                            notificationUiModel
                                .classifiedNotification
                                .notification
                                .key
                        }
                    ) { notificationUiModel ->
                        val notificationKey =
                            notificationUiModel
                                .classifiedNotification
                                .notification
                                .key

                        val isExpanded =
                            expandedNotificationKey ==
                                notificationKey

                        SwipeableNotificationCard(
                            onMarkAsRead = {
                                if (
                                    expandedNotificationKey ==
                                    notificationKey
                                ) {
                                    expandedNotificationKey = null
                                }

                                onMarkAsRead(notificationKey)

                                coroutineScope.launch {
                                    val result =
                                        snackbarHostState
                                            .showSnackbar(
                                                message =
                                                    "확인한 알림으로 옮겼어요",
                                                actionLabel =
                                                    "실행 취소",
                                                duration =
                                                    SnackbarDuration.Short
                                            )

                                    if (
                                        result ==
                                        SnackbarResult.ActionPerformed
                                    ) {
                                        onMarkAsUnread(
                                            notificationKey
                                        )
                                    }
                                }
                            }
                        ) {
                            NotificationCard(
                                notificationUiModel =
                                    notificationUiModel,

                                isExpanded = isExpanded,

                                onCardClick = {
                                    expandedNotificationKey =
                                        if (isExpanded) {
                                            null
                                        } else {
                                            notificationKey
                                        }
                                },

                                onReasonClick = {
                                    selectedReasonNotificationKey =
                                        notificationKey
                                }
                            )
                        }
                    }
                }
            }
        }

        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(24.dp)
        )
    }

    selectedReasonNotification?.let {
            notificationUiModel ->

        ImportanceReasonBottomSheet(
            notificationUiModel = notificationUiModel,

            onDismiss = {
                selectedReasonNotificationKey = null
            },

            onLessImportantClick = {
                onLessImportant(
                    notificationUiModel
                        .classifiedNotification
                )

                selectedReasonNotificationKey = null
                expandedNotificationKey = null
            },

            onEditCriteriaClick = {
                selectedReasonNotificationKey = null
                expandedNotificationKey = null
                onEditCriteria()
            }
        )
    }
}

@Composable
private fun NotificationAccessRequiredContent(
    onRequestAccess: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.padding(
            horizontal = 24.dp
        ),
        horizontalAlignment =
            Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        NotificationAccessRequiredVisual()

        Spacer(modifier = Modifier.height(28.dp))

        Text(
            text = stringResource(
                R.string.home_notification_access_title
            ),
            style = MaterialTheme.typography.headlineSmall,
            color = MaterialTheme.colorScheme.onBackground,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = stringResource(
                R.string.home_notification_access_description
            ),
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(32.dp))

        Button(
            onClick = onRequestAccess,
            modifier = Modifier
                .fillMaxWidth()
                .height(56.dp),
            shape = RoundedCornerShape(18.dp)
        ) {
            Text(
                text = stringResource(
                    R.string.home_notification_access_button
                ),
                style = MaterialTheme.typography.titleMedium
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = stringResource(
                R.string.home_notification_access_footer
            ),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
    }
}

@Composable
private fun NotificationAccessRequiredVisual(
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .size(160.dp)
            .background(
                color = MaterialTheme.colorScheme.primaryContainer,
                shape = CircleShape
            ),
        contentAlignment = Alignment.Center
    ) {
        Box(
            modifier = Modifier
                .size(108.dp)
                .background(
                    color = MaterialTheme.colorScheme.surface,
                    shape = CircleShape
                ),
            contentAlignment = Alignment.Center
        ) {
            Box(
                modifier = Modifier.size(72.dp),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    painter = painterResource(
                        R.drawable.ic_nav_notifications
                    ),
                    contentDescription = null,
                    modifier = Modifier.size(52.dp),
                    tint = MaterialTheme.colorScheme.primary
                )

                Box(
                    modifier = Modifier
                        .align(Alignment.TopEnd)
                        .size(30.dp)
                        .background(
                            color = MaterialTheme.colorScheme.primary,
                            shape = CircleShape
                        ),
                    contentAlignment = Alignment.Center
                ) {
                    ClockIcon()
                }
            }
        }
    }
}

@Composable
private fun ClockIcon() {
    val color = MaterialTheme.colorScheme.onPrimary

    Canvas(modifier = Modifier.size(18.dp)) {
        val strokeWidth = 1.8.dp.toPx()
        val center = Offset(
            x = size.width / 2f,
            y = size.height / 2f
        )

        drawCircle(
            color = color,
            radius = size.minDimension * 0.4f,
            center = center,
            style = Stroke(width = strokeWidth)
        )

        drawLine(
            color = color,
            start = center,
            end = Offset(
                x = center.x,
                y = size.height * 0.28f
            ),
            strokeWidth = strokeWidth,
            cap = StrokeCap.Round
        )

        drawLine(
            color = color,
            start = center,
            end = Offset(
                x = size.width * 0.68f,
                y = size.height * 0.58f
            ),
            strokeWidth = strokeWidth,
            cap = StrokeCap.Round
        )
    }
}

@Composable
private fun HomeHeader(
    notificationCount: Int,
    totalNotificationCount: Int,
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

    val description =
        when {
            notificationCount > 0 -> {
                "알림 ${totalNotificationCount}개 중 " +
                        "중요한 내용만 골랐어요"
            }

            totalNotificationCount > 0 -> {
                "오늘 도착한 ${totalNotificationCount}개 알림을 " +
                        "모두 정리했어요"
            }

            else -> {
                "새 알림이 오면 중요한 내용만 골라드려요"
            }
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

        Spacer(
            modifier = Modifier.height(12.dp)
        )

        Text(
            text = description,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
@Composable
private fun HomeEmptyContent(
    todayTotalCount: Int,
    todayImportantCount: Int,
    onShowAllNotifications: () -> Unit,
    modifier: Modifier = Modifier
) {
    val description =
        if (todayImportantCount > 0) {
            "중요한 알림을 모두 확인했어요.\n" +
                    "새 알림이 오면 다시 알려드릴게요."
        } else if (todayTotalCount > 0) {
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
private fun SwipeableNotificationCard(
    onMarkAsRead: () -> Unit,
    content: @Composable () -> Unit
) {
    val dismissState = rememberSwipeToDismissBoxState()

    LaunchedEffect(dismissState.currentValue) {
        if (
            dismissState.currentValue ==
            SwipeToDismissBoxValue.EndToStart
        ) {
            onMarkAsRead()

            dismissState.snapTo(
                SwipeToDismissBoxValue.Settled
            )
        }
    }

    val swipeBackgroundColor by animateColorAsState(
        targetValue =
            if (
                dismissState.dismissDirection ==
                SwipeToDismissBoxValue.EndToStart
            ) {
                MaterialTheme.colorScheme.primary
            } else {
                Color.Transparent
            },
        label = "swipeBackgroundColor"
    )

    SwipeToDismissBox(
        state = dismissState,
        enableDismissFromStartToEnd = false,
        enableDismissFromEndToStart = true,
        backgroundContent = {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .clip(RoundedCornerShape(20.dp))
                    .background(
                        swipeBackgroundColor
                    )
                    .padding(horizontal = 20.dp),
                contentAlignment = Alignment.CenterEnd
            ) {
                Text(
                    text = "확인 완료",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onPrimary
                )
            }
        },
        content = {
            content()
        }
    )
}

@Composable
private fun NotificationCard(
    notificationUiModel: NotificationUiModel,
    isExpanded: Boolean,
    onCardClick: () -> Unit,
    onReasonClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val classifiedNotification =
        notificationUiModel.classifiedNotification

    val notification =
        classifiedNotification.notification

    val importance =
        classifiedNotification.importance

    val containerColor by animateColorAsState(
        targetValue =
            if (isExpanded) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surface
            },
        label = "notificationCardColor"
    )

    Card(
        onClick = onCardClick,
        modifier = modifier
            .fillMaxWidth()
            .animateContentSize(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(
            containerColor = containerColor
        )
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.Top
        ) {
            NotificationAppIcon(
                appIcon = notificationUiModel.appIcon
            )

            Spacer(
                modifier = Modifier.width(12.dp)
            )

            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement =
                    Arrangement.spacedBy(6.dp)
            ) {
                Text(
                    text = notificationUiModel.appName,
                    style =
                        MaterialTheme.typography.labelMedium,
                    color =
                        MaterialTheme.colorScheme.onSurfaceVariant
                )

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

                AnimatedVisibility(
                    visible = isExpanded
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 12.dp),
                        horizontalArrangement =
                            Arrangement.SpaceBetween,
                        verticalAlignment =
                            Alignment.CenterVertically
                    ) {
                        ReasonButton(
                            onClick = onReasonClick
                        )

                        ClassificationSourceChip(
                            isForced = importance.isForced
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun ReasonButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        onClick = onClick,
        modifier = modifier,
        shape = CircleShape,
        color = MaterialTheme.colorScheme.surface
    ) {
        Row(
            modifier = Modifier.padding(
                horizontal = 14.dp,
                vertical = 9.dp
            ),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(20.dp)
                    .background(
                        color = MaterialTheme.colorScheme.primary,
                        shape = CircleShape
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "i",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onPrimary
                )
            }

            Spacer(modifier = Modifier.width(8.dp))

            Text(
                text = "판정 이유  ›",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary
            )
        }
    }
}

@Composable
private fun ClassificationSourceChip(
    isForced: Boolean,
    modifier: Modifier = Modifier
) {
    val label =
        if (isForced) {
            "내 기준"
        } else {
            "자동 판정"
        }

    val containerColor =
        if (isForced) {
            MaterialTheme.colorScheme.primary.copy(
                alpha = 0.10f
            )
        } else {
            MaterialTheme.colorScheme.surfaceVariant
        }

    val contentColor =
        if (isForced) {
            MaterialTheme.colorScheme.primary
        } else {
            MaterialTheme.colorScheme.onSurfaceVariant
        }

    Surface(
        modifier = modifier,
        shape = CircleShape,
        color = containerColor
    ) {
        Text(
            text = label,
            modifier = Modifier.padding(
                horizontal = 16.dp,
                vertical = 10.dp
            ),
            style = MaterialTheme.typography.labelLarge,
            color = contentColor
        )
    }
}

@Composable
private fun NotificationAppIcon(
    appIcon: android.graphics.Bitmap?,
    modifier: Modifier = Modifier
) {
    if (appIcon != null) {
        Image(
            bitmap = appIcon.asImageBitmap(),
            contentDescription = null,
            modifier = modifier
                .size(48.dp)
                .clip(CircleShape)
        )
    } else {
        Box(
            modifier = modifier
                .size(48.dp)
                .background(
                    color =
                        MaterialTheme.colorScheme.surfaceVariant,
                    shape = CircleShape
                ),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                painter = painterResource(
                    R.drawable.ic_nav_notifications
                ),
                contentDescription = null,
                modifier = Modifier.size(24.dp),
                tint =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
