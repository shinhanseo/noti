package com.hanseo.noti.ui.components.feedback

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.BottomSheetDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.rememberModalBottomSheetState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.hanseo.noti.domain.feedback.FeedbackLabel
import com.hanseo.noti.domain.feedback.FeedbackReasonCode

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeedbackReasonBottomSheet(
    feedbackLabel: FeedbackLabel,
    onDismiss: () -> Unit,
    onApply: (
        reasonCode: FeedbackReasonCode,
        reasonText: String?
    ) -> Unit,
    modifier: Modifier = Modifier
) {
    val sheetState = rememberModalBottomSheetState(
        skipPartiallyExpanded = true
    )

    var selectedReasonName by rememberSaveable(
        feedbackLabel
    ) {
        mutableStateOf<String?>(null)
    }

    var otherReasonText by rememberSaveable(
        feedbackLabel
    ) {
        mutableStateOf("")
    }

    val selectedReason = remember(selectedReasonName) {
        selectedReasonName?.let { name ->
            FeedbackReasonCode.entries
                .firstOrNull { reason ->
                    reason.name == name
                }
        }
    }

    val options = remember(feedbackLabel) {
        feedbackReasonOptions(feedbackLabel)
    }

    val isOtherSelected =
        selectedReason == FeedbackReasonCode.OTHER

    val canApply =
        selectedReason != null &&
            (
                !isOtherSelected ||
                    otherReasonText.isNotBlank()
                )

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
                .verticalScroll(rememberScrollState())
                .imePadding()
                .navigationBarsPadding()
                .padding(
                    start = 24.dp,
                    end = 24.dp,
                    bottom = 24.dp
                )
        ) {
            Text(
                text =
                    if (
                        feedbackLabel ==
                        FeedbackLabel.IMPORTANT
                    ) {
                        "중요한 이유가 무엇인가요?"
                    } else {
                        "일반으로 보는 이유가 무엇인가요?"
                    },
                style = MaterialTheme.typography.headlineSmall,
                color = MaterialTheme.colorScheme.onSurface
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text =
                    "선택한 이유를 기기에 저장해 " +
                        "분류 결과를 검토해요",
                style = MaterialTheme.typography.bodyMedium,
                color =
                    MaterialTheme.colorScheme
                        .onSurfaceVariant
            )

            Spacer(modifier = Modifier.height(20.dp))

            Column(
                verticalArrangement =
                    Arrangement.spacedBy(10.dp)
            ) {
                options.forEach { option ->
                    FeedbackReasonOptionRow(
                        option = option,
                        selected =
                            selectedReason == option.code,
                        onClick = {
                            selectedReasonName =
                                option.code.name

                            if (
                                option.code !=
                                FeedbackReasonCode.OTHER
                            ) {
                                otherReasonText = ""
                            }
                        }
                    )
                }
            }

            if (isOtherSelected) {
                Spacer(modifier = Modifier.height(12.dp))

                OutlinedTextField(
                    value = otherReasonText,
                    onValueChange = { text ->
                        otherReasonText = text.take(
                            MAX_OTHER_REASON_LENGTH
                        )
                    },
                    modifier = Modifier.fillMaxWidth(),
                    label = {
                        Text("기타 이유")
                    },
                    placeholder = {
                        Text("중요도를 바꾼 이유를 입력해주세요")
                    },
                    minLines = 2,
                    maxLines = 3,
                    shape = RoundedCornerShape(16.dp)
                )
            }

            Spacer(modifier = Modifier.height(20.dp))

            Button(
                onClick = {
                    val reason =
                        selectedReason
                            ?: return@Button

                    onApply(
                        reason,
                        otherReasonText
                            .trim()
                            .takeIf { text ->
                                reason ==
                                    FeedbackReasonCode.OTHER &&
                                    text.isNotEmpty()
                            }
                    )
                },
                enabled = canApply,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                shape = RoundedCornerShape(18.dp)
            ) {
                Text(
                    text = "적용하기",
                    style = MaterialTheme.typography.titleMedium
                )
            }
        }
    }
}

@Composable
private fun FeedbackReasonOptionRow(
    option: FeedbackReasonOption,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val containerColor =
        if (selected) {
            MaterialTheme.colorScheme.primaryContainer
        } else {
            MaterialTheme.colorScheme.surfaceVariant
        }

    val borderColor =
        if (selected) {
            MaterialTheme.colorScheme.primary
        } else {
            MaterialTheme.colorScheme.outlineVariant
        }

    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(18.dp),
        color = containerColor,
        border = androidx.compose.foundation.BorderStroke(
            width = 1.dp,
            color = borderColor
        )
    ) {
        Row(
            modifier = Modifier.padding(
                horizontal = 14.dp,
                vertical = 12.dp
            ),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier.size(40.dp),
                contentAlignment = Alignment.Center
            ) {
                RadioButton(
                    selected = selected,
                    onClick = onClick
                )
            }

            Column(
                modifier = Modifier
                    .weight(1f)
                    .padding(start = 8.dp),
                verticalArrangement =
                    Arrangement.spacedBy(3.dp)
            ) {
                Text(
                    text = option.title,
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.onSurface,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )

                Text(
                    text = option.description,
                    style = MaterialTheme.typography.bodySmall,
                    color =
                        MaterialTheme.colorScheme
                            .onSurfaceVariant,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
    }
}

data class FeedbackReasonOption(
    val code: FeedbackReasonCode,
    val title: String,
    val description: String
)

fun feedbackReasonTitle(
    reasonCode: FeedbackReasonCode
): String {
    return feedbackReasonOption(reasonCode).title
}

private fun feedbackReasonOptions(
    label: FeedbackLabel
): List<FeedbackReasonOption> {
    val reasonCodes =
        if (label == FeedbackLabel.IMPORTANT) {
            listOf(
                FeedbackReasonCode.SCHEDULE_DEADLINE,
                FeedbackReasonCode.ACTION_REQUEST,
                FeedbackReasonCode.FINANCE_SECURITY,
                FeedbackReasonCode.DELIVERY_RESERVATION,
                FeedbackReasonCode.IMPORTANT_SOURCE,
                FeedbackReasonCode.OTHER
            )
        } else {
            listOf(
                FeedbackReasonCode.PROMOTIONAL,
                FeedbackReasonCode.INFORMATIONAL,
                FeedbackReasonCode.REPEATED,
                FeedbackReasonCode.UNIMPORTANT_SOURCE,
                FeedbackReasonCode.NOT_TIME_SENSITIVE,
                FeedbackReasonCode.OTHER
            )
        }

    return reasonCodes.map(::feedbackReasonOption)
}

private fun feedbackReasonOption(
    reasonCode: FeedbackReasonCode
): FeedbackReasonOption {
    return when (reasonCode) {
        FeedbackReasonCode.SCHEDULE_DEADLINE ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "일정이나 마감이 있는 알림이에요",
                description =
                    "예약, 제출, 일정 시작처럼 놓치면 안 돼요"
            )

        FeedbackReasonCode.ACTION_REQUEST ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "답변하거나 처리할 요청이 있어요",
                description =
                    "확인, 승인, 회신처럼 직접 행동이 필요해요"
            )

        FeedbackReasonCode.FINANCE_SECURITY ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "결제·보안·계정 상태가 변했어요",
                description =
                    "출금, 결제 실패, 로그인처럼 확인이 필요해요"
            )

        FeedbackReasonCode.DELIVERY_RESERVATION ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "배송이나 예약 상태를 확인하고 싶어요",
                description =
                    "기다리던 상품이나 예약 상태가 바뀌었어요"
            )

        FeedbackReasonCode.IMPORTANT_SOURCE ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "중요한 앱이나 사람이 보냈어요",
                description =
                    "자주 확인해야 하는 앱이나 사람이에요"
            )

        FeedbackReasonCode.PROMOTIONAL ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "광고나 혜택 알림이에요",
                description =
                    "쿠폰, 이벤트, 추천처럼 홍보성 내용이에요"
            )

        FeedbackReasonCode.INFORMATIONAL ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "단순한 정보나 상태 안내예요",
                description =
                    "별도로 확인하거나 처리할 필요가 없어요"
            )

        FeedbackReasonCode.REPEATED ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "같은 내용이 반복됐어요",
                description =
                    "이미 확인했거나 비슷한 알림이 계속 와요"
            )

        FeedbackReasonCode.UNIMPORTANT_SOURCE ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "이 앱이나 사람은 중요하지 않아요",
                description =
                    "이 발신처의 알림을 자주 확인하지 않아요"
            )

        FeedbackReasonCode.NOT_TIME_SENSITIVE ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "지금 확인할 필요가 없어요",
                description =
                    "나중에 앱에서 확인해도 괜찮은 내용이에요"
            )

        FeedbackReasonCode.OTHER ->
            FeedbackReasonOption(
                code = reasonCode,
                title = "기타 이유 직접 입력",
                description =
                    "목록에 없는 이유를 직접 남길 수 있어요"
            )
    }
}

private const val MAX_OTHER_REASON_LENGTH = 100
