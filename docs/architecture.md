# 아키텍처

> 이 문서는 MVP의 목표 구조다. 현재 저장소는 기본 Compose 프로젝트 상태이며 아래 구성은 순차적으로 구현한다.

## 기술 방향

- UI: Kotlin, Jetpack Compose, Material 3
- 알림 수집: Android `NotificationListenerService`
- 비동기 처리: Kotlin Coroutines, Flow
- 로컬 저장: Room
- 설정 저장: DataStore
- 의존성 주입: 초기에는 수동 주입, 구조가 커지면 Hilt 도입 검토
- 네트워크: MVP에서는 사용하지 않음

## 데이터 흐름

```text
시스템 알림
   ↓
NotificationListenerService
   ↓ 정규화 및 중복 확인
NotificationRepository
   ↓
ImportanceEngine
   ├─ 사용자 규칙
   ├─ 앱/발신자 신호
   ├─ 중요·제외 키워드
   └─ 알림 문맥 신호
   ↓
Room: 알림 + 점수 + 판정 이유
   ↓ Flow
ViewModel
   ↓
Compose 화면
   ↓ 사용자 피드백
FeedbackRepository → 사용자 규칙 갱신 → 재판정
```

## 권장 패키지 구조

```text
com.hanseo.noti
├── data
│   ├── local
│   ├── model
│   └── repository
├── notification
│   ├── NotiNotificationListenerService.kt
│   └── NotificationParser.kt
├── domain
│   ├── importance
│   └── model
├── ui
│   ├── onboarding
│   ├── home
│   ├── notifications
│   ├── settings
│   └── theme
└── MainActivity.kt
```

## 핵심 모델 초안

### NotificationItem

- 내부 ID
- Android 알림 키
- 패키지명과 표시용 앱 이름
- 제목, 본문, 발신자
- 수신 시각
- 원본 카테고리 및 진행 중 알림 여부
- 읽음/삭제 상태
- 중요도 점수와 등급
- 판정 이유 목록

### ImportanceReason

- 이유 유형: 중요 앱, 중요 발신자, 중요 키워드, 마감·일정, 업무 요청, 결제·배송 상태, 제외 규칙 등
- 점수 변화량
- 사용자에게 보여줄 설명
- 매칭된 규칙의 ID

### UserRule

- 규칙 유형: 앱, 발신자, 포함 키워드, 제외 키워드
- 대상 값
- 점수 변화량 또는 강제 분류
- 활성 여부
- 사용자 직접 설정인지 피드백으로 생성됐는지 여부

## NotificationListenerService 처리 원칙

- 서비스는 알림을 받는 즉시 UI 로직을 실행하지 않는다.
- `StatusBarNotification`에서 필요한 필드만 안전하게 추출해 저장 계층으로 전달한다.
- 같은 알림 키의 갱신은 새 알림을 무한히 추가하지 않고 기존 항목을 갱신한다.
- 진행률, 미디어, 포그라운드 서비스 등 반복 갱신이 잦은 알림은 별도 필터링한다.
- 앱 프로세스가 재생성돼도 Room의 기존 데이터로 화면을 복구한다.
- 사용자가 권한을 해제한 경우 상태를 감지하고 안내한다.

## 개인정보 및 보안

- 알림 제목과 본문은 민감정보로 취급한다.
- 로그에 실제 알림 본문을 출력하지 않는다.
- Android 백업을 통한 알림 데이터 유출 가능성을 검토하고, 필요한 경우 DB를 백업 제외 대상으로 설정한다.
- 앱 삭제 또는 설정 화면에서 수집 데이터를 지울 수 있어야 한다.
- 분석이나 오류 보고 도구를 도입할 때 알림 내용이 포함되지 않도록 별도 필터를 둔다.

## 테스트 전략

- `ImportanceEngine`: Android 의존성이 없는 순수 Kotlin 단위 테스트
- `NotificationParser`: 누락 필드, 긴 텍스트, 그룹 알림, 반복 갱신 테스트
- Room: 저장·수정·정렬·삭제 계측 테스트
- 권한 흐름: 미허용, 허용, 사용 중 해제 시나리오
- 실기기: 화면 꺼짐, 앱 백그라운드, 앱 태스크 제거, 재부팅 이후 수집 확인
