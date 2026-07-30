package com.hanseo.noti.ui.home

import com.hanseo.noti.domain.model.ClassifiedNotification

data class HomeUiState(
    val importantNotification: List<ClassifiedNotification>
)

