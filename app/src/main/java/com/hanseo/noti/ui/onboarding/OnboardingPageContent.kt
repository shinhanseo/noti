package com.hanseo.noti.ui.onboarding

import androidx.annotation.DrawableRes
import androidx.annotation.StringRes

data class OnboardingPageContent(
    @param:DrawableRes
    val imageResId: Int,

    @param:StringRes
    val titleResId: Int,

    @param:StringRes
    val descriptionResId: Int,

    @param:StringRes
    val buttonTextResId: Int
)