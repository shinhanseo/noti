package com.hanseo.noti.ui.criteria

import androidx.annotation.DrawableRes
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.hanseo.noti.R
import com.hanseo.noti.ui.theme.NotiSuccess

@Composable
fun MyCriteriaScreen(
    importantAppCount: Int = 0,
    importantKeywordCount: Int = 0,
    exclusionKeywordCount: Int = 0,
    hasNotificationAccess: Boolean = false,
    isBatteryOptimizationExempt: Boolean = false,
    onImportantAppsClick: () -> Unit = {},
    onImportantKeywordsClick: () -> Unit = {},
    onExclusionKeywordsClick: () -> Unit = {},
    onNotificationAccessClick: () -> Unit = {},
    onBatterySettingsClick: () -> Unit = {},
    onPrivacyPolicyClick: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(
            start = 20.dp,
            end = 20.dp,
            bottom = 28.dp
        )
    ) {
        item {
            Text(
                text = "내 기준",
                style = MaterialTheme.typography.headlineLarge,
                color = MaterialTheme.colorScheme.onBackground
            )

            Spacer(modifier = Modifier.height(20.dp))

            CriteriaSummaryBanner(
                importantAppCount = importantAppCount,
                importantKeywordCount = importantKeywordCount
            )

            Spacer(modifier = Modifier.height(26.dp))

            CriteriaSectionTitle(text = "빠른 설정")

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                QuickSettingCard(
                    iconResId = R.drawable.ic_criteria_keyword,
                    title = "중요 키워드",
                    count = importantKeywordCount,
                    onClick = onImportantKeywordsClick,
                    modifier = Modifier.weight(1f)
                )

                QuickSettingCard(
                    iconResId = R.drawable.ic_criteria_apps,
                    title = "중요 앱",
                    count = importantAppCount,
                    onClick = onImportantAppsClick,
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            ExclusionSettingCard(
                exclusionKeywordCount = exclusionKeywordCount,
                onClick = onExclusionKeywordsClick
            )

            Spacer(modifier = Modifier.height(28.dp))

            CriteriaSectionTitle(text = "알림 수집 상태")

            Spacer(modifier = Modifier.height(10.dp))

            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(22.dp),
                color = MaterialTheme.colorScheme.surface,
                border = BorderStroke(
                    1.dp,
                    MaterialTheme.colorScheme.outlineVariant
                )
            ) {
                Column {
                    CollectionStatusItem(
                        iconResId = R.drawable.ic_criteria_permission,
                        title = "알림 접근 권한",
                        status =
                            if (hasNotificationAccess) {
                                "허용됨"
                            } else {
                                "설정 필요"
                            },
                        isEnabled = hasNotificationAccess,
                        onClick = onNotificationAccessClick
                    )

                    CriteriaMenuDivider()

                    CollectionStatusItem(
                        iconResId = R.drawable.ic_criteria_battery,
                        title = "배터리 사용 제한",
                        status =
                            if (isBatteryOptimizationExempt) {
                                "제한 없음"
                            } else {
                                "설정 필요"
                            },
                        isEnabled = isBatteryOptimizationExempt,
                        onClick = onBatterySettingsClick
                    )
                }
            }

            Spacer(modifier = Modifier.height(28.dp))

            CriteriaSectionTitle(
                text = stringResource(
                    R.string.service_information_title
                )
            )

            Spacer(modifier = Modifier.height(10.dp))

            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp),
                color = MaterialTheme.colorScheme.surface,
                border = BorderStroke(
                    1.dp,
                    MaterialTheme.colorScheme.outlineVariant
                )
            ) {
                ServiceInformationItem(
                    onClick = onPrivacyPolicyClick
                )
            }

            Spacer(modifier = Modifier.height(18.dp))

            Text(
                text = "알림 내용과 설정은 기기 안에서만 처리돼요.",
                modifier = Modifier.fillMaxWidth(),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun CriteriaSummaryBanner(
    importantAppCount: Int,
    importantKeywordCount: Int,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .height(170.dp)
            .clip(RoundedCornerShape(24.dp))
            .background(
                Brush.linearGradient(
                    colors = listOf(
                        Color(0xFF2474F5),
                        Color(0xFF6577F5)
                    )
                )
            )
    ) {
        BannerDecoration(
            modifier = Modifier.fillMaxSize()
        )

        Icon(
            painter = painterResource(
                R.drawable.ic_nav_notifications
            ),
            contentDescription = null,
            modifier = Modifier
                .align(Alignment.CenterEnd)
                .padding(end = 38.dp)
                .size(68.dp),
            tint = Color.White.copy(alpha = 0.82f)
        )

        Column(
            modifier = Modifier
                .align(Alignment.CenterStart)
                .fillMaxWidth(0.7f)
                .padding(horizontal = 22.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "나의 알림 기준",
                style = MaterialTheme.typography.titleLarge,
                color = Color.White
            )

            Text(
                text =
                    "중요 앱 ${importantAppCount}개 · " +
                        "중요 키워드 ${importantKeywordCount}개",
                style = MaterialTheme.typography.bodyLarge,
                color = Color.White.copy(alpha = 0.82f)
            )
        }
    }
}

@Composable
private fun BannerDecoration(
    modifier: Modifier = Modifier
) {
    Canvas(modifier = modifier) {
        val center = Offset(
            x = size.width * 0.82f,
            y = size.height * 0.5f
        )

        listOf(46.dp, 76.dp, 106.dp).forEach { radius ->
            drawCircle(
                color = Color.White.copy(alpha = 0.13f),
                radius = radius.toPx(),
                center = center,
                style = Stroke(width = 1.dp.toPx())
            )
        }

        drawCircle(
            color = Color.White.copy(alpha = 0.25f),
            radius = 4.dp.toPx(),
            center = Offset(
                x = size.width * 0.63f,
                y = size.height * 0.36f
            )
        )

        drawCircle(
            color = Color.White.copy(alpha = 0.25f),
            radius = 3.dp.toPx(),
            center = Offset(
                x = size.width * 0.67f,
                y = size.height * 0.64f
            )
        )
    }
}

@Composable
private fun QuickSettingCard(
    @DrawableRes iconResId: Int,
    title: String,
    count: Int,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .height(142.dp)
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(22.dp),
        color = MaterialTheme.colorScheme.surface,
        border = BorderStroke(
            1.dp,
            MaterialTheme.colorScheme.outlineVariant
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            CriteriaBadge(
                iconResId = iconResId,
                size = 44
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.Bottom
            ) {
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(1.dp)
                ) {
                    Text(
                        text = title,
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onSurface
                    )

                    Text(
                        text = "${count}개",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary
                    )
                }

                NavigationArrow()
            }
        }
    }
}

@Composable
private fun ExclusionSettingCard(
    exclusionKeywordCount: Int,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(20.dp),
        color = MaterialTheme.colorScheme.primaryContainer
            .copy(alpha = 0.72f),
        border = BorderStroke(
            1.dp,
            MaterialTheme.colorScheme.primary.copy(alpha = 0.16f)
        )
    ) {
        Row(
            modifier = Modifier.padding(
                horizontal = 16.dp,
                vertical = 15.dp
            ),
            verticalAlignment = Alignment.CenterVertically
        ) {
            CriteriaBadge(
                iconResId = R.drawable.ic_criteria_exclusion,
                backgroundColor = MaterialTheme.colorScheme.surface
            )

            Spacer(modifier = Modifier.width(14.dp))

            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(2.dp)
            ) {
                Text(
                    text = "앱별 제외 키워드",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.onSurface
                )

                Text(
                    text =
                        if (exclusionKeywordCount == 0) {
                            "광고처럼 넘기고 싶은 표현을 설정해보세요"
                        } else {
                            "${exclusionKeywordCount}개 제외 키워드가 설정되어 있어요"
                        },
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            NavigationArrow()
        }
    }
}

@Composable
private fun CollectionStatusItem(
    @DrawableRes iconResId: Int,
    title: String,
    status: String,
    isEnabled: Boolean,
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
        verticalAlignment = Alignment.CenterVertically
    ) {
        CriteriaBadge(
            iconResId = iconResId,
            size = 42
        )

        Spacer(modifier = Modifier.width(14.dp))

        Text(
            text = title,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurface
        )

        StatusLabel(
            text = status,
            isEnabled = isEnabled
        )
    }
}

@Composable
private fun StatusLabel(
    text: String,
    isEnabled: Boolean,
    modifier: Modifier = Modifier
) {
    val statusColor =
        if (isEnabled) {
            NotiSuccess
        } else {
            MaterialTheme.colorScheme.primary
        }

    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(7.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Surface(
            modifier = Modifier.size(18.dp),
            shape = CircleShape,
            color = Color.Transparent,
            border = BorderStroke(1.5.dp, statusColor)
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text(
                    text = if (isEnabled) "✓" else "!",
                    style = MaterialTheme.typography.labelSmall,
                    color = statusColor
                )
            }
        }

        Text(
            text = text,
            style = MaterialTheme.typography.labelLarge,
            color = statusColor
        )
    }
}

@Composable
private fun ServiceInformationItem(
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
        verticalAlignment = Alignment.CenterVertically
    ) {
        CriteriaBadge(
            iconResId = R.drawable.ic_criteria_privacy,
            size = 42
        )

        Spacer(modifier = Modifier.width(14.dp))

        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(2.dp)
        ) {
            Text(
                text = stringResource(
                    R.string.privacy_policy_title
                ),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface
            )

            Text(
                text = stringResource(
                    R.string.privacy_policy_description
                ),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }

        NavigationArrow()
    }
}

@Composable
private fun CriteriaBadge(
    @DrawableRes iconResId: Int,
    modifier: Modifier = Modifier,
    size: Int = 46,
    backgroundColor: Color =
        MaterialTheme.colorScheme.primaryContainer
) {
    Surface(
        modifier = modifier.size(size.dp),
        shape = CircleShape,
        color = backgroundColor
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(
                painter = painterResource(id = iconResId),
                contentDescription = null,
                modifier = Modifier.size(23.dp),
                tint = MaterialTheme.colorScheme.primary
            )
        }
    }
}

@Composable
private fun NavigationArrow(
    modifier: Modifier = Modifier
) {
    Text(
        text = "›",
        modifier = modifier,
        style = MaterialTheme.typography.headlineSmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant
    )
}

@Composable
private fun CriteriaSectionTitle(
    text: String,
    modifier: Modifier = Modifier
) {
    Text(
        text = text,
        modifier = modifier,
        style = MaterialTheme.typography.titleMedium,
        color = MaterialTheme.colorScheme.onBackground
    )
}

@Composable
private fun CriteriaMenuDivider() {
    HorizontalDivider(
        modifier = Modifier.padding(start = 72.dp),
        color = MaterialTheme.colorScheme.outlineVariant
    )
}
