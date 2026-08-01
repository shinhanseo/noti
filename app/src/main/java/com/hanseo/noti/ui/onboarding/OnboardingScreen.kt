package com.hanseo.noti.ui.onboarding

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.material3.Button
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

@Composable
fun OnboardingScreen(
    onIntroCompleted: () -> Unit
) {
    val pages = OnboardingPages.items

    val pagerState = rememberPagerState(
        pageCount = { pages.size }
    )

    val coroutineScope = rememberCoroutineScope()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp)
    ) {
        HorizontalPager(
            state = pagerState,
            modifier = Modifier.weight(1f)
        ) { pageIndex ->
            OnboardingPage(
                content = pages[pageIndex]
            )
        }

        Button(
            onClick = {
                val isLastPage =
                    pagerState.currentPage == pages.lastIndex

                if (isLastPage) {
                    onIntroCompleted()
                } else {
                    coroutineScope.launch {
                        pagerState.animateScrollToPage(
                            pagerState.currentPage + 1
                        )
                    }
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            val currentPage = pages[pagerState.currentPage]

            Text(
                text = stringResource(
                    currentPage.buttonTextResId
                )
            )
        }
    }
}

@Composable
private fun OnboardingPage(
    content: OnboardingPageContent
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(horizontal = 16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Image(
            painter = painterResource(content.imageResId),
            contentDescription = null
        )

        Spacer(modifier = Modifier.height(48.dp))

        Text(
            text = stringResource(content.titleResId),
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = stringResource(content.descriptionResId),
            textAlign = TextAlign.Center
        )
    }
}