package com.hanseo.noti.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColorScheme = lightColorScheme(
    primary = NotiBlue,
    onPrimary = NotiSurface,
    primaryContainer = NotiBlueContainer,
    onPrimaryContainer = NotiBlueStrong,
    secondary = NotiBlueStrong,
    onSecondary = NotiSurface,
    secondaryContainer = NotiSurfaceVariant,
    onSecondaryContainer = NotiTextPrimary,
    tertiary = NotiTextSecondary,
    onTertiary = NotiSurface,
    tertiaryContainer = NotiSurfaceVariant,
    onTertiaryContainer = NotiTextPrimary,
    background = NotiBackground,
    onBackground = NotiTextPrimary,
    surface = NotiSurface,
    onSurface = NotiTextPrimary,
    surfaceVariant = NotiSurfaceVariant,
    onSurfaceVariant = NotiTextSecondary,
    outline = NotiOutline,
    outlineVariant = NotiDivider
)

@Composable
fun NotiTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = LightColorScheme,
        typography = Typography,
        content = content
    )
}
