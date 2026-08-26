package com.hanseo.noti.ui.notifications

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.hanseo.noti.R
import com.hanseo.noti.ui.components.notification.NotificationReasonBottomSheet
import com.hanseo.noti.ui.model.NotificationUiModel
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale

@Composable
fun NotificationsScreen(
    uiState: NotificationsUiState,
    onFilterSelected: (NotificationFilter) -> Unit,
    onMarkAsRead: (String) -> Unit,
    onMarkAllAsRead: (LocalDate) -> Unit,
    modifier: Modifier = Modifier
) {
    var expandedNotificationKey by rememberSaveable {
        mutableStateOf<String?>(null)
    }

    var selectedReasonNotificationKey by rememberSaveable {
        mutableStateOf<String?>(null)
    }

    val selectedReasonNotification =
        uiState.notifications.firstOrNull {
                notificationUiModel ->

            notificationUiModel
                .classifiedNotification
                .notification
                .key == selectedReasonNotificationKey
        }

    Column(
        modifier = modifier
            .fillMaxSize()
            .background(
                MaterialTheme.colorScheme.background
            )
    ) {
        NotificationsHeader(
            uiState = uiState,
            onFilterSelected = onFilterSelected,
            modifier = Modifier.padding(
                horizontal = 24.dp
            )
        )

        Spacer(modifier = Modifier.height(20.dp))

        if (uiState.isLoading) {
            NotificationsSkeletonContent(
                modifier = Modifier.weight(1f)
            )
        } else if (uiState.notifications.isEmpty()) {
            EmptyNotificationsContent(
                selectedFilter = uiState.selectedFilter,
                modifier = Modifier.weight(1f)
            )
        } else {
            NotificationList(
                notifications = uiState.notifications,
                expandedNotificationKey =
                    expandedNotificationKey,
                onNotificationClick =
                    { notificationKey ->
                        expandedNotificationKey =
                            if (
                                expandedNotificationKey ==
                                notificationKey
                            ) {
                                null
                            } else {
                                notificationKey
                            }
                    },
                onReasonClick =
                    { notificationKey ->
                        selectedReasonNotificationKey =
                            notificationKey
                    },
                onMarkAllAsRead =
                    onMarkAllAsRead,
                modifier = Modifier.weight(1f)
            )
        }
    }

    selectedReasonNotification?.let {
            notificationUiModel ->

        NotificationReasonBottomSheet(
            notificationUiModel = notificationUiModel,
            onDismiss = {
                selectedReasonNotificationKey = null
            },
            onConfirm = {
                val notificationKey =
                    notificationUiModel
                        .classifiedNotification
                        .notification
                        .key

                onMarkAsRead(notificationKey)
                selectedReasonNotificationKey = null
            }
        )
    }
}

@Composable
private fun NotificationsHeader(
    uiState: NotificationsUiState,
    onFilterSelected: (NotificationFilter) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier.fillMaxWidth()
    ) {
        Text(
            text = "알림",
            style =
                MaterialTheme.typography.headlineLarge,
            color =
                MaterialTheme.colorScheme.onBackground
        )

        Spacer(modifier = Modifier.height(6.dp))

        Text(
            text = "모든 알림을 한곳에서 확인해요",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(18.dp))

        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            NotificationFilter.entries.forEach { filter ->
                NotificationFilterChip(
                    filter = filter,
                    count = when (filter) {
                        NotificationFilter.ALL -> {
                            if (uiState.isLoading) {
                                null
                            } else {
                                uiState.totalCount
                            }
                        }

                        NotificationFilter.UNREAD -> {
                            if (uiState.isLoading) {
                                null
                            } else {
                                uiState.unreadCount
                            }
                        }

                        NotificationFilter.IMPORTANT -> {
                            if (uiState.isLoading) {
                                null
                            } else {
                                uiState.importantCount
                            }
                        }
                    },
                    selected =
                        uiState.selectedFilter == filter,
                    onClick = {
                        onFilterSelected(filter)
                    }
                )
            }
        }
    }
}

@Composable
private fun NotificationFilterChip(
    filter: NotificationFilter,
    count: Int?,
    selected: Boolean,
    onClick: () -> Unit
) {
    val label =
        when (filter) {
            NotificationFilter.ALL -> "전체"
            NotificationFilter.UNREAD -> "안 읽음"
            NotificationFilter.IMPORTANT -> "중요"
        }

    FilterChip(
        selected = selected,
        onClick = onClick,
        label = {
            Text(
                text =
                    if (count == null) {
                        label
                    } else {
                        "$label $count"
                    },
                style = MaterialTheme.typography.labelLarge
            )
        },
        shape = CircleShape,
        colors = FilterChipDefaults.filterChipColors(
            containerColor =
                MaterialTheme.colorScheme.surface,
            labelColor =
                MaterialTheme.colorScheme.onSurfaceVariant,
            selectedContainerColor =
                MaterialTheme.colorScheme.primary,
            selectedLabelColor =
                MaterialTheme.colorScheme.onPrimary
        ),
        border = null
    )
}

@Composable
private fun NotificationsSkeletonContent(
    modifier: Modifier = Modifier
) {
    val infiniteTransition =
        rememberInfiniteTransition(
            label = "notificationsSkeleton"
        )

    val skeletonAlpha by
        infiniteTransition.animateFloat(
            initialValue = 0.45f,
            targetValue = 0.9f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = 900),
                repeatMode = RepeatMode.Reverse
            ),
            label = "notificationsSkeletonAlpha"
        )

    val skeletonColor =
        MaterialTheme.colorScheme.surfaceVariant.copy(
            alpha = skeletonAlpha
        )

    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(
                start = 24.dp,
                end = 24.dp,
                bottom = 24.dp
            ),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        Box(
            modifier = Modifier
                .padding(
                    top = 12.dp,
                    bottom = 6.dp
                )
                .width(62.dp)
                .height(20.dp)
                .clip(RoundedCornerShape(8.dp))
                .background(skeletonColor)
        )

        repeat(3) { index ->
            NotificationSkeletonCard(
                skeletonColor = skeletonColor,
                bodyWidth =
                    if (index == 1) {
                        170.dp
                    } else {
                        210.dp
                    }
            )
        }
    }
}

@Composable
private fun NotificationSkeletonCard(
    skeletonColor: Color,
    bodyWidth: Dp,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = MaterialTheme.colorScheme.surface
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.Top
        ) {
            Box(
                modifier = Modifier
                    .size(46.dp)
                    .clip(CircleShape)
                    .background(skeletonColor)
            )

            Spacer(modifier = Modifier.width(12.dp))

            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(9.dp)
            ) {
                Box(
                    modifier = Modifier
                        .width(104.dp)
                        .height(17.dp)
                        .clip(RoundedCornerShape(7.dp))
                        .background(skeletonColor)
                )

                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(15.dp)
                        .clip(RoundedCornerShape(7.dp))
                        .background(skeletonColor)
                )

                Box(
                    modifier = Modifier
                        .width(bodyWidth)
                        .height(15.dp)
                        .clip(RoundedCornerShape(7.dp))
                        .background(skeletonColor)
                )
            }

            Spacer(modifier = Modifier.width(12.dp))

            Box(
                modifier = Modifier
                    .width(38.dp)
                    .height(14.dp)
                    .clip(RoundedCornerShape(7.dp))
                    .background(skeletonColor)
            )
        }
    }
}

@Composable
private fun NotificationList(
    notifications: List<NotificationUiModel>,
    expandedNotificationKey: String?,
    onNotificationClick: (String) -> Unit,
    onReasonClick: (String) -> Unit,
    onMarkAllAsRead: (LocalDate) -> Unit,
    modifier: Modifier = Modifier
) {
    val listEntries = remember(notifications) {
        buildNotificationListEntries(
            notifications = notifications,
            zoneId = ZoneId.systemDefault()
        )
    }

    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(
            start = 24.dp,
            end = 24.dp,
            bottom = 24.dp
        ),
        verticalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        items(
            items = listEntries,
            key = { entry -> entry.key }
        ) { entry ->
            when (entry) {
                is NotificationListEntry.DateHeader -> {
                    DateSectionHeader(
                        date = entry.date,
                        hasUnreadNotifications =
                            entry.hasUnreadNotifications,
                        onMarkAllAsRead = {
                            onMarkAllAsRead(entry.date)
                        }
                    )
                }

                is NotificationListEntry.Notification -> {
                    val notificationKey =
                        entry
                            .notificationUiModel
                            .classifiedNotification
                            .notification
                            .key

                    NotificationListCard(
                        notificationUiModel =
                            entry.notificationUiModel,
                        isExpanded =
                            expandedNotificationKey ==
                                notificationKey,
                        onCardClick = {
                            onNotificationClick(
                                notificationKey
                            )
                        },
                        onReasonClick = {
                            onReasonClick(notificationKey)
                        }
                    )
                }
            }
        }
    }
}

@Composable
private fun DateSectionHeader(
    date: LocalDate,
    hasUnreadNotifications: Boolean,
    onMarkAllAsRead: () -> Unit,
    modifier: Modifier = Modifier
) {
    val today = LocalDate.now()

    val label = remember(date, today) {
        when (date) {
            today -> "오늘"
            today.minusDays(1) -> "어제"
            else ->
                date.format(
                    DateTimeFormatter.ofPattern(
                        "M월 d일 EEEE",
                        Locale.KOREAN
                    )
                )
        }
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(
            top = 8.dp,
            bottom = 2.dp
        ),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.onBackground
        )

        if (hasUnreadNotifications) {
            TextButton(
                onClick = onMarkAllAsRead,
                contentPadding = PaddingValues(
                    horizontal = 8.dp,
                    vertical = 4.dp
                )
            ) {
                Text(
                    text = "모두 읽음",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}

@Composable
private fun NotificationListCard(
    notificationUiModel: NotificationUiModel,
    isExpanded: Boolean,
    onCardClick: () -> Unit,
    onReasonClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val notification =
        notificationUiModel
            .classifiedNotification
            .notification

    val isUnread = notification.readAt == null

    val importance =
        notificationUiModel
            .classifiedNotification
            .importance

    val containerColor by animateColorAsState(
        targetValue =
            if (isExpanded) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surface
            },
        label = "notificationListCardColor"
    )

    val timeText = remember(notification.postedAt) {
        Instant
            .ofEpochMilli(notification.postedAt)
            .atZone(ZoneId.systemDefault())
            .format(
                DateTimeFormatter.ofPattern("HH:mm")
            )
    }

    Surface(
        onClick = onCardClick,
        modifier = modifier
            .fillMaxWidth()
            .animateContentSize(),
        shape = RoundedCornerShape(20.dp),
        color = containerColor
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.Top
        ) {
            Box(
                modifier = Modifier
                    .width(8.dp)
                    .padding(top = 5.dp),
                contentAlignment = Alignment.TopStart
            ) {
                if (isUnread) {
                    Box(
                        modifier = Modifier
                            .size(7.dp)
                            .background(
                                color =
                                    MaterialTheme.colorScheme.primary,
                                shape = CircleShape
                            )
                    )
                }
            }

            Spacer(modifier = Modifier.width(10.dp))

            NotificationAppIcon(
                notificationUiModel = notificationUiModel
            )

            Spacer(modifier = Modifier.width(12.dp))

            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(5.dp)
            ) {
                Text(
                    text =
                        "${notificationUiModel.appName} · $timeText",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )

                Text(
                    text = notification.title ?: "제목 없음",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )

                notification.body
                    ?.takeIf { body -> body.isNotBlank() }
                    ?.let { body ->
                        Text(
                            text = body,
                            style = MaterialTheme.typography.bodyMedium,
                            color =
                                MaterialTheme.colorScheme.onSurfaceVariant,
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis
                        )
                    }

                AnimatedVisibility(
                    visible = isExpanded
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 10.dp),
                        horizontalArrangement =
                            Arrangement.SpaceBetween,
                        verticalAlignment =
                            Alignment.CenterVertically
                    ) {
                        NotificationReasonButton(
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
private fun NotificationReasonButton(
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

    Surface(
        modifier = modifier,
        shape = CircleShape,
        color =
            if (isForced) {
                MaterialTheme.colorScheme.primary.copy(
                    alpha = 0.10f
                )
            } else {
                MaterialTheme.colorScheme.surfaceVariant
            }
    ) {
        Text(
            text = label,
            modifier = Modifier.padding(
                horizontal = 14.dp,
                vertical = 9.dp
            ),
            style = MaterialTheme.typography.labelLarge,
            color =
                if (isForced) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.onSurfaceVariant
                }
        )
    }
}

@Composable
private fun NotificationAppIcon(
    notificationUiModel: NotificationUiModel,
    modifier: Modifier = Modifier
) {
    val appIcon = notificationUiModel.appIcon

    if (appIcon != null) {
        Image(
            bitmap = appIcon.asImageBitmap(),
            contentDescription = null,
            modifier = modifier
                .size(46.dp)
                .clip(CircleShape)
        )
    } else {
        Box(
            modifier = modifier
                .size(46.dp)
                .background(
                    color =
                        MaterialTheme.colorScheme.surfaceVariant,
                    shape = CircleShape
                ),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = notificationUiModel.appName
                    .firstOrNull()
                    ?.uppercase()
                    ?: "?",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun EmptyNotificationsContent(
    selectedFilter: NotificationFilter,
    modifier: Modifier = Modifier
) {
    val title =
        when (selectedFilter) {
            NotificationFilter.ALL ->
                "아직 모아둔 알림이 없어요"

            NotificationFilter.UNREAD ->
                "모든 알림을 확인했어요"

            NotificationFilter.IMPORTANT ->
                "지금은 중요한 알림이 없어요"
        }

    val description =
        when (selectedFilter) {
            NotificationFilter.ALL ->
                "새 알림이 도착하면 중요도를 정리해\n" +
                    "이곳에 차곡차곡 보여드릴게요."

            NotificationFilter.UNREAD ->
                "새로 확인할 알림이 생기면\n" +
                    "이곳에서 바로 알려드릴게요."

            NotificationFilter.IMPORTANT ->
                "중요 앱과 키워드에 맞는 알림이 생기면\n" +
                    "놓치지 않도록 따로 모아드려요."
        }

    val helperText =
        when (selectedFilter) {
            NotificationFilter.ALL ->
                "알림은 기기 안에서만 안전하게 정리돼요"

            NotificationFilter.UNREAD ->
                "지금까지 도착한 알림을 모두 확인했어요"

            NotificationFilter.IMPORTANT ->
                "중요 앱과 키워드는 내 기준에서 바꿀 수 있어요"
        }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .padding(
                start = 24.dp,
                end = 24.dp,
                bottom = 40.dp
            ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Image(
                painter = painterResource(
                    R.drawable.empty_state_visual
                ),
                contentDescription = null,
                modifier = Modifier.size(148.dp)
            )

            Spacer(modifier = Modifier.height(22.dp))

            Text(
                text = title,
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onBackground,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = description,
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(24.dp))

            Surface(
                shape = RoundedCornerShape(18.dp),
                color = MaterialTheme.colorScheme.primaryContainer
                    .copy(alpha = 0.72f)
            ) {
                Row(
                    modifier = Modifier.padding(
                        horizontal = 16.dp,
                        vertical = 13.dp
                    ),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Surface(
                        modifier = Modifier.size(34.dp),
                        shape = CircleShape,
                        color = MaterialTheme.colorScheme.surface
                    ) {
                        Box(
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                painter = painterResource(
                                    R.drawable.ic_nav_notifications
                                ),
                                contentDescription = null,
                                modifier = Modifier.size(19.dp),
                                tint = MaterialTheme.colorScheme.primary
                            )
                        }
                    }

                    Spacer(modifier = Modifier.width(10.dp))

                    Text(
                        text = helperText,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

private fun buildNotificationListEntries(
    notifications: List<NotificationUiModel>,
    zoneId: ZoneId
): List<NotificationListEntry> {
    val notificationsByDate =
        notifications.groupBy { notificationUiModel ->
            val notification =
                notificationUiModel
                    .classifiedNotification
                    .notification

            Instant
                .ofEpochMilli(notification.postedAt)
                .atZone(zoneId)
                .toLocalDate()
        }

    return buildList {
        notificationsByDate.forEach {
                (date, notificationsForDate) ->

            add(
                NotificationListEntry.DateHeader(
                    date = date,
                    hasUnreadNotifications =
                        notificationsForDate.any {
                                notificationUiModel ->

                            notificationUiModel
                                .classifiedNotification
                                .notification
                                .readAt == null
                        }
                )
            )

            notificationsForDate.forEach {
                    notificationUiModel ->

                add(
                    NotificationListEntry.Notification(
                        notificationUiModel =
                            notificationUiModel
                    )
                )
            }
        }
    }
}

private sealed interface NotificationListEntry {
    val key: String

    data class DateHeader(
        val date: LocalDate,
        val hasUnreadNotifications: Boolean
    ) : NotificationListEntry {
        override val key: String =
            "date-${date.toEpochDay()}"
    }

    data class Notification(
        val notificationUiModel: NotificationUiModel
    ) : NotificationListEntry {
        override val key: String =
            "notification-${
                notificationUiModel
                    .classifiedNotification
                    .notification
                    .key
            }"
    }
}
