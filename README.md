<p align="center">
  <img src="./app/src/main/res/drawable-nodpi/noti_launcher_art.png" width="112" alt="noti. app icon" />
</p>

<h1 align="center">noti.</h1>

<p align="center">
  <strong>온디바이스 AI와 사용자 피드백으로 중요한 알림을 먼저 보여주는 Android 앱</strong>
</p>

<p align="center">
  알림을 외부 서버로 보내지 않고 기기 안에서 분류하며,<br />
  중요하다고 판단한 이유까지 사용자가 이해할 수 있게 설명합니다.
</p>

<p align="center">
  <a href="https://velog.io/@imkara/series/noti."><img src="https://img.shields.io/badge/Velog-Series-20C997?style=flat-square&logo=velog&logoColor=white" alt="noti. Velog Series" /></a>
  <a href="https://quiet-lifter-473.notion.site/noti-3c812450961b802dacedf0ddff3134a0"><img src="https://img.shields.io/badge/Privacy-Policy-475569?style=flat-square" alt="noti. Privacy Policy" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Closed_Test_Preparation-2563EB?style=flat-square" alt="Closed Test Preparation" />
  <img src="https://img.shields.io/badge/Android_8.0+-3DDC84?style=flat-square&logo=android&logoColor=white" alt="Android 8.0 or later" />
  <img src="https://img.shields.io/badge/Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white" alt="Kotlin" />
  <img src="https://img.shields.io/badge/Jetpack_Compose-4285F4?style=flat-square&logo=jetpackcompose&logoColor=white" alt="Jetpack Compose" />
  <img src="https://img.shields.io/badge/AI-On--device_ONNX-005CED?style=flat-square&logo=onnx&logoColor=white" alt="On-device ONNX" />
</p>

---

## Overview

메신저, 일정, 결제, 배송, 광고 알림이 한꺼번에 쌓이면 지금 확인해야 할 내용을 찾는 일 자체가 피로가 됩니다. `noti.`는 Android 알림을 수집해 **중요한 알림을 먼저 선별하고, 왜 그렇게 판단했는지 함께 보여주는 알림 보조 앱**입니다.

사용자가 지정한 앱과 키워드를 우선하고, 규칙만으로 판단하기 애매한 알림에만 온디바이스 AI를 사용합니다. 잘못 분류된 알림은 사용자가 직접 수정할 수 있으며, 그 피드백은 이후 비슷한 알림의 점수에 반영됩니다.

> 개인 프로젝트로 제품 기획, UI/UX, Android 구현, 데이터 정책, ML 실험과 모바일 배포 전 과정을 진행하고 있습니다.

## Screens

<p align="center">
  <img src="./docs/screens/home-anonymized.png" width="18%" alt="noti. 중요 알림 홈 화면" />
  <img src="./docs/screens/importance-reason.png" width="18%" alt="noti. 중요도 판정 이유 화면" />
  <img src="./docs/screens/important-apps.png" width="18%" alt="noti. 중요 앱 설정 화면" />
  <img src="./docs/screens/important-keywords.png" width="18%" alt="noti. 중요 키워드 설정 화면" />
  <img src="./docs/screens/exclusion-keywords.png" width="18%" alt="noti. 앱별 제외 키워드 화면" />
</p>

## Key Features

| 기능 | 설명 |
| --- | --- |
| 알림 수집 | `NotificationListenerService`로 앱이 화면에 없어도 새 알림을 수집합니다. |
| 하이브리드 분류 | 사용자 규칙, 설명 가능한 점수 정책, 개인화와 온디바이스 AI를 단계적으로 결합합니다. |
| 판정 이유 | 중요 앱, 키워드, 보안·결제·일정 문맥 등 실제 점수 근거를 함께 저장하고 표시합니다. |
| 사용자 피드백 | `중요하게 보기`와 `덜 중요하게 보기` 및 선택한 이유를 다음 판단에 반영합니다. |
| 내 기준 설정 | 중요 앱, 중요 키워드, 앱별 제외 키워드를 사용자가 직접 관리합니다. |
| 로컬 우선 | 알림 본문, 분류 결과와 피드백을 외부 AI API가 아닌 사용자 기기 안에서 처리합니다. |
| 수집 안정성 | 배터리 제한 상태를 안내하고 WorkManager가 알림 리스너 연결 상태를 주기적으로 점검합니다. |

## Importance Decision Flow

```text
Android Notification
        ↓
Parse · Normalize · Filter
        ↓
Explainable Rule Engine
        ↓
Forced decision? ── yes ──→ Final result
        │ no
        ↓
On-device Personalization
(app · channel · topic)
        ↓
Still REVIEW? ── no ──────→ Final result
        │ yes
        ↓
KoEn-E5-Tiny INT8 ONNX Classifier
        ↓
Score · Reasons · Feedback → Room
        ↓
Flow → ViewModel → Jetpack Compose UI
```

명시적인 중요 앱·키워드처럼 확실한 사용자 규칙을 가장 먼저 적용합니다. 개인화까지 거친 뒤에도 판단이 애매한 `REVIEW` 구간에서만 AI를 실행해 불필요한 추론과 과도한 AI 의존을 줄였습니다.

## On-device Personalization

피드백은 공통 AI 모델을 휴대폰에서 다시 학습시키는 방식이 아닙니다. 알림의 앱, 채널과 Topic을 조합한 개인화 프로필을 Room에 누적하고 다음 알림의 중요도 점수를 보정합니다.

```text
사용자가 분류 결과 수정
        ↓
중요하거나 중요하지 않은 이유 선택
        ↓
App · Channel · Topic 조합 추출
        ↓
기기 내부 개인화 프로필 갱신
        ↓
다음 유사 알림의 점수 보정 (-15 ~ +15)
```

- 구체적인 `앱 + 채널 + Topic` 피드백을 넓은 앱 단위 피드백보다 우선합니다.
- 같은 방향의 피드백이 반복되면 영향력이 커지고, 서로 충돌하면 보정 강도가 낮아집니다.
- 첫 피드백부터 작은 점수로 반영하되 강제 규칙보다 우선하지 않습니다.
- 원문과 개인화 프로필은 서버에 업로드하지 않습니다.

## On-device AI

현재 Android 앱에는 약 **36.5 MiB**의 `KoEn-E5-Tiny` ARM64 INT8 ONNX 모델과 SentencePiece Tokenizer가 포함되어 있습니다. 한국어 알림 문장을 임베딩한 뒤 학습한 작은 MLP 분류기로 다음 세 클래스를 예측합니다.

| Class | 의미 |
| --- | --- |
| `GENERAL` | 별도의 즉시 확인이 필요하지 않은 일반 정보 |
| `ATTENTION_WORTHY` | 사용자가 가까운 시점에 확인할 가치가 있는 알림 |
| `ACTION_REQUIRED` | 승인, 인증, 응답처럼 직접 행동이 필요한 알림 |

모델 정확도만 비교하지 않고 실제 알림에서의 중요 알림 Recall, 오탐, 모델 크기, 메모리 사용량과 모바일 추론 비용을 함께 평가했습니다. 실험 과정과 재현 가능한 결과는 [`ml/reports`](./ml/reports)에서 확인할 수 있습니다.

## Reliability

일부 Android 제조사는 배터리 절약을 위해 백그라운드 프로세스와 알림 리스너를 종료할 수 있습니다. `noti.`는 이를 완전히 막을 수 있다고 가정하지 않고 다음 방어 장치를 적용합니다.

- 온보딩과 내 기준 화면에서 알림 접근 권한 및 배터리 사용 제한 상태 안내
- 앱 진입 시 알림 리스너 연결 상태 확인과 필요 시 재연결 요청
- WorkManager를 이용한 15분 주기의 연결 상태 점검
- 부팅 후 작업 재등록 및 중복되지 않는 Unique Periodic Work 구성

WorkManager 실행 시각은 Android 시스템 정책에 따라 달라질 수 있으며, 제조사가 앱 프로세스를 강제로 중지한 상황까지 즉시 복구하는 수단은 아닙니다.

## Architecture

| Layer | Responsibility |
| --- | --- |
| `notification` | 시스템 알림 수집, 파싱, 필터링, 리스너 복구 작업 |
| `domain/importance` | 점수 규칙, 텍스트 전처리, 중요도 판정 |
| `domain/personalization` | 앱·채널·Topic 기반 피드백 누적과 점수 보정 |
| `domain/topic` | 알림 문맥에서 개인화용 Topic 추출 |
| `ai` | SentencePiece 토크나이징, ONNX 추론, 결과 매핑 |
| `data` | Room, DataStore, Repository와 Migration |
| `ui` | 온보딩, 홈, 알림 목록, 피드백, 내 기준 화면 |

## Tech Stack

`Kotlin` · `Jetpack Compose` · `Material 3` · `Room` · `Hilt` · `DataStore` · `Flow` · `WorkManager` · `ONNX Runtime` · `SentencePiece` · `C++/JNI` · `JUnit`

## Project Structure

```text
noti/
├── app/                 Android application
│   └── src/main/
│       ├── java/        Kotlin source
│       ├── cpp/         SentencePiece JNI bridge
│       └── assets/ai/   ONNX model and tokenizer
├── ml/                  Dataset, training and evaluation pipeline
├── docs/                Product, architecture and policy documents
└── store-assets/        Google Play listing assets
```

## Build & Test

### Requirements

- Android Studio
- JDK 17
- Android SDK 36
- Android NDK `28.2.13676358`
- CMake `3.22.1`

### Commands

```bash
./gradlew test
./gradlew connectedAndroidTest
./gradlew :app:assembleDebug
```

테스트는 중요도 규칙과 AI 결과 결합, 피드백 기반 개인화, Topic 추출, 텍스트 전처리, Room Migration, Repository 통합, ONNX·Tokenizer 호환성을 포함합니다.

## Product Principles

- **Explainable** — 모든 중요 판정에 사용자가 이해할 수 있는 근거를 남깁니다.
- **Local-first** — 알림 제목과 본문을 외부 서버나 원격 AI API로 전송하지 않습니다.
- **User-controlled** — 자동 판정보다 사용자가 지정한 앱·키워드와 피드백을 우선합니다.
- **Conservative** — 확실한 규칙을 먼저 적용하고 애매한 알림에만 AI를 사용합니다.

## Documentation

- [제품 정의](./docs/product.md)
- [아키텍처](./docs/architecture.md)
- [중요도 정책](./docs/importance-policy.md)
- [개발 계획](./docs/development-plan.md)
- [ML 실험 및 재현 방법](./ml/README.md)
- [개인정보처리방침](https://quiet-lifter-473.notion.site/noti-3c812450961b802dacedf0ddff3134a0)

## Release Status

- [x] 알림 수집과 중요도 규칙 엔진
- [x] 온디바이스 ONNX 추론
- [x] 피드백 수집과 개인화 점수 반영
- [x] 알림 리스너 상태 점검과 배터리 제한 안내
- [x] Google Play 스토어 등록정보 및 개인정보처리방침 준비
- [ ] Google Play 비공개 테스트
- [ ] 프로덕션 출시

현재 Google Play 비공개 테스트 배포를 준비하고 있습니다. 실제 사용자 환경에서 분류 품질과 장시간 알림 수집 안정성을 검증한 뒤 프로덕션 출시를 진행할 예정입니다.
