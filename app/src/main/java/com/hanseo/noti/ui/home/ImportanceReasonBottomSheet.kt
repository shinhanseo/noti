package com.hanseo.noti.ui.home

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.hanseo.noti.domain.importance.ImportanceReasonType
import com.hanseo.noti.ui.components.notification.NotificationReasonBottomSheet
import com.hanseo.noti.ui.model.NotificationUiModel

@Composable
fun ImportanceReasonBottomSheet(
    notificationUiModel: NotificationUiModel,
    onDismiss: () -> Unit,
    onLessImportantClick: () -> Unit,
    onEditCriteriaClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val importance =
        notificationUiModel
            .classifiedNotification
            .importance

    val isUserCriterion =
        importance.reasons.any { reason ->
            reason.type ==
                ImportanceReasonType.IMPORTANT_APP ||
                reason.type ==
                ImportanceReasonType.GLOBAL_IMPORTANT_KEYWORD
        }

    NotificationReasonBottomSheet(
        notificationUiModel = notificationUiModel,
        onDismiss = onDismiss,
        secondaryActionText =
            if (isUserCriterion) {
                "내 기준에서 수정하기"
            } else {
                "덜 중요하게 보기"
            },
        onSecondaryActionClick =
            if (isUserCriterion) {
                onEditCriteriaClick
            } else {
                onLessImportantClick
            },
        modifier = modifier
    )
}
