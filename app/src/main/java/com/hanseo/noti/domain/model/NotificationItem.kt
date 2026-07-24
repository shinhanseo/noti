package com.hanseo.noti.domain.model

data class NotificationItem(
    val key: String, // 알림 고유 key
    val packageName: String, // 알림 보낸 앱의 패키지명
    val title: String?, // 제목
    val body: String?, // 본문
    val postedAt: Long, // 시각
    val category: String?, // 메시지, 전화, 일정 등 Android가 지정한 알림 종류
    val isOngoing: Boolean, // 다운로드 음악 재생처럼 계속 유지되는 알람인지 여부
    val isGroupSummary: Boolean // 여러 알림을 묶어 보여주는 대표 알림인지 여부
)

