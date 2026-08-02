package com.hanseo.noti.ui.navigation

import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp

@Composable
fun NotiBottomNavigation(
    currentRoute: String?,
    onTabSelected: (MainTab) -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(
            topStart = 28.dp,
            topEnd = 28.dp
        ),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 8.dp
    ) {
        NavigationBar(
            containerColor =
                MaterialTheme.colorScheme.surface
        ) {
            MainTab.entries.forEach { tab ->
                val selected =
                    currentRoute == tab.route

                NavigationBarItem(
                    selected = selected,
                    onClick = {
                        onTabSelected(tab)
                    },
                    icon = {
                        Icon(
                            painter = painterResource(
                                id = tab.iconResId
                            ),
                            contentDescription =
                                stringResource(
                                    id = tab.labelResId
                                ),
                            modifier = Modifier.size(26.dp)
                        )
                    },
                    label = {
                        Text(
                            text = stringResource(
                                id = tab.labelResId
                            ),
                            style =
                                MaterialTheme.typography.labelMedium
                        )
                    },
                    alwaysShowLabel = true,
                    colors =
                        NavigationBarItemDefaults.colors(
                            selectedIconColor =
                                MaterialTheme.colorScheme.primary,

                            selectedTextColor =
                                MaterialTheme.colorScheme.primary,

                            indicatorColor =
                                MaterialTheme.colorScheme.primaryContainer,

                            unselectedIconColor =
                                MaterialTheme.colorScheme.onSurfaceVariant,

                            unselectedTextColor =
                                MaterialTheme.colorScheme.onSurfaceVariant
                        )
                )
            }
        }
    }
}