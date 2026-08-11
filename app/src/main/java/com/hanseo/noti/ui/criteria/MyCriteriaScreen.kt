package com.hanseo.noti.ui.criteria

import androidx.annotation.DrawableRes
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.hanseo.noti.R

@Composable
fun MyCriteriaScreen(
    importantAppCount: Int = 0,
    importantKeywordCount: Int = 0,
    exclusionKeywordCount: Int = 0,
    hasNotificationAccess: Boolean = false,
    onImportantAppsClick: () -> Unit = {},
    onImportantKeywordsClick: () -> Unit = {},
    onExclusionKeywordsClick: () -> Unit = {},
    onNotificationAccessClick: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier
            .fillMaxSize(),
        contentPadding = PaddingValues(
            start = 20.dp,
            end = 20.dp,
            bottom = 24.dp
        )
    ) {
        item {
            Text(
                text = "내 기준",
                style =
                    MaterialTheme.typography.headlineLarge,
                color =
                    MaterialTheme.colorScheme.onBackground
            )

            Spacer(
                modifier = Modifier.height(20.dp)
            )

            CriteriaSummaryCard(
                importantAppCount = importantAppCount,
                importantKeywordCount = importantKeywordCount
            )

            Spacer(
                modifier = Modifier.height(28.dp)
            )

            CriteriaSectionTitle(
                text = "중요하게 볼 알림"
            )

            Spacer(
                modifier = Modifier.height(10.dp)
            )

            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp),
                color = MaterialTheme.colorScheme.surface
            ) {
                Column {
                    CriteriaMenuItem(
                        iconResId =
                            R.drawable.ic_criteria_keyword,
                        title = "중요 키워드",
                        description =
                            if (importantKeywordCount == 0) {
                                "중요하게 확인할 단어를 추가해보세요"
                            } else {
                                "${importantKeywordCount}개 키워드"
                            },
                        onClick = onImportantKeywordsClick
                    )

                    CriteriaMenuDivider()

                    CriteriaMenuItem(
                        iconResId =
                            R.drawable.ic_criteria_apps,
                        title = "중요 앱",
                        description =
                            if (importantAppCount == 0) {
                                "먼저 확인하고 싶은 앱을 선택해보세요"
                            } else {
                                "${importantAppCount}개 앱"
                            },
                        onClick = onImportantAppsClick
                    )
                }
            }

            Spacer(
                modifier = Modifier.height(28.dp)
            )

            CriteriaSectionTitle(
                text = "중요 앱에서 제외할 알림"
            )

            Spacer(
                modifier = Modifier.height(10.dp)
            )

            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp),
                color = MaterialTheme.colorScheme.surface
            ) {
                CriteriaMenuItem(
                    iconResId =
                        R.drawable.ic_criteria_exclusion,
                    title = "앱별 제외 키워드",
                    description =
                        if (exclusionKeywordCount == 0) {
                            "광고처럼 넘기고 싶은 표현을 설정해보세요"
                        } else {
                            "${exclusionKeywordCount}개 제외 키워드"
                        },
                    onClick = onExclusionKeywordsClick
                )
            }

            Spacer(
                modifier = Modifier.height(28.dp)
            )

            CriteriaSectionTitle(
                text = "앱 설정"
            )

            Spacer(
                modifier = Modifier.height(10.dp)
            )

            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp),
                color = MaterialTheme.colorScheme.surface
            ) {
                NotificationAccessMenuItem(
                    hasNotificationAccess =
                        hasNotificationAccess,
                    onClick =
                        onNotificationAccessClick
                )
            }

            Spacer(
                modifier = Modifier.height(24.dp)
            )

            Text(
                text = "알림 내용과 설정은 기기 안에서만 처리돼요.",
                modifier = Modifier.fillMaxWidth(),
                style =
                    MaterialTheme.typography.bodySmall,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun CriteriaSummaryCard(
    importantAppCount: Int,
    importantKeywordCount: Int,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color =
            MaterialTheme.colorScheme.primaryContainer
    ) {
        Row(
            modifier = Modifier.padding(
                horizontal = 18.dp,
                vertical = 18.dp
            ),
            verticalAlignment =
                Alignment.CenterVertically
        ) {
            Surface(
                modifier = Modifier.size(48.dp),
                shape = CircleShape,
                color =
                    MaterialTheme.colorScheme.primary
            ) {
                Box(
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        painter = painterResource(
                            id = R.drawable.ic_nav_notifications
                        ),
                        contentDescription = null,
                        modifier = Modifier.size(25.dp),
                        tint =
                            MaterialTheme.colorScheme.onPrimary
                    )
                }
            }

            Spacer(
                modifier = Modifier.width(14.dp)
            )

            Column(
                verticalArrangement =
                    Arrangement.spacedBy(3.dp)
            ) {
                Text(
                    text = "나의 알림 기준",
                    style =
                        MaterialTheme.typography.titleMedium,
                    color =
                        MaterialTheme.colorScheme.onPrimaryContainer
                )

                Text(
                    text =
                        "중요 앱 ${importantAppCount}개 · " +
                            "중요 키워드 ${importantKeywordCount}개",
                    style =
                        MaterialTheme.typography.bodyMedium,
                    color =
                        MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}

@Composable
private fun CriteriaMenuItem(
    @DrawableRes iconResId: Int,
    title: String,
    description: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(
                horizontal = 16.dp,
                vertical = 16.dp
            ),
        verticalAlignment =
            Alignment.CenterVertically
    ) {
        CriteriaBadge(
            iconResId = iconResId
        )

        Spacer(
            modifier = Modifier.width(14.dp)
        )

        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement =
                Arrangement.spacedBy(2.dp)
        ) {
            Text(
                text = title,
                style =
                    MaterialTheme.typography.titleSmall,
                color =
                    MaterialTheme.colorScheme.onSurface
            )

            Text(
                text = description,
                style =
                    MaterialTheme.typography.bodySmall,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        Text(
            text = "›",
            style =
                MaterialTheme.typography.headlineSmall,
            color =
                MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun NotificationAccessMenuItem(
    hasNotificationAccess: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(
                horizontal = 16.dp,
                vertical = 16.dp
            ),
        verticalAlignment =
            Alignment.CenterVertically
    ) {
        CriteriaBadge(
            iconResId =
                R.drawable.ic_criteria_permission
        )

        Spacer(
            modifier = Modifier.width(14.dp)
        )

        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement =
                Arrangement.spacedBy(2.dp)
        ) {
            Text(
                text = "알림 접근 권한",
                style =
                    MaterialTheme.typography.titleSmall,
                color =
                    MaterialTheme.colorScheme.onSurface
            )

            Text(
                text =
                    if (hasNotificationAccess) {
                        "알림을 정상적으로 읽고 있어요"
                    } else {
                        "알림을 읽으려면 권한이 필요해요"
                    },
                style =
                    MaterialTheme.typography.bodySmall,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        Text(
            text =
                if (hasNotificationAccess) {
                    "허용됨"
                } else {
                    "허용 필요"
                },
            style =
                MaterialTheme.typography.labelMedium,
            color =
                if (hasNotificationAccess) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.onSurfaceVariant
                }
        )
    }
}

@Composable
private fun CriteriaBadge(
    @DrawableRes iconResId: Int,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.size(46.dp),
        shape = CircleShape,
        color =
            MaterialTheme.colorScheme.primaryContainer
    ) {
        Box(
            contentAlignment = Alignment.Center
        ) {
            Icon(
                painter = painterResource(
                    id = iconResId
                ),
                contentDescription = null,
                modifier = Modifier.size(24.dp),
                tint = MaterialTheme.colorScheme.primary
            )
        }
    }
}

@Composable
private fun CriteriaSectionTitle(
    text: String,
    modifier: Modifier = Modifier
) {
    Text(
        text = text,
        modifier = modifier,
        style =
            MaterialTheme.typography.titleMedium,
        color =
            MaterialTheme.colorScheme.onBackground
    )
}

@Composable
private fun CriteriaMenuDivider() {
    HorizontalDivider(
        modifier = Modifier.padding(
            start = 76.dp
        ),
        color =
            MaterialTheme.colorScheme.outlineVariant
    )
}
