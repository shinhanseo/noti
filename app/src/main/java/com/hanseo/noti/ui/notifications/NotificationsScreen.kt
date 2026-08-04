package com.hanseo.noti.ui.notifications

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.animateContentSize
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
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
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

        if (uiState.notifications.isEmpty()) {
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
            style = MaterialTheme.typography.headlineLarge,
            color = MaterialTheme.colorScheme.onBackground
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
                        NotificationFilter.ALL ->
                            uiState.totalCount

                        NotificationFilter.UNREAD ->
                            uiState.unreadCount

                        NotificationFilter.IMPORTANT ->
                            uiState.importantCount
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
    count: Int,
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
                text = "$label $count",
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
private fun NotificationList(
    notifications: List<NotificationUiModel>,
    expandedNotificationKey: String?,
    onNotificationClick: (String) -> Unit,
    onReasonClick: (String) -> Unit,
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
                        date = entry.date
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

    Text(
        text = label,
        modifier = modifier.padding(
            top = 8.dp,
            bottom = 2.dp
        ),
        style = MaterialTheme.typography.titleMedium,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.onBackground
    )
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
    val message =
        when (selectedFilter) {
            NotificationFilter.ALL ->
                "아직 수집된 알림이 없어요"

            NotificationFilter.UNREAD ->
                "안 읽은 알림이 없어요"

            NotificationFilter.IMPORTANT ->
                "중요한 알림이 없어요"
        }

    Box(
        modifier = modifier.fillMaxWidth(),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = message,
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

private fun buildNotificationListEntries(
    notifications: List<NotificationUiModel>,
    zoneId: ZoneId
): List<NotificationListEntry> {
    return buildList {
        var previousDate: LocalDate? = null

        notifications.forEach { notificationUiModel ->
            val notification =
                notificationUiModel
                    .classifiedNotification
                    .notification

            val postedDate =
                Instant
                    .ofEpochMilli(notification.postedAt)
                    .atZone(zoneId)
                    .toLocalDate()

            if (postedDate != previousDate) {
                add(
                    NotificationListEntry.DateHeader(
                        date = postedDate
                    )
                )

                previousDate = postedDate
            }

            add(
                NotificationListEntry.Notification(
                    notificationUiModel =
                        notificationUiModel
                )
            )
        }
    }
}

private sealed interface NotificationListEntry {
    val key: String

    data class DateHeader(
        val date: LocalDate
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
