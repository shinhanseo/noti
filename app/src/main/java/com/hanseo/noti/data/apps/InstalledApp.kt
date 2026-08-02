package com.hanseo.noti.data.apps

import android.graphics.Bitmap

data class InstalledApp (
    val packageName: String,
    val displayName: String,
    val icon: Bitmap?
)
