package com.hanseo.noti.ui.navigation

import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import com.hanseo.noti.R

enum class MainTab(
    val route: String,

    @param:StringRes
    val labelResId: Int,

    @param:DrawableRes
    val iconResId: Int
) {
    HOME(
        route = NotiRoutes.HOME,
        labelResId = R.string.bottom_tab_home,
        iconResId = R.drawable.ic_nav_home
    ),

    NOTIFICATIONS(
        route = NotiRoutes.NOTIFICATIONS,
        labelResId =
            R.string.bottom_tab_notifications,
        iconResId =
            R.drawable.ic_nav_notifications
    ),

    MY_CRITERIA(
        route = NotiRoutes.MY_CRITERIA,
        labelResId =
            R.string.bottom_tab_my_criteria,
        iconResId =
            R.drawable.ic_nav_my_criteria
    )
}