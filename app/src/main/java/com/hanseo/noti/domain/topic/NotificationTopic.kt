package com.hanseo.noti.domain.topic

enum class NotificationTopic {
    FINANCE_SECURITY, // 결제, 송금, 계정, 인증, 로그인, 보안
    ACTION_REQUEST, // 확인, 승인, 회신, 제출같은 행동이 필요한 알림
    DELIVERY, // 배송 출발, 도착, 지연, 반송
    RESERVATION, // 예약, 예매, 진료 예약 상태
    SCHEDULE, // 일정, 회의, 마감, 리마인더
    PROMOTIONAL, // 광고, 할인, 쿠폰, 이벤트
    INFORMATIONAL, // 단순 정보, 상태 안내, 완료 알림
    COMMUNICATION, // 메시지, 이메일
    CALL_ALARM, // 전화, 알람
    UNKNOWN
}