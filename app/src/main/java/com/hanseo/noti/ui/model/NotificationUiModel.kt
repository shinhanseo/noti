package com.hanseo.noti.ui.model

import android.graphics.Bitmap
import com.hanseo.noti.domain.model.ClassifiedNotification

data class NotificationUiModel(
    val classifiedNotification: ClassifiedNotification,
    val appName: String,
    val appIcon: Bitmap?
)
