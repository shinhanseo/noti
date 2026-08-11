package com.hanseo.noti.ui.criteria

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.hanseo.noti.data.apps.InstalledApp

@Composable
internal fun CriteriaSettingsTopBar(
    title: String,
    onBackClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        TextButton(
            onClick = onBackClick,
            modifier = Modifier.size(48.dp),
            contentPadding = PaddingValues(12.dp)
        ) {
            CriteriaBackArrowIcon()
        }

        Spacer(modifier = Modifier.width(4.dp))

        Text(
            text = title,
            modifier = Modifier.weight(1f),
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.onBackground,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )
    }
}

@Composable
internal fun CriteriaAppIcon(
    app: InstalledApp,
    modifier: Modifier = Modifier
) {
    val icon = app.icon

    if (icon != null) {
        Image(
            bitmap = icon.asImageBitmap(),
            contentDescription = "${app.displayName} 앱 아이콘",
            modifier = modifier
                .size(46.dp)
                .background(
                    color = MaterialTheme.colorScheme.surface,
                    shape = RoundedCornerShape(13.dp)
                )
                .padding(3.dp),
            contentScale = ContentScale.Fit
        )
    } else {
        Box(
            modifier = modifier
                .size(46.dp)
                .background(
                    color =
                        MaterialTheme.colorScheme.surfaceVariant,
                    shape = RoundedCornerShape(13.dp)
                ),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = app.displayName
                    .firstOrNull()
                    ?.uppercase()
                    ?: "?",
                style = MaterialTheme.typography.titleMedium,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
internal fun CriteriaSelectionIndicator(
    selected: Boolean,
    modifier: Modifier = Modifier
) {
    val backgroundColor =
        if (selected) {
            MaterialTheme.colorScheme.primary
        } else {
            MaterialTheme.colorScheme.background
        }

    val borderColor =
        if (selected) {
            MaterialTheme.colorScheme.primary
        } else {
            MaterialTheme.colorScheme.outline
        }

    Box(
        modifier = modifier
            .size(28.dp)
            .background(
                color = backgroundColor,
                shape = CircleShape
            )
            .border(
                width = 2.dp,
                color = borderColor,
                shape = CircleShape
            ),
        contentAlignment = Alignment.Center
    ) {
        if (selected) {
            Text(
                text = "✓",
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onPrimary
            )
        }
    }
}

@Composable
internal fun CriteriaKeywordInput(
    value: String,
    placeholder: String,
    onValueChanged: (String) -> Unit,
    onAddClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val canAdd = value.isNotBlank()

    OutlinedTextField(
        value = value,
        onValueChange = onValueChanged,
        modifier = modifier.fillMaxWidth(),
        placeholder = {
            Text(
                text = placeholder,
                style = MaterialTheme.typography.bodyLarge
            )
        },
        leadingIcon = {
            Box(
                modifier = Modifier
                    .size(34.dp)
                    .background(
                        color =
                            MaterialTheme.colorScheme.primaryContainer,
                        shape = CircleShape
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "+",
                    style = MaterialTheme.typography.headlineSmall,
                    color = MaterialTheme.colorScheme.primary
                )
            }
        },
        trailingIcon = {
            TextButton(
                onClick = onAddClick,
                enabled = canAdd
            ) {
                Text(
                    text = "추가",
                    style = MaterialTheme.typography.labelLarge
                )
            }
        },
        singleLine = true,
        shape = RoundedCornerShape(18.dp),
        textStyle = MaterialTheme.typography.bodyLarge,
        keyboardOptions = KeyboardOptions(
            imeAction = ImeAction.Done
        ),
        keyboardActions = KeyboardActions(
            onDone = {
                if (canAdd) {
                    onAddClick()
                }
            }
        ),
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
}

@Composable
internal fun CriteriaKeywordChip(
    keyword: String,
    onRemoveClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        onClick = onRemoveClick,
        modifier = modifier,
        shape = CircleShape,
        color = MaterialTheme.colorScheme.surface,
        contentColor = MaterialTheme.colorScheme.onSurface,
        border = BorderStroke(
            width = 1.dp,
            color = MaterialTheme.colorScheme.outlineVariant
        )
    ) {
        Row(
            modifier = Modifier.padding(
                horizontal = 15.dp,
                vertical = 9.dp
            ),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = keyword,
                style = MaterialTheme.typography.bodyMedium
            )

            Spacer(modifier = Modifier.width(9.dp))

            Text(
                text = "×",
                style = MaterialTheme.typography.titleMedium,
                color =
                    MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
internal fun CriteriaSaveError(
    visible: Boolean,
    modifier: Modifier = Modifier
) {
    if (visible) {
        Text(
            text = "설정을 저장하지 못했어요. 다시 시도해주세요.",
            modifier = modifier.fillMaxWidth(),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.error
        )
    }
}

@Composable
private fun CriteriaBackArrowIcon() {
    val color = MaterialTheme.colorScheme.onBackground

    Canvas(modifier = Modifier.size(24.dp)) {
        val strokeWidth = 2.dp.toPx()

        drawLine(
            color = color,
            start = Offset(
                x = size.width * 0.68f,
                y = size.height * 0.16f
            ),
            end = Offset(
                x = size.width * 0.32f,
                y = size.height * 0.5f
            ),
            strokeWidth = strokeWidth,
            cap = StrokeCap.Round
        )

        drawLine(
            color = color,
            start = Offset(
                x = size.width * 0.32f,
                y = size.height * 0.5f
            ),
            end = Offset(
                x = size.width * 0.68f,
                y = size.height * 0.84f
            ),
            strokeWidth = strokeWidth,
            cap = StrokeCap.Round
        )
    }
}
