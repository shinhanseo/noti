package com.hanseo.noti.ui.criteria

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ImportantKeywordsSettingsScreen(
    uiState: MyCriteriaUiState,
    onBackClick: () -> Unit,
    onKeywordInputChanged: (String) -> Unit,
    onKeywordAdded: () -> Unit,
    onKeywordRemoved: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp)
    ) {
        CriteriaSettingsTopBar(
            title = "중요 키워드",
            onBackClick = onBackClick
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = "어떤 앱에서 온 알림이든 등록한 단어가 포함되면 중요한 알림으로 분류해요.",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(24.dp))

        CriteriaKeywordInput(
            value = uiState.keywordInput,
            placeholder = "예: 과제, 마감, 배송",
            onValueChanged = onKeywordInputChanged,
            onAddClick = onKeywordAdded
        )

        Spacer(modifier = Modifier.height(28.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "추가한 단어",
                modifier = Modifier.weight(1f),
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onBackground
            )

            Text(
                text = "${uiState.importantKeywordCount}개",
                style = MaterialTheme.typography.bodyMedium,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        Spacer(modifier = Modifier.height(16.dp))

        if (uiState.globalImportantKeywords.isEmpty()) {
            Text(
                text = "아직 추가한 중요 키워드가 없어요.",
                style = MaterialTheme.typography.bodyMedium,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        } else {
            FlowRow(
                horizontalArrangement =
                    Arrangement.spacedBy(8.dp),
                verticalArrangement =
                    Arrangement.spacedBy(10.dp)
            ) {
                uiState.globalImportantKeywords
                    .sorted()
                    .forEach { keyword ->
                        CriteriaKeywordChip(
                            keyword = keyword,
                            onRemoveClick = {
                                onKeywordRemoved(keyword)
                            }
                        )
                    }
            }
        }

        Spacer(modifier = Modifier.height(30.dp))

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    color =
                        MaterialTheme.colorScheme.primaryContainer,
                    shape = RoundedCornerShape(18.dp)
                )
                .padding(18.dp)
        ) {
            Text(
                text = "짧고 흔한 단어는 주의해주세요",
                style = MaterialTheme.typography.titleSmall,
                color =
                    MaterialTheme.colorScheme.onPrimaryContainer
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = "‘확인’처럼 여러 알림에 자주 등장하는 단어보다 ‘과제 제출’처럼 구체적인 표현이 좋아요.",
                style = MaterialTheme.typography.bodyMedium,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        Spacer(modifier = Modifier.height(20.dp))

        CriteriaSaveError(
            visible = uiState.hasSaveError
        )

        Text(
            text = "변경한 내용은 자동으로 저장돼요.",
            modifier = Modifier.padding(
                top = 12.dp,
                bottom = 24.dp
            ),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}
