package com.hanseo.noti.ui.onboarding

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
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
    onIntroCompleted: () -> Unit,
    modifier: Modifier = Modifier
) {
    val pages = OnboardingPages.items

    val pagerState = rememberPagerState(
        pageCount = { pages.size }
    )

    val coroutineScope = rememberCoroutineScope()

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(
                horizontal = 24.dp,
                vertical = 16.dp
            )
    ) {
        Text(
            text = "noti.",
            style = MaterialTheme.typography.headlineMedium
        )

        HorizontalPager(
            state = pagerState,
            modifier = Modifier.weight(1f)
        ) { pageIndex ->
            OnboardingPage(
                content = pages[pageIndex]
            )
        }

        OnboardingPageIndicator(
            currentPage = pagerState.currentPage,
            pageCount = pages.size,
            modifier = Modifier.align(
                Alignment.CenterHorizontally
            )
        )

        Spacer(modifier = Modifier.height(32.dp))

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
            modifier = Modifier
                .fillMaxWidth()
                .height(52.dp)
        ) {
            val currentPage =
                pages[pagerState.currentPage]

            Text(
                text = stringResource(
                    currentPage.buttonTextResId
                ),
                style = MaterialTheme.typography.labelLarge
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
            painter = painterResource(
                content.imageResId
            ),
            contentDescription = null
        )

        Spacer(modifier = Modifier.height(48.dp))

        Text(
            text = stringResource(
                content.titleResId
            ),
            style = MaterialTheme.typography.headlineMedium,
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(24.dp))

        Text(
            text = stringResource(
                content.descriptionResId
            ),
            style = MaterialTheme.typography.bodyMedium,
            color =
                MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center
        )
    }
}

@Composable
private fun OnboardingPageIndicator(
    currentPage: Int,
    pageCount: Int,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        repeat(pageCount) { pageIndex ->
            val isSelected =
                currentPage == pageIndex

            val indicatorWidth =
                if (isSelected) {
                    18.dp
                } else {
                    6.dp
                }

            val indicatorColor =
                if (isSelected) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.outlineVariant
                }

            Spacer(
                modifier = Modifier
                    .size(
                        width = indicatorWidth,
                        height = 6.dp
                    )
                    .background(
                        color = indicatorColor,
                        shape = RoundedCornerShape(
                            percent = 50
                        )
                    )
            )
        }
    }
}