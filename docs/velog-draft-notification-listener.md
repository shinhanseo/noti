# [Android 알림, 제대로 이해하기 01] 앱 화면이 없어도 알림을 어떻게 받을까?

## 개요

`noti.`라는 Android 애플리케이션을 만들고 있다.

`noti.`는 기기에 쌓이는 알림 중 사용자가 지금 확인해야 할 알림을 찾고, 왜 중요하다고 판단했는지 설명하는 앱이다.

이 기능을 만들려면 가장 먼저 다른 앱에서 도착한 알림을 가져와야 한다.

처음에는 다음과 같이 생각할 수 있다.

> 앱이 실행 중일 때 알림 목록을 읽어 오면 되지 않을까?

하지만 알림은 사용자가 `noti.`를 보고 있을 때만 도착하지 않는다.
화면이 꺼져 있거나 다른 앱을 사용하고 있을 때도 도착하고, `noti.`의 `Activity`가 화면에 없어도 수집되어야 한다.

그렇다면 Android 앱은 자신의 화면이 떠 있지 않을 때 다른 앱의 알림을 어떻게 전달받을 수 있을까?

이번 글에서는 `NotificationListenerService`로 알림을 전달받고, Android의 알림 객체를 앱에서 사용할 모델로 변환한 뒤, 저장할 필요가 없는 알림을 걸러 내기까지의 흐름을 정리해 보려고 한다.

## Activity에서 알림을 읽으면 안 될까?

`Activity`는 사용자에게 화면을 보여 주는 컴포넌트다.

따라서 `Activity`의 생명주기에 알림 수집을 연결하면 화면이 열려 있는 동안에는 동작할 수 있지만, 화면이 사라진 뒤에도 계속 알림을 받는 구조를 만들기 어렵다.

알림 수집은 화면의 수명과 다른 수명을 가져야 한다.

`noti.`의 화면이 현재 보이는지와 관계없이 Android 시스템이 새 알림을 게시했을 때 이를 전달받아야 한다.

Android는 이런 동작을 위해 `NotificationListenerService`를 제공한다.

`NotificationListenerService`는 새로운 알림이 게시되거나 제거되는 등의 변화를 Android 시스템으로부터 전달받는 서비스다.

여기서 중요한 점은 앱이 임의로 다른 앱의 알림을 읽는 것이 아니라는 것이다.

사용자가 Android 설정에서 알림 접근 권한을 허용하면 시스템이 서비스를 연결하고, 이후 알림 이벤트를 콜백으로 전달한다.

## NotificationListenerService 등록하기

먼저 `NotificationListenerService`를 상속한 서비스를 만든다.

```kotlin
class NotiNotificationListenerService :
    NotificationListenerService() {

    override fun onListenerConnected() {
        super.onListenerConnected()

        Log.d(TAG, "Notification listener connected")
    }

    override fun onNotificationPosted(
        sbn: StatusBarNotification?
    ) {
        if (sbn == null) return
    }

    companion object {
        private const val TAG = "NotiListener"
    }
}
```

`onListenerConnected()`는 알림 리스너가 시스템의 알림 관리자와 연결되었을 때 호출된다.

새 알림이 게시되면 `onNotificationPosted()`가 호출되고, 전달된 `StatusBarNotification`을 통해 알림을 게시한 앱과 실제 `Notification` 객체에 접근할 수 있다.

서비스를 만들기만 해서는 시스템이 이 컴포넌트의 역할을 알 수 없다.
따라서 `AndroidManifest.xml`에도 서비스를 선언해야 한다.

```xml
<service
    android:name=".notification.NotiNotificationListenerService"
    android:exported="false"
    android:label="@string/app_name"
    android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE">

    <intent-filter>
        <action android:name=
            "android.service.notification.NotificationListenerService" />
    </intent-filter>
</service>
```

`BIND_NOTIFICATION_LISTENER_SERVICE` 권한과 `intent-filter`를 선언하면 Android 시스템이 이 서비스를 알림 리스너로 인식할 수 있다.

다만 Manifest 등록만으로 알림 내용에 접근할 수 있는 것은 아니다.
알림에는 메시지, 인증 번호, 결제 내역처럼 민감한 정보가 포함될 수 있기 때문에 사용자가 시스템 설정에서 직접 접근을 허용해야 한다.

즉 전체 흐름은 다음과 같다.

```text
사용자가 알림 접근을 허용한다
        ↓
Android 시스템이 ListenerService를 연결한다
        ↓
다른 앱이 알림을 게시한다
        ↓
onNotificationPosted()가 호출된다
```

## StatusBarNotification을 그대로 사용하면 안 될까?

`onNotificationPosted()`가 전달하는 값은 `StatusBarNotification`이다.

여기에는 알림의 고유 키, 알림을 게시한 패키지명, 게시 시각과 실제 `Notification` 객체 등이 들어 있다.

기술적으로는 이 객체를 서비스 안에서 바로 읽고 처리할 수 있다.

```kotlin
override fun onNotificationPosted(
    sbn: StatusBarNotification?
) {
    if (sbn == null) return

    val title = sbn.notification.extras
        .getCharSequence(Notification.EXTRA_TITLE)
        ?.toString()
}
```

하지만 이렇게 구현하면 서비스가 다음 책임을 모두 가지게 된다.

- Android 콜백 처리
- 알림 데이터 추출
- 저장할 알림과 무시할 알림 판단
- 이후 추가될 저장 및 중요도 판정

코드가 적을 때는 문제가 없어 보이지만 기능이 추가될수록 서비스가 Android 객체의 세부 구조와 앱의 정책을 모두 알아야 한다.

그래서 `StatusBarNotification`에서 필요한 값만 추출해 앱 내부 모델로 변환하는 책임을 `NotificationParser`로 분리했다.

## Android 알림을 앱의 모델로 변환하기

현재 `noti.`에서 사용하는 알림 모델은 다음과 같다.

```kotlin
data class NotificationItem(
    val key: String,
    val packageName: String,
    val title: String?,
    val body: String?,
    val postedAt: Long,
    val category: String?,
    val isOngoing: Boolean,
    val isGroupSummary: Boolean
)
```

이 모델은 Android 알림의 모든 값을 복사하지 않는다.

알림을 구분하고, 화면에 표시하고, 이후 중요도를 판단하는 데 필요한 값만 가진다.

변환은 `NotificationParser`가 담당한다.

```kotlin
object NotificationParser {

    fun parse(sbn: StatusBarNotification): NotificationItem {
        val notification = sbn.notification
        val extras = notification.extras

        val title = extras
            .getCharSequence(Notification.EXTRA_TITLE)
            ?.toString()

        val body = (
            extras.getCharSequence(Notification.EXTRA_BIG_TEXT)
                ?: extras.getCharSequence(Notification.EXTRA_TEXT)
        )?.toString()

        return NotificationItem(
            key = sbn.key,
            packageName = sbn.packageName,
            title = title,
            body = body,
            postedAt = sbn.postTime,
            category = notification.category,
            isOngoing = sbn.isOngoing,
            isGroupSummary =
                notification.flags and
                    Notification.FLAG_GROUP_SUMMARY != 0
        )
    }
}
```

제목은 `Notification.EXTRA_TITLE`에서 가져온다.

본문은 먼저 `Notification.EXTRA_BIG_TEXT`를 확인하고, 값이 없으면 `Notification.EXTRA_TEXT`를 사용한다.

`BigTextStyle`을 사용한 알림은 펼쳤을 때 보이는 긴 본문이 `EXTRA_BIG_TEXT`에 들어갈 수 있다.
따라서 `EXTRA_TEXT`만 읽으면 화면에서는 보였던 내용의 일부만 가져올 수 있다.

```kotlin
val body = (
    extras.getCharSequence(Notification.EXTRA_BIG_TEXT)
        ?: extras.getCharSequence(Notification.EXTRA_TEXT)
)?.toString()
```

이 코드는 “긴 본문이 있으면 긴 본문을 사용하고, 없으면 일반 본문을 사용한다”는 우선순위를 표현한다.

파싱을 별도 객체로 분리하면서 서비스는 알림이 어떤 `extras` 키를 사용하는지 알 필요가 없어졌다.

```kotlin
val notificationItem = NotificationParser.parse(sbn)
```

이제 서비스는 Android의 알림을 `NotificationItem`으로 바꾸어 달라고 요청하기만 한다.

## 전달받은 알림을 모두 저장해야 할까?

`onNotificationPosted()`가 호출되었다고 해서 모든 알림이 `noti.`에 필요한 것은 아니다.

먼저 `noti.`가 게시한 알림을 다시 수집하면 자기 자신의 알림이 입력으로 돌아오는 흐름이 생길 수 있다.

```kotlin
if (sbn.packageName == packageName) return
```

그래서 현재 앱과 알림을 게시한 앱의 패키지명이 같으면 바로 종료한다.

파싱한 뒤에는 두 종류의 알림을 추가로 제외한다.

```kotlin
enum class NotificationIgnoreReason {
    EMPTY_CONTENT,
    GROUP_SUMMARY,
}

object NotificationFilter {
    fun findIgnoreReason(
        item: NotificationItem
    ): NotificationIgnoreReason? {
        return when {
            item.isGroupSummary ->
                NotificationIgnoreReason.GROUP_SUMMARY

            item.title.isNullOrBlank() &&
                item.body.isNullOrBlank() ->
                NotificationIgnoreReason.EMPTY_CONTENT

            else -> null
        }
    }
}
```

### 내용이 없는 알림

제목과 본문이 모두 없다면 현재 단계에서는 중요도를 판단하거나 사용자에게 의미 있는 내용을 보여 주기 어렵다.

따라서 `EMPTY_CONTENT`로 분류한다.

### 그룹 요약 알림

Android는 여러 알림을 하나의 그룹으로 보여 주기 위해 별도의 그룹 요약 알림을 사용할 수 있다.

예를 들어 개별 메시지 알림이 여러 개 있고, 이를 묶어 “새 메시지 3개”와 같은 요약 알림을 함께 게시할 수 있다.

개별 알림과 요약 알림을 모두 저장하면 같은 사건이 중복되어 보일 수 있다.

현재 `noti.`는 `FLAG_GROUP_SUMMARY`가 설정된 알림을 `GROUP_SUMMARY`로 분류해 제외한다.

여기서 `Boolean`만 반환하지 않고 제외 이유를 반환하도록 만들었다.

```kotlin
val ignoreReason =
    NotificationFilter.findIgnoreReason(notificationItem)

if (ignoreReason != null) {
    Log.d(
        TAG,
        "Notification ignored: reason=$ignoreReason"
    )
    return
}
```

단순히 `true` 또는 `false`를 반환하면 알림이 제외되었다는 사실만 알 수 있다.

반면 이유를 값으로 표현하면 어떤 정책 때문에 제외되었는지 확인할 수 있고, 이후 테스트에서도 기대한 이유를 검증할 수 있다.

필터 규칙이 늘어나더라도 서비스에는 새로운 조건문을 계속 추가하지 않아도 된다.

## 실제 알림 내용은 로그로 남기지 않는다

알림 수집 기능을 개발할 때는 어떤 값이 들어왔는지 확인하고 싶어진다.

```kotlin
Log.d(TAG, "title=${notificationItem.title}")
Log.d(TAG, "body=${notificationItem.body}")
```

하지만 알림 제목과 본문에는 개인정보가 포함될 수 있다.

그래서 현재 구현에서는 실제 내용을 출력하지 않고 값의 존재 여부와 민감하지 않은 상태만 기록한다.

```kotlin
Log.d(
    TAG,
    "Notification accepted: " +
        "titlePresent=${notificationItem.title != null}, " +
        "bodyPresent=${notificationItem.body != null}, " +
        "ongoing=${notificationItem.isOngoing}"
)
```

디버그 로그도 데이터가 이동하는 또 하나의 경로다.

로컬에서만 알림을 처리하는 앱을 만들더라도, 로그에 원문을 남긴다면 “알림 데이터가 기기 안에만 있다”는 원칙이 흐려질 수 있다.

## 현재 알림 수집 흐름

현재까지 구현한 흐름을 정리하면 다음과 같다.

```text
Android 시스템
    ↓ onNotificationPosted()
NotiNotificationListenerService
    ↓ 자기 앱 알림 제외
NotificationParser
    ↓ StatusBarNotification → NotificationItem
NotificationFilter
    ↓ 빈 내용·그룹 요약 제외
수집 가능한 알림
```

`NotificationListenerService`는 시스템과 연결되는 입구만 담당한다.

`NotificationParser`는 Android 객체를 앱의 모델로 바꾸고, `NotificationFilter`는 현재 정책에서 저장할 필요가 없는 알림을 판단한다.

이렇게 책임을 나누면 이후 Room 저장이나 중요도 판정이 추가되어도 서비스가 모든 세부 구현을 직접 가지지 않아도 된다.

## 앱 화면이 없으면 항상 알림을 받을 수 있을까?

`NotificationListenerService`를 사용하면 알림 수집을 `Activity`의 생명주기에서 분리할 수 있다.

그렇다고 “어떤 상황에서도 반드시 모든 알림을 받는다”고 단정할 수는 없다.

사용자가 알림 접근 권한을 해제할 수 있고, 시스템과 리스너의 연결이 끊길 수도 있다.
앱을 강제 종료한 상황과 최근 앱 화면에서 태스크만 제거한 상황도 구분해서 확인해야 한다.

따라서 다음 시나리오는 실제 기기에서 별도로 검증할 필요가 있다.

- 앱 화면이 다른 앱 뒤에 있는 상태
- 앱 태스크를 최근 앱 화면에서 제거한 상태
- 화면이 꺼진 상태
- 알림 접근 권한을 해제한 상태
- 기기를 재부팅한 이후

서비스를 사용했다는 사실 자체보다, 시스템이 관리하는 컴포넌트의 수명과 권한 상태를 이해하고 실제 기기에서 확인하는 것이 중요하다.

## 마무리

다른 앱의 알림을 수집하려면 화면을 담당하는 `Activity`가 아니라 Android 시스템과 연결되는 `NotificationListenerService`가 필요하다.

하지만 콜백을 받는 것만으로 알림 수집이 끝나는 것은 아니다.

Android의 `StatusBarNotification`을 앱에서 사용할 모델로 바꾸고, 긴 본문과 일반 본문의 차이를 처리하고, 그룹 요약이나 내용이 없는 알림을 구분해야 한다.

현재 `noti.`에서는 이 책임을 다음과 같이 나누었다.

- `NotiNotificationListenerService`: 시스템 콜백 처리
- `NotificationParser`: Android 알림을 앱 모델로 변환
- `NotificationFilter`: 저장하지 않을 알림과 이유 판단

그러면 다음 질문이 남는다.

> 같은 알림이 내용만 바뀌어 다시 게시되면 새로운 알림으로 저장해야 할까?

다음 글에서는 `StatusBarNotification.key`를 기준으로 알림의 신규 게시와 갱신을 어떻게 구분할지, 그리고 수집한 알림을 Room에 저장할 때 어떤 구조가 필요한지 정리해 보려고 한다.

## 참고 자료

- [Android Developers: NotificationListenerService](https://developer.android.com/reference/kotlin/android/service/notification/NotificationListenerService)
- [Android Developers: Notification](https://developer.android.com/reference/android/app/Notification)
- [Android Developers: Create a group of notifications](https://developer.android.com/develop/ui/views/notifications/group)
