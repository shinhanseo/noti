# [Android 알림, 제대로 이해하기 02] 같은 알림이 다시 오면 새로 저장해야 할까?

## 개요

지난 글에서는 `NotificationListenerService`를 이용해 Android 시스템으로부터 알림을 전달받는 과정을 살펴봤다.

`StatusBarNotification`을 앱에서 사용할 `NotificationItem`으로 변환하고, 내용이 없거나 그룹을 대표하는 알림은 저장 대상에서 제외했다.

하지만 아직 수집한 알림은 로그에서만 확인할 수 있었다.

```kotlin
Log.d(TAG, "Notification accepted")
```

로그는 알림이 정상적으로 수신되었는지 확인하기에는 충분하다.
하지만 앱 프로세스가 종료되면 이전 알림을 다시 가져올 수 없고, 사용자가 나중에 앱을 열었을 때 지금까지 수집한 알림을 보여 줄 수도 없다.

그래서 수집한 알림을 기기 안에 저장하기 위해 Room을 연결했다.

처음에는 새 알림이 도착하면 `INSERT`하고, 알림 목록에서 사라지면 `DELETE`하면 된다고 생각할 수 있다.

그런데 Android 알림은 한 번 생성되고 끝나는 데이터가 아니다.

같은 알림이 내용만 바뀌어 다시 게시될 수 있고, 사용자가 알림을 지우거나 게시한 앱이 알림을 제거할 수도 있다.

그렇다면 같은 알림이 다시 도착했을 때 새로운 데이터로 저장해야 할까?
알림 목록에서 사라진 데이터는 Room에서도 바로 삭제해야 할까?

이번 글에서는 Room으로 알림을 저장하면서 알림의 생성, 갱신, 제거 상태를 어떻게 표현했는지 정리해 보려고 한다.

## 왜 Room을 사용했을까?

알림은 다음과 같은 구조를 가진다.

- 알림을 게시한 앱
- 제목과 본문
- 수신 시각
- 알림 카테고리
- 현재 유지 중인지 여부
- 시스템 알림 목록에서 제거되었는지 여부

여러 필드를 가진 알림을 저장하고, 수신 시각을 기준으로 정렬하거나 제거 여부에 따라 조회하려면 구조화된 로컬 저장소가 필요하다.

Room은 SQLite 위에 추상화 계층을 제공하는 Android Jetpack 라이브러리다.

SQLite를 직접 다룰 수도 있지만 Room을 사용하면 Entity로 테이블 구조를 정의하고, DAO에 작성한 SQL을 컴파일 시점에 확인할 수 있다.

Room의 기본 구성 요소는 다음 세 가지다.

```text
Entity
데이터베이스의 테이블과 행을 표현한다

DAO
데이터를 저장하고 조회하고 수정하는 방법을 정의한다

RoomDatabase
Entity와 DAO를 연결하고 데이터베이스의 진입점을 제공한다
```

먼저 알림을 저장할 Entity부터 만들었다.

## NotificationItem을 그대로 저장하면 안 될까?

앱 내부에서는 다음과 같은 `NotificationItem`을 사용하고 있다.

```kotlin
data class NotificationItem(
    val key: String,
    val packageName: String,
    val title: String?,
    val body: String?,
    val postedAt: Long,
    val category: String?,
    val isOngoing: Boolean,
    val isGroupSummary: Boolean,
    val isRemoved: Boolean = false,
    val removedAt: Long? = null
)
```

여기에 `@Entity`를 바로 붙여 Room에 저장할 수도 있다.

하지만 `NotificationItem`은 앱의 기능에서 사용하는 도메인 모델이고, Entity는 데이터베이스 스키마를 표현하는 모델이다.

둘을 하나로 사용하면 다음 변화가 서로 직접 영향을 주게 된다.

- 화면과 중요도 판정에 필요한 필드가 추가되면 DB 스키마도 바뀐다.
- 컬럼 이름이나 기본값 같은 저장 규칙이 도메인 모델에 들어온다.
- 데이터베이스 구조를 변경하면 앱 전체에서 사용하는 모델도 수정해야 한다.

두 모델은 현재 비슷해 보이지만 변경되는 이유가 다르다.

그래서 Room에 저장할 구조를 `NotificationEntity`로 분리했다.

```kotlin
@Entity(tableName = "notifications")
data class NotificationEntity(
    @PrimaryKey
    @ColumnInfo(name = "notification_key")
    val notificationKey: String,

    @ColumnInfo(name = "package_name")
    val packageName: String,

    val title: String?,
    val body: String?,

    @ColumnInfo(name = "posted_at")
    val postedAt: Long,

    val category: String?,

    @ColumnInfo(name = "is_ongoing")
    val isOngoing: Boolean,

    @ColumnInfo(
        name = "is_removed",
        defaultValue = "0"
    )
    val isRemoved: Boolean = false,

    @ColumnInfo(
        name = "removed_at",
        defaultValue = "NULL"
    )
    val removedAt: Long? = null
)
```

`NotificationItem`에는 `isGroupSummary`가 있지만 Entity에는 없다.

그룹 요약 알림은 `NotificationFilter`에서 저장 전에 제외하기 때문에 데이터베이스에 도달한 알림은 그룹 요약이 아니라는 전제가 생긴다.

반대로 `isRemoved`와 `removedAt`은 알림이 저장된 이후의 상태를 기록하기 위해 Entity에도 포함했다.

도메인 모델과 Entity 사이의 변환은 Mapper가 담당한다.

```kotlin
fun NotificationItem.toEntity(): NotificationEntity {
    return NotificationEntity(
        notificationKey = key,
        packageName = packageName,
        title = title,
        body = body,
        postedAt = postedAt,
        category = category,
        isOngoing = isOngoing,
        isRemoved = isRemoved,
        removedAt = removedAt
    )
}

fun NotificationEntity.toDomain(): NotificationItem {
    return NotificationItem(
        key = notificationKey,
        packageName = packageName,
        title = title,
        body = body,
        postedAt = postedAt,
        category = category,
        isOngoing = isOngoing,
        isGroupSummary = false,
        isRemoved = isRemoved,
        removedAt = removedAt
    )
}
```

이제 데이터베이스 컬럼 이름과 앱 내부의 프로퍼티 이름이 달라도 변환 지점을 한곳에서 관리할 수 있다.

## 알림의 Primary Key는 무엇이어야 할까?

Room의 모든 Entity에는 각 행을 고유하게 구분할 Primary Key가 필요하다.

처음 떠올릴 수 있는 방법은 자동으로 증가하는 숫자 ID를 만드는 것이다.

```kotlin
@PrimaryKey(autoGenerate = true)
val id: Long = 0
```

하지만 이 값을 사용하면 같은 Android 알림이 다시 게시되었는지 판단하기 어렵다.

예를 들어 다운로드 진행률 알림은 같은 알림의 본문을 바꾸면서 여러 번 게시될 수 있다.

```text
다운로드 중 10%
        ↓
다운로드 중 50%
        ↓
다운로드 완료
```

각 콜백마다 자동 ID를 생성하면 하나의 알림이 세 개의 행으로 쌓일 수 있다.

`StatusBarNotification`은 알림을 식별할 수 있는 `key`를 제공한다.
그래서 이 값을 `notifications` 테이블의 Primary Key로 사용했다.

```kotlin
@PrimaryKey
@ColumnInfo(name = "notification_key")
val notificationKey: String
```

이제 같은 key를 가진 알림은 데이터베이스에서도 같은 행을 가리킨다.

Primary Key는 단순히 중복을 막는 값이 아니라, Android 시스템에서 발생한 같은 알림의 상태 변화를 하나의 데이터로 연결하는 기준이 된다.

## INSERT만 사용하면 어떻게 될까?

새 알림을 저장하기 위해 DAO에 `@Insert`를 사용할 수 있다.

```kotlin
@Insert
suspend fun insert(notification: NotificationEntity)
```

하지만 이미 같은 Primary Key를 가진 행이 있다면 충돌이 발생한다.

충돌 전략을 `IGNORE`로 설정하면 기존 알림의 제목이나 본문이 갱신되지 않는다.
반대로 항상 새로운 행으로 저장하면 하나의 알림이 중복되어 쌓인다.

`noti.`에서는 같은 key가 없다면 새로 저장하고, 이미 존재한다면 현재 알림의 내용으로 갱신해야 했다.

그래서 `@Upsert`를 사용했다.

```kotlin
@Dao
interface NotificationDao {

    @Upsert
    suspend fun upsert(
        notification: NotificationEntity
    )
}
```

Upsert는 Insert와 Update를 합친 동작이다.

Primary Key가 존재하지 않으면 새로운 행을 추가하고, 이미 존재하면 해당 행을 갱신한다.

```text
처음 보는 notificationKey
        ↓
INSERT

이미 저장된 notificationKey
        ↓
UPDATE
```

Repository에서는 도메인 모델을 Entity로 변환한 뒤 DAO에 전달한다.

```kotlin
class NotificationRepository(
    private val notificationDao: NotificationDao
) {
    suspend fun save(
        notification: NotificationItem
    ) {
        notificationDao.upsert(
            notification.toEntity()
        )
    }
}
```

알림 수신 서비스는 Room이나 Entity를 직접 알 필요가 없다.

```kotlin
notificationRepository.save(notificationItem)
```

서비스는 알림 저장을 Repository에 요청하고, Repository가 Mapper와 DAO를 이용해 실제 저장 방법을 결정한다.

이렇게 하면 이후 저장 구조가 달라져도 시스템 콜백을 담당하는 서비스의 코드를 함께 수정할 가능성이 줄어든다.

## 알림이 제거되면 DB에서도 삭제해야 할까?

`NotificationListenerService`는 새로운 알림뿐 아니라 알림이 제거된 시점도 알려 준다.

```kotlin
override fun onNotificationRemoved(
    sbn: StatusBarNotification?
) {
    // 알림 제거 처리
}
```

처음에는 이 콜백이 호출되면 DAO에서 해당 행을 삭제하는 방법을 생각했다.

```sql
DELETE FROM notifications
WHERE notification_key = :notificationKey
```

하지만 시스템 알림 목록에서 사라졌다는 사실과 앱이 보관하던 기록을 삭제한다는 것은 같은 의미가 아니다.

알림은 다음과 같은 이유로 시스템 목록에서 제거될 수 있다.

- 사용자가 직접 알림을 지웠다.
- 사용자가 알림을 눌렀다.
- 알림을 게시한 앱이 알림을 취소했다.
- Android 시스템이 알림 상태를 변경했다.

`noti.`는 사용자가 놓친 중요한 알림을 다시 확인하고, 중요도 판단에 대한 피드백을 남길 수 있어야 한다.

시스템 목록에서 알림이 사라졌다는 이유만으로 DB의 행까지 삭제하면 다음 정보를 잃게 된다.

- 어떤 알림이 도착했는지
- 언제 도착하고 제거되었는지
- 어떤 기준으로 중요하다고 판단했는지
- 사용자가 판단을 수정했는지

그래서 물리적으로 행을 삭제하는 대신 제거 상태를 기록하는 소프트 삭제를 사용했다.

## 소프트 삭제는 데이터를 삭제하지 않는다

소프트 삭제는 행을 실제로 제거하지 않고 삭제된 상태를 나타내는 값을 변경하는 방식이다.

`NotificationEntity`에는 다음 두 필드를 추가했다.

```kotlin
@ColumnInfo(
    name = "is_removed",
    defaultValue = "0"
)
val isRemoved: Boolean = false

@ColumnInfo(
    name = "removed_at",
    defaultValue = "NULL"
)
val removedAt: Long? = null
```

`isRemoved`는 알림이 시스템 알림 목록에서 제거되었는지를 나타낸다.

`removedAt`은 제거된 시각을 저장한다.

```text
알림 수신
is_removed = 0
removed_at = null

알림 제거
is_removed = 1
removed_at = 제거 시각
```

DAO에서는 `DELETE` 대신 `UPDATE`를 실행한다.

```kotlin
@Query(
    """
    UPDATE notifications
    SET is_removed = 1,
        removed_at = :removedAt
    WHERE notification_key = :notificationKey
      AND is_removed = 0
    """
)
suspend fun markAsRemoved(
    notificationKey: String,
    removedAt: Long
): Int
```

`WHERE`에는 key뿐 아니라 `is_removed = 0` 조건도 포함했다.

이미 제거 처리된 알림에 같은 요청이 다시 들어오면 `removedAt`을 덮어쓰지 않기 위해서다.

```text
처음 들어온 제거 요청
is_removed = 0
        ↓
상태 변경, 수정된 행 1개

중복으로 들어온 제거 요청
is_removed = 1
        ↓
변경 없음, 수정된 행 0개
```

같은 제거 요청을 여러 번 실행해도 첫 번째 요청 이후 상태가 달라지지 않는다.

이처럼 같은 요청을 반복해도 결과가 같도록 만드는 성질을 멱등성이라고 한다.

Room의 `UPDATE` 쿼리가 반환하는 `Int`는 실제로 수정된 행의 개수다.

하지만 서비스가 알고 싶은 것은 정확한 행 개수보다 제거 상태가 변경되었는지 여부다.

그래서 Repository에서 `Int`를 `Boolean`으로 변환했다.

```kotlin
suspend fun markAsRemoved(
    notificationKey: String,
    removedAt: Long
): Boolean {
    val updatedRowCount =
        notificationDao.markAsRemoved(
            notificationKey = notificationKey,
            removedAt = removedAt
        )

    return updatedRowCount > 0
}
```

서비스에서는 이 결과에 따라 로그를 구분할 수 있다.

```kotlin
val wasUpdated =
    notificationRepository.markAsRemoved(
        notificationKey = sbn.key,
        removedAt = System.currentTimeMillis()
    )

if (wasUpdated) {
    Log.d(TAG, "Notification marked as removed")
} else {
    Log.d(TAG, "Removed notification was not stored")
}
```

제거 콜백을 받았더라도 해당 알림이 필터링되어 처음부터 저장되지 않았거나, 이미 제거 상태로 변경되었다면 `false`가 반환된다.

## 소프트 삭제했는데 같은 알림이 다시 게시되면?

제거된 알림과 같은 key의 알림이 다시 게시될 수도 있다.

새로 파싱한 `NotificationItem`의 기본 상태는 다음과 같다.

```kotlin
val isRemoved: Boolean = false
val removedAt: Long? = null
```

Repository가 이 모델을 Entity로 변환하고 `upsert()`를 실행하면 기존 행은 새로운 알림 내용으로 갱신된다.

```text
기존 행
is_removed = 1
removed_at = 이전 제거 시각

같은 key의 알림이 다시 게시됨
        ↓
UPSERT
        ↓
is_removed = 0
removed_at = null
```

따라서 하나의 key를 가진 알림이 다시 활성화되더라도 새로운 중복 행을 만들지 않고 기존 행의 현재 상태를 갱신할 수 있다.

다만 모든 과거 변경 이력을 별도의 행으로 남기려는 요구가 생긴다면 현재 구조만으로는 충분하지 않다.

현재 테이블은 알림의 최신 상태를 저장한다.
모든 게시와 제거 이벤트의 이력이 필요하다면 알림 테이블과 별도로 이벤트 이력 테이블을 두는 방식을 검토해야 한다.

MVP에서는 먼저 한 알림의 현재 상태를 일관되게 저장하는 데 집중했다.

## 필드를 추가하면 기존 DB는 어떻게 될까?

처음 만든 Entity에는 `is_removed`와 `removed_at`이 없었다.

소프트 삭제를 추가하면서 데이터베이스 스키마가 변경되었고, Room의 버전을 1에서 2로 올렸다.

```kotlin
@Database(
    entities = [NotificationEntity::class],
    version = 2,
    exportSchema = false
)
abstract class NotiDatabase : RoomDatabase() {

    abstract fun notificationDao(): NotificationDao
}
```

앱을 삭제하고 다시 설치하면 새로운 스키마로 DB를 만들 수 있다.

하지만 실제 사용자가 이미 저장한 알림이 있다면 앱 업데이트 때마다 DB를 지울 수 없다.

기존 데이터를 유지하면서 스키마를 변경하기 위해 1에서 2로 이동하는 Migration을 작성했다.

```kotlin
val MIGRATION_1_2 = object : Migration(1, 2) {

    override fun migrate(
        db: SupportSQLiteDatabase
    ) {
        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN is_removed
            INTEGER NOT NULL DEFAULT 0
            """.trimIndent()
        )

        db.execSQL(
            """
            ALTER TABLE notifications
            ADD COLUMN removed_at
            INTEGER DEFAULT NULL
            """.trimIndent()
        )
    }
}
```

기존 행에는 새 컬럼의 값이 없기 때문에 기본값이 필요하다.

- 기존 알림은 제거되지 않은 상태로 보기 위해 `is_removed`의 기본값을 `0`으로 설정했다.
- 제거 시각은 아직 없으므로 `removed_at`의 기본값을 `NULL`로 설정했다.

작성한 Migration은 데이터베이스를 생성할 때 등록한다.

```kotlin
Room.databaseBuilder(
    this,
    NotiDatabase::class.java,
    "noti.db"
)
    .addMigrations(MIGRATION_1_2)
    .build()
```

Entity의 프로퍼티 하나를 추가한 변경이지만, 이미 설치된 앱의 관점에서는 실제 테이블의 구조를 변경하는 작업이다.

Room의 버전과 Migration은 코드의 최신 구조뿐 아니라 이전 버전의 데이터를 어떻게 보존할지도 함께 표현한다.

## Room 객체는 어디에서 만들어야 할까?

Room 데이터베이스 인스턴스는 앱에서 하나만 만들어 공유하는 편이 적절하다.

현재는 별도의 DI 라이브러리를 도입하지 않고 `Application`에서 Database와 Repository를 생성한다.

```kotlin
class NotiApplication : Application() {

    val database: NotiDatabase by lazy {
        Room.databaseBuilder(
            this,
            NotiDatabase::class.java,
            DATABASE_NAME
        )
            .addMigrations(MIGRATION_1_2)
            .build()
    }

    val notificationRepository:
        NotificationRepository by lazy {
            NotificationRepository(
                notificationDao =
                    database.notificationDao()
            )
        }

    companion object {
        private const val DATABASE_NAME = "noti.db"
    }
}
```

`by lazy`를 사용했기 때문에 실제로 처음 접근하는 시점에 객체가 생성되고, 이후에는 같은 인스턴스를 사용한다.

서비스에서는 `Application`을 통해 Repository를 가져온다.

```kotlin
private val notificationRepository by lazy {
    (application as NotiApplication)
        .notificationRepository
}
```

현재 규모에서는 객체가 생성되는 위치를 직접 확인할 수 있는 단순한 방식이다.

기능이 늘어나고 Repository와 의존성이 많아지면 Hilt 같은 의존성 주입 도구를 검토할 수 있지만, 지금 단계에서는 필요한 객체와 생성 위치를 먼저 명확하게 만드는 데 집중했다.

## 알림 목록은 어떻게 변경을 알 수 있을까?

Room에 알림을 저장했더라도 화면이 데이터 변경을 알지 못하면 매번 목록을 다시 요청해야 한다.

DAO의 조회 함수는 `Flow`를 반환하도록 만들었다.

```kotlin
@Query(
    """
    SELECT *
    FROM notifications
    ORDER BY posted_at DESC
    """
)
fun observeAll():
    Flow<List<NotificationEntity>>
```

Room은 `notifications` 테이블이 변경되면 쿼리를 다시 실행하고 새로운 목록을 Flow로 전달할 수 있다.

Repository에서는 Entity 목록을 도메인 모델 목록으로 변환한다.

```kotlin
fun observeAll():
    Flow<List<NotificationItem>> {
    return notificationDao.observeAll()
        .map { entities ->
            entities.map { entity ->
                entity.toDomain()
            }
        }
}
```

현재 쿼리는 제거된 알림을 포함한 전체 기록을 반환한다.

이후 화면의 목적에 따라 쿼리를 분리할 수 있다.

```text
현재 시스템 알림 목록
WHERE is_removed = 0

수집한 전체 알림 기록
제거 여부와 관계없이 조회

제거된 알림 기록
WHERE is_removed = 1
```

Room을 사용하면 데이터가 변경될 때마다 UI가 직접 DB를 반복 조회하는 대신, 변경을 관찰하는 흐름을 만들 수 있다.

`suspend` 함수와 Flow가 실제로 어떻게 비동기 작업을 처리하는지는 다음 글에서 조금 더 자세히 살펴보려고 한다.

## 현재 알림 저장 흐름

지금까지 구현한 흐름을 정리하면 다음과 같다.

```text
알림 게시
    ↓ onNotificationPosted()
NotificationParser
    ↓
NotificationItem
    ↓
NotificationRepository.save()
    ↓
NotificationMapper
    ↓
NotificationDao.upsert()
    ↓
Room

알림 제거
    ↓ onNotificationRemoved()
notificationKey + removedAt
    ↓
NotificationRepository.markAsRemoved()
    ↓
NotificationDao
    ↓
is_removed = 1
```

새 알림과 기존 알림을 서비스가 직접 구분하지 않는다.

같은 `notificationKey`를 Primary Key로 사용하고 `@Upsert`를 실행함으로써 데이터베이스가 삽입과 갱신을 결정한다.

알림이 제거되었을 때도 행을 바로 삭제하지 않는다.

`isRemoved`와 `removedAt`을 변경해 시스템 알림 목록에서는 사라졌지만 `noti.`가 수집한 기록으로는 남아 있다는 상태를 표현한다.

## 마무리

Room을 연결하는 일은 Entity, DAO, Database 클래스를 만드는 것으로 끝나지 않았다.

먼저 저장하려는 데이터가 어떤 생명주기를 가지는지 정해야 했다.

Android 알림은 같은 key로 다시 게시될 수 있고, 게시된 뒤에는 시스템 목록에서 제거될 수 있다.

현재 `noti.`에서는 이 변화를 다음과 같이 저장한다.

- `StatusBarNotification.key`를 Primary Key로 사용한다.
- 처음 받은 key는 Insert하고, 같은 key는 `@Upsert`로 갱신한다.
- 알림이 제거되면 행을 삭제하지 않고 `isRemoved`와 `removedAt`을 변경한다.
- 중복 제거 요청은 `is_removed = 0` 조건으로 상태를 다시 변경하지 않는다.
- Entity 변경으로 추가된 컬럼은 Migration을 통해 기존 DB에 반영한다.
- DAO를 직접 노출하지 않고 Repository와 Mapper를 통해 도메인 모델로 변환한다.

결국 Room에 무엇을 저장할지 정하는 일은 단순히 데이터 클래스의 필드를 테이블로 옮기는 일이 아니었다.

알림이 생성되고, 내용이 바뀌고, 제거되는 과정을 어떤 상태로 표현할지 결정하는 일이었다.

그런데 현재 DAO의 저장과 수정 함수에는 `suspend`가 붙어 있다.

```kotlin
@Upsert
suspend fun upsert(
    notification: NotificationEntity
)
```

반면 Android 시스템이 호출하는 `onNotificationPosted()`와 `onNotificationRemoved()`는 일반 함수다.

그렇다면 일반 함수인 알림 콜백에서 `suspend` 함수는 어떻게 호출해야 할까?
그리고 알림이 연속으로 들어오거나 서비스가 종료될 때 실행 중인 저장 작업은 어떻게 관리해야 할까?

다음 글에서는 `CoroutineScope`, `SupervisorJob`, `Dispatchers.IO`를 사용해 Room 작업을 서비스의 생명주기와 연결한 과정을 정리해 보려고 한다.

## 참고 자료

- [Android Developers: Save data in a local database using Room](https://developer.android.com/training/data-storage/room)
- [Android Developers: Define data using Room entities](https://developer.android.com/training/data-storage/room/defining-data)
- [Android Developers: Access data using Room DAOs](https://developer.android.com/training/data-storage/room/accessing-data)
- [Android Developers: Upsert](https://developer.android.com/reference/androidx/room/Upsert)
- [Android Developers: Write asynchronous DAO queries](https://developer.android.com/training/data-storage/room/async-queries)
- [Android Developers: Migrate your Room database](https://developer.android.com/training/data-storage/room/migrating-db-versions)
