package com.hanseo.noti.ui.criteria

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.hanseo.noti.data.apps.InstalledApp

@Composable
fun ImportantAppsSettingsScreen(
    uiState: MyCriteriaUiState,
    onBackClick: () -> Unit,
    onSearchQueryChanged: (String) -> Unit,
    onAppToggled: (String) -> Unit,
    onRetryClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp)
    ) {
        CriteriaSettingsTopBar(
            title = "중요 앱",
            onBackClick = onBackClick
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = "선택한 앱에서 온 알림은 먼저 확인할 수 있도록 중요하게 분류해요.",
            style = MaterialTheme.typography.bodyLarge,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )

        Spacer(modifier = Modifier.height(20.dp))

        OutlinedTextField(
            value = uiState.appSearchQuery,
            onValueChange = onSearchQueryChanged,
            modifier = Modifier.fillMaxWidth(),
            placeholder = {
                Text(
                    text = "설치된 앱 검색",
                    style = MaterialTheme.typography.bodyLarge
                )
            },
            singleLine = true,
            shape = RoundedCornerShape(18.dp),
            textStyle = MaterialTheme.typography.bodyLarge,
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor =
                    MaterialTheme.colorScheme.surface,
                unfocusedContainerColor =
                    MaterialTheme.colorScheme.surface,
                focusedBorderColor =
                    MaterialTheme.colorScheme.primary,
                unfocusedBorderColor =
                    MaterialTheme.colorScheme.outlineVariant,
                cursorColor = MaterialTheme.colorScheme.primary
            )
        )

        Spacer(modifier = Modifier.height(24.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "설치된 앱",
                style = MaterialTheme.typography.titleLarge,
                color = MaterialTheme.colorScheme.onBackground
            )

            Spacer(modifier = Modifier.weight(1f))

            Text(
                text = "${uiState.importantAppCount}개 선택",
                style = MaterialTheme.typography.bodyMedium,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        when {
            uiState.isLoadingApps -> {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }

            uiState.hasAppLoadError -> {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment =
                            Alignment.CenterHorizontally
                    ) {
                        Text(
                            text = "설치된 앱을 불러오지 못했어요.",
                            style = MaterialTheme.typography.bodyMedium,
                            color =
                                MaterialTheme.colorScheme.onSurfaceVariant
                        )

                        TextButton(onClick = onRetryClick) {
                            Text(text = "다시 시도")
                        }
                    }
                }
            }

            uiState.filteredInstalledApps.isEmpty() -> {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "검색 결과가 없어요.",
                        style = MaterialTheme.typography.bodyMedium,
                        color =
                            MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            else -> {
                ImportantAppSettingsList(
                    apps = uiState.filteredInstalledApps,
                    selectedPackages =
                        uiState.importantAppPackages,
                    onAppToggled = onAppToggled,
                    modifier = Modifier.weight(1f)
                )
            }
        }

        CriteriaSaveError(
            visible = uiState.hasSaveError
        )

        Text(
            text = "변경한 내용은 자동으로 저장돼요.",
            modifier = Modifier.padding(
                top = 12.dp,
                bottom = 20.dp
            ),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun ImportantAppSettingsList(
    apps: List<InstalledApp>,
    selectedPackages: Set<String>,
    onAppToggled: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxWidth(),
        contentPadding = PaddingValues(bottom = 12.dp)
    ) {
        itemsIndexed(
            items = apps,
            key = { _, app -> app.packageName }
        ) { index, app ->
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        onAppToggled(app.packageName)
                    }
                    .padding(vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                CriteriaAppIcon(app = app)

                Spacer(modifier = Modifier.width(14.dp))

                Text(
                    text = app.displayName,
                    modifier = Modifier.weight(1f),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onBackground,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )

                Spacer(modifier = Modifier.width(12.dp))

                CriteriaSelectionIndicator(
                    selected =
                        app.packageName in selectedPackages
                )
            }

            if (index < apps.lastIndex) {
                HorizontalDivider(
                    modifier = Modifier.padding(start = 60.dp),
                    color =
                        MaterialTheme.colorScheme.outlineVariant
                )
            }
        }
    }
}
