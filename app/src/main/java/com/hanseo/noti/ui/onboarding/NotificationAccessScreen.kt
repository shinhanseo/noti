package com.hanseo.noti.ui.onboarding

import androidx.annotation.DrawableRes
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.hanseo.noti.R

@Composable
fun NotificationAccessScreen(
    onBackClick: () -> Unit,
    onRequestAccess: () -> Unit,
    onDefer: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp)
    ) {
        Box(
            modifier = modifier
                .fillMaxWidth()
                .height(56.dp)
        ) {
            TextButton(
                onClick = onBackClick,
                modifier = Modifier.align(Alignment.CenterStart)
            ) {
                Text(
                    text = stringResource(R.string.back)
                )
            }

            Text(
                text = stringResource(
                    R.string.notification_access_top_title
                ),
                style = MaterialTheme.typography.titleLarge,
                modifier = Modifier.align(Alignment.Center)
            )
        }

        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(40.dp))

            Image(
                painter = painterResource(
                    R.drawable.onboarding_access
                ),
                contentDescription = null
            )

            Spacer(modifier = Modifier.height(32.dp))

            Text(
                text = stringResource(
                    R.string.notification_access_title
                ),
                style = MaterialTheme.typography.headlineMedium,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = stringResource(
                    R.string.notification_access_description
                ),
                style = MaterialTheme.typography.bodyMedium,
                color =
                    MaterialTheme.colorScheme.tertiary,
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(32.dp))

            PermissionReason(
                title = stringResource(
                    R.string.notification_access_read_title
                ),
                description = stringResource(
                    R.string.notification_access_read_description
                ),
                iconResId = R.drawable.onboarding_plus
            )

            PermissionReason(
                title = stringResource(
                    R.string.notification_access_local_title
                ),
                description = stringResource(
                    R.string.notification_access_local_description
                ),
                iconResId = R.drawable.onboarding_secure
            )

            PermissionReason(
                title = stringResource(
                    R.string.notification_access_revoke_title
                ),
                description = stringResource(
                    R.string.notification_access_revoke_description
                ),
                iconResId = R.drawable.onboardindg_minus
            )
        }

        Button(
            onClick = onRequestAccess,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp)
        ) {
            Text(
                text = stringResource(
                    R.string.notification_access_allow
                ),
                style = MaterialTheme.typography.labelLarge
            )
        }

        TextButton(
            onClick = onDefer,
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp)
        ) {
            Text(
                text = stringResource(
                    R.string.notification_access_later
                ),
                style = MaterialTheme.typography.labelLarge
            )
        }
    }
}

@Composable
private fun PermissionReason(
    title: String,
    description: String,
    @DrawableRes iconResId: Int
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 10.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Image(
            painter = painterResource(iconResId),
            contentDescription = null,
            modifier = Modifier.size(40.dp)
        )

        Spacer(modifier = Modifier.width(6.dp))

        Column(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSurface
            )

            Text(
                text = description,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.tertiary
            )
        }
    }
}