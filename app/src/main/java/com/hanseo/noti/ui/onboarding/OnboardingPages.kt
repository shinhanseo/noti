package com.hanseo.noti.ui.onboarding

import com.hanseo.noti.R

object OnboardingPages {

    val items: List<OnboardingPageContent> = listOf(
        OnboardingPageContent(
            imageResId = R.drawable.onboarding_priority,
            titleResId = R.string.onboarding_priority_title,
            descriptionResId =
                R.string.onboarding_priority_description,
            buttonTextResId = R.string.onboarding_next
        ),
        OnboardingPageContent(
            imageResId = R.drawable.onboarding_privacy,
            titleResId = R.string.onboarding_privacy_title,
            descriptionResId =
                R.string.onboarding_privacy_description,
            buttonTextResId = R.string.onboarding_next
        ),
        OnboardingPageContent(
            imageResId = R.drawable.onboarding_personalization,
            titleResId =
                R.string.onboarding_personalization_title,
            descriptionResId =
                R.string.onboarding_personalization_description,
            buttonTextResId = R.string.onboarding_start
        )
    )
}