package com.hanseo.noti.ui.home

import android.graphics.Bitmap
import com.hanseo.noti.domain.model.ClassifiedNotification

data class HomeNotificationUiModel(
    val classifiedNotification: ClassifiedNotification,
    val appName: String,
    val appIcon: Bitmap?
)