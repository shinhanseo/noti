package com.hanseo.noti.ui.criteria

import androidx.compose.foundation.BorderStroke
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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.hanseo.noti.data.apps.InstalledApp

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ExclusionKeywordsSettingsScreen(
    uiState: MyCriteriaUiState,
    onBackClick: () -> Unit,
    onAppSelected: (String) -> Unit,
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
            title = "앱별 제외 키워드",
            onBackClick = onBackClick
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = "중요 앱에서 온 알림이라도 등록한 표현이 포함되면 일반 알림으로 분류해요.",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(26.dp))

        if (uiState.importantApps.isEmpty()) {
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(18.dp),
                color = MaterialTheme.colorScheme.surface
            ) {
                Column(
                    modifier = Modifier.padding(20.dp)
                ) {
                    Text(
                        text = "먼저 중요 앱을 선택해주세요",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "제외 키워드는 중요 앱마다 따로 설정할 수 있어요.",
                        style = MaterialTheme.typography.bodyMedium,
                        color =
                            MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            Text(
                text = "적용할 중요 앱",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onBackground
            )

            Spacer(modifier = Modifier.height(14.dp))

            FlowRow(
                horizontalArrangement =
                    Arrangement.spacedBy(8.dp),
                verticalArrangement =
                    Arrangement.spacedBy(10.dp)
            ) {
                uiState.importantApps.forEach { app ->
                    ExclusionAppChip(
                        app = app,
                        selected =
                            app.packageName ==
                                uiState.selectedExclusionAppPackage,
                        keywordCount =
                            uiState
                                .exclusionKeywordsByPackage[
                                    app.packageName
                                ]
                                ?.size
                                ?: 0,
                        onClick = {
                            onAppSelected(app.packageName)
                        }
                    )
                }
            }

            Spacer(modifier = Modifier.height(26.dp))

            val selectedApp =
                uiState.importantApps
                    .firstOrNull { app ->
                        app.packageName ==
                            uiState.selectedExclusionAppPackage
                    }

            if (selectedApp != null) {
                Text(
                    text = "${selectedApp.displayName}에서 제외할 단어",
                    style = MaterialTheme.typography.titleLarge,
                    color = MaterialTheme.colorScheme.onBackground
                )

                Spacer(modifier = Modifier.height(14.dp))

                CriteriaKeywordInput(
                    value = uiState.exclusionKeywordInput,
                    placeholder = "예: [광고], 수신거부",
                    onValueChanged = onKeywordInputChanged,
                    onAddClick = onKeywordAdded
                )

                Spacer(modifier = Modifier.height(18.dp))

                if (uiState.selectedExclusionKeywords.isEmpty()) {
                    Text(
                        text = "이 앱에 등록한 제외 키워드가 없어요.",
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
                        uiState.selectedExclusionKeywords
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
            }
        }

        Spacer(modifier = Modifier.height(26.dp))

        CriteriaSaveError(
            visible = uiState.hasSaveError
        )

        Text(
            text = "‘광고’처럼 짧은 단어보다 ‘[광고]’, ‘광고성 정보’처럼 구체적인 표현을 권장해요.",
            modifier = Modifier.padding(bottom = 24.dp),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun ExclusionAppChip(
    app: InstalledApp,
    selected: Boolean,
    keywordCount: Int,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        onClick = onClick,
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        color =
            if (selected) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surface
            },
        border = BorderStroke(
            width = 1.dp,
            color =
                if (selected) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.outlineVariant
                }
        )
    ) {
        Row(
            modifier = Modifier.padding(
                horizontal = 12.dp,
                vertical = 10.dp
            ),
            verticalAlignment = Alignment.CenterVertically
        ) {
            CriteriaAppIcon(
                app = app,
                modifier = Modifier.height(34.dp)
            )

            Spacer(modifier = Modifier.width(8.dp))

            Column {
                Text(
                    text = app.displayName,
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurface,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )

                if (keywordCount > 0) {
                    Text(
                        text = "${keywordCount}개 제외",
                        style = MaterialTheme.typography.labelSmall,
                        color =
                            MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}
