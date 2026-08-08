# noti. 알림 데이터셋 v0.4 설계

## 이번 버전에서 바꾼 문제 정의

v0.3의 `label`은 알림의 일반적인 중요도와 개인의 선호를 하나의 이진 정답으로 표현했다. 하지만 배송 출발, 입금 완료, 일반 메시지처럼 같은 알림도 사용자에 따라 중요도가 달라질 수 있다.

v0.4부터 공통 모델과 개인화 모델의 역할을 분리한다.

```text
공통 KoELECTRA 모델
→ 알림의 일반적인 행동 필요성과 이벤트 유형을 판단

Android 개인화 계층
→ 사용자의 중요/일반 피드백으로 앱·이벤트 유형별 선호를 보정
```

공통 학습 데이터에는 특정 사용자의 `user_label`을 정답으로 섞지 않는다.

## 공통 모델의 정답

`actionability`는 다음 네 값 중 하나다. 최초 초안은 세 값이었지만, 사용자 검수에서 “해야 할 행동은 없어도 먼저 확인할 가치가 있는 알림”이 반복적으로 발견되어 `ATTENTION_WORTHY`를 분리했다.

| 값 | 의미 | 예시 |
|---|---|---|
| `ACTION_REQUIRED` | 사용자의 확인이나 행동이 필요함 | 결제 실패, 보안 경고, 주소 확인, 마감 임박 |
| `ATTENTION_WORTHY` | 직접 행동은 없어도 먼저 확인할 가치가 있음 | 배송 출발, 입금 완료, 일정 변경, 주문 취소 |
| `INFORMATIONAL` | 알아두면 되는 일반 정보 | 요약, 일반 상태 안내, 관심 소식 |
| `PROMOTIONAL` | 선택적 참여나 소비를 유도함 | 광고, 추천, 설문, 장바구니, 가격 하락 |

`base_label`은 기존 이진 분류 파이프라인과 호환하기 위한 값이다.

```text
ACTION_REQUIRED → 1
ATTENTION_WORTHY → 1
INFORMATIONAL   → 0
PROMOTIONAL     → 0
```

기존 `label`도 v0.4에서는 `base_label`과 같은 값을 저장한다. v0.3의 값은 `previous_label`에 보존하여 라벨 변경을 추적한다.

## 개인화 메타데이터

`preference_sensitive=true`는 사용자마다 중요도가 달라질 가능성이 큰 알림이라는 뜻이다. 이 값 자체는 중요/일반 정답이 아니다.

개인화 후보 예시는 다음과 같다.

- 일정 변경
- 주문 취소
- 일반 상태 안내와 요약
- 관심 콘텐츠와 가격 변화
- 일반 메시지와 개인 일정

명백한 결제 실패나 보안 경고는 공통 모델이 놓치지 않아야 하므로 초기 정책에서는 개인화 후보에서 제외한다. 명시적인 광고와 일반 설문도 초기 개인화 대상에서 제외한다.

`personalization_scope=APP_EVENT_TYPE`인 경우 Android는 나중에 `packageName + eventType` 단위의 사용자 보정값을 적용할 수 있다.

## 이벤트 유형

v0.4는 기존의 세부 `notification_type`을 Android 개인화에서 사용하기 쉬운 `event_type`으로 정규화한다. 예시는 다음과 같다.

| 기존 유형 | v0.4 이벤트 유형 |
|---|---|
| `payment_failure`, `card_declined`, `autopay_failure` | `PAYMENT_PROBLEM` |
| `security_change`, `suspicious_payment` | `SECURITY` |
| `schedule_change` | `SCHEDULE_CHANGE` |
| `delivery_exception` | `DELIVERY_PROBLEM` |
| `summary` | `SUMMARY` |
| `promotion` | `PROMOTION` |
| `relationship_message` | `MESSAGE` |
| `personal_schedule` | `PERSONAL_SCHEDULE` |

## 생성 결과

| 파일 | 행 수 | 용도 |
|---|---:|---|
| `train_notifications_v0.4.csv` | 520 | 공통 행동 필요성 학습·대조 데이터 |
| `context_notifications_v0.4.csv` | 80 | 공통 정답을 부여하지 않은 개인화 문맥 데이터 |
| `review_notifications_v0.4.csv` | 30 | 정책 경계와 개인화 후보를 사람이 확인할 표본 |
| `public_evaluation_v0.4.csv` | 0 | 공개 실데이터의 검토 전 입구 |
| `source_manifest_v0.4.csv` | 9 sources | 출처와 이용 상태 기록 |

학습 데이터의 분포는 억지로 1:1로 맞추지 않는다.

| Actionability | 행 수 |
|---|---:|
| `ACTION_REQUIRED` | 186 |
| `ATTENTION_WORTHY` | 94 |
| `INFORMATIONAL` | 70 |
| `PROMOTIONAL` | 170 |

이진 `base_label`은 `1=280`, `0=240`이다. `1`은 AI가 REVIEW 알림에 가점을 줄 공통 후보이며 `ACTION_REQUIRED`와 `ATTENTION_WORTHY`를 포함한다. 실제 제품 분포와 비용 함수를 고려해 학습 시 class weight나 threshold를 조절하며, 데이터 자체를 균형 숫자에 맞추기 위해 정답을 바꾸지 않는다.

v0.3에는 정상적인 배송 상태와 완료된 금융 상태가 부족했다. v0.4에서 다음 현실형 합성 문장 40개를 추가했다.

- 오늘·내일 도착 예정이 포함된 정상 배송 상태 20개
- 입금·이체·결제·송금 완료 상태 20개

두 유형은 모두 `ATTENTION_WORTHY`, `base_label=1`이다. 정상 배송 상태는 개인차가 큰 유형으로 유지하고, 완료된 금융 상태는 사용자 검수 결과에 따라 공통적으로 먼저 확인할 가치가 있는 유형으로 정의했다. 실제 앱의 문장을 복사하지 않고 한국 알림의 일반적인 표현을 참고해 직접 작성했다.

## v0.3과의 관계

v0.3에서 중요 방향이었던 일정 변경 42개와 주문 취소 12개는 `ATTENTION_WORTHY`로 세분화했다. 따라서 기존 이진 라벨의 방향은 유지하면서, 실제 행동이 필요한 알림과 먼저 확인할 가치가 있는 알림을 구분한다.

원래 라벨은 `previous_label`에 남아 있어 언제든 비교할 수 있다. 새로 추가한 v0.4 문장 40개는 이전 라벨이 없으므로 `previous_label`이 비어 있다.

## 검수 원칙

`review_notifications_v0.4.csv`의 30개는 다음 질문으로 확인한다.

1. 대부분의 사용자가 이 알림을 보고 곧바로 행동해야 하는가?
2. 행동은 없어도 먼저 확인할 가치가 있는가?
3. 알아두면 되는 일반 정보인가?
4. 선택적 소비·참여를 유도하는가?
5. 사용자에 따라 중요도가 크게 달라질 수 있는가?

검수자는 자신의 개인 취향이 아니라 공통 모델의 기준으로 `user_actionability`를 작성한다. 개인차 여부는 `user_preference_sensitive`에 별도로 작성한다.

첫 검수에서는 30개 응답을 받았다. 학습 데이터에 속한 20개는 `HUMAN_REVIEWED_V04`로 표시하고 검수한 개인차 값을 반영했다. 문맥 데이터 10개는 검수 결과를 기록하되, 한 사람의 판단을 공통 학습 정답으로 승격하지 않고 계속 `training_eligible=false`로 유지한다.

## 아직 하지 않은 것

- 여러 fold를 사용한 이벤트 유형 균형 교차검증은 아직 하지 않았다.
- Android의 개인화 보정 테이블과 온라인 업데이트 코드를 구현하지 않았다.
- Room 실데이터의 사용자 피드백을 공통 정답으로 승격하지 않았다.
- 실제 Android 기기의 성능과 배터리를 측정하지 않았다.

v0.4 첫 fold 학습과 TFLite 변환은 완료했지만 실제 배송 문장을 놓치고 프로모션 오탐이 많아 Android 중요도 점수에는 연결하지 않는다. 결과는 `reports/koelectra_v0.4_training.md`에 기록한다.
