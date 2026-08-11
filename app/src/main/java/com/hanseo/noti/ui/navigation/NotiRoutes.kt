package com.hanseo.noti.ui.navigation

object NotiRoutes {

    // 바텀 탭이 없는 최상위 화면
    const val ONBOARDING = "onboarding"
    const val MAIN = "main"

    // MainScreen 내부 바텀 탭 화면
    const val HOME = "home"
    const val NOTIFICATIONS = "notifications"
    const val MY_CRITERIA = "my_criteria"

    // 내 기준에서 진입하는 세부 설정 화면
    const val IMPORTANT_APPS_SETTINGS =
        "important_apps_settings"
    const val IMPORTANT_KEYWORDS_SETTINGS =
        "important_keywords_settings"
    const val EXCLUSION_KEYWORDS_SETTINGS =
        "exclusion_keywords_settings"
}
