package com.hanseo.noti.ui.home

import com.hanseo.noti.ui.model.NotificationUiModel

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.BottomSheetDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.hanseo.noti.domain.importance.ImportanceReason
import com.hanseo.noti.domain.importance.ImportanceReasonType

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ImportanceReasonBottomSheet(
    notificationUiModel: NotificationUiModel,
    onDismiss: () -> Unit,
    onLessImportantClick: () -> Unit,
    onEditCriteriaClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val sheetState = rememberModalBottomSheetState(
        skipPartiallyExpanded = true
    )

    val classifiedNotification =
        notificationUiModel.classifiedNotification

    val importance =
        classifiedNotification.importance

    val isUserCriterion =
        importance.reasons.any { reason ->
            reason.type ==
                ImportanceReasonType.IMPORTANT_APP ||
                reason.type ==
                ImportanceReasonType.GLOBAL_IMPORTANT_KEYWORD
        }

    val secondaryActionText =
        if (isUserCriterion) {
            "내 기준에서 수정하기"
        } else {
            "덜 중요하게 보기"
        }

    val onSecondaryActionClick =
        if (isUserCriterion) {
            onEditCriteriaClick
        } else {
            onLessImportantClick
        }

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        modifier = modifier,
        sheetState = sheetState,
        containerColor = MaterialTheme.colorScheme.surface,
        dragHandle = {
            BottomSheetDefaults.DragHandle(
                color = MaterialTheme.colorScheme.outline
            )
        }
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .navigationBarsPadding()
                .padding(
                    start = 24.dp,
                    end = 24.dp,
                    bottom = 24.dp
                )
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement =
                    Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "왜 중요한 알림인가요?",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.onSurface
                )

                CloseButton(
                    onClick = onDismiss
                )
            }

            Spacer(modifier = Modifier.height(20.dp))

            NotificationSummary(
                notificationUiModel = notificationUiModel
            )

            Spacer(modifier = Modifier.height(28.dp))

            Text(
                text = "판단한 이유",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface
            )

            Spacer(modifier = Modifier.height(18.dp))

            if (importance.reasons.isEmpty()) {
                Text(
                    text = "저장된 판정 이유가 없어요.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            } else {
                Column(
                    verticalArrangement =
                        Arrangement.spacedBy(18.dp)
                ) {
                    importance.reasons.forEach { reason ->
                        ImportanceReasonRow(
                            reason = reason
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(28.dp))

            Surface(
                onClick = onSecondaryActionClick,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(18.dp),
                color = MaterialTheme.colorScheme.primaryContainer
            ) {
                Box(
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = secondaryActionText,
                        style = MaterialTheme.typography.titleSmall,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Button(
                onClick = onDismiss,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(18.dp)
            ) {
                Text(
                    text = "확인",
                    style = MaterialTheme.typography.titleMedium
                )
            }
        }
    }
}

@Composable
private fun NotificationSummary(
    notificationUiModel: NotificationUiModel,
    modifier: Modifier = Modifier
) {
    val notification =
        notificationUiModel
            .classifiedNotification
            .notification

    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = MaterialTheme.colorScheme.surfaceVariant
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            BottomSheetAppIcon(
                notificationUiModel = notificationUiModel
            )

            Spacer(modifier = Modifier.width(14.dp))

            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement =
                    Arrangement.spacedBy(4.dp)
            ) {
                Text(
                    text = notificationUiModel.appName,
                    style = MaterialTheme.typography.bodyMedium,
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
                    ?.takeIf { body ->
                        body.isNotBlank()
                    }
                    ?.let { body ->
                        Text(
                            text = body,
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            maxLines = 2,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
            }
        }
    }
}

@Composable
private fun BottomSheetAppIcon(
    notificationUiModel: NotificationUiModel,
    modifier: Modifier = Modifier
) {
    val appIcon = notificationUiModel.appIcon

    if (appIcon != null) {
        Image(
            bitmap = appIcon.asImageBitmap(),
            contentDescription = null,
            modifier = modifier
                .size(52.dp)
                .clip(CircleShape)
        )
    } else {
        Box(
            modifier = modifier
                .size(52.dp)
                .background(
                    color = MaterialTheme.colorScheme.primaryContainer,
                    shape = CircleShape
                ),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = notificationUiModel.appName
                    .firstOrNull()
                    ?.toString()
                    ?: "?",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.primary
            )
        }
    }
}

@Composable
private fun ImportanceReasonRow(
    reason: ImportanceReason,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        ReasonTypeIcon(
            reasonType = reason.type
        )

        Spacer(modifier = Modifier.width(14.dp))

        Text(
            text = reason.description,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

@Composable
private fun ReasonTypeIcon(
    reasonType: ImportanceReasonType,
    modifier: Modifier = Modifier
) {
    val symbol =
        when (reasonType) {
            ImportanceReasonType.IMPORTANT_APP -> "!"
            ImportanceReasonType.GLOBAL_IMPORTANT_KEYWORD -> "="
            ImportanceReasonType.AUTOMATIC_RULE -> "✓"
            ImportanceReasonType.USER_FEEDBACK -> "+"
            ImportanceReasonType.APP_EXCLUSION_KEYWORD -> "−"
        }

    Box(
        modifier = modifier
            .size(40.dp)
            .background(
                color = MaterialTheme.colorScheme.primaryContainer,
                shape = CircleShape
            ),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = symbol,
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.primary
        )
    }
}

@Composable
private fun CloseButton(
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        onClick = onClick,
        modifier = modifier.size(44.dp),
        shape = CircleShape,
        color = MaterialTheme.colorScheme.surfaceVariant
    ) {
        Box(
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "×",
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
