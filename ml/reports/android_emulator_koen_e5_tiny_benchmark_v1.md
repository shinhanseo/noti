# KoEn-E5-Tiny Android 에뮬레이터 기준선 v1

## 측정 환경

- 날짜: 2026-08-18
- 기기: Android Studio Pixel 7 AVD (`sdk_gphone16k_arm64`)
- ABI: `arm64-v8a`
- Android API: 37
- 가상 메모리: 2,042,240 kB
- 가상 CPU: 4개
- ONNX Runtime: 1.29.0, CPU Execution Provider, intra-op thread 4개
- 입력 길이: 64 token
- 워밍업: 5회
- 본 측정: 서로 다른 알림 문장 5개를 순환해 50회

## 결과

| 항목 | 결과 |
| --- | ---: |
| 모델·토크나이저 초기화 | 161.548 ms |
| 첫 추론 | 15.045 ms |
| 워밍업 후 평균 | 5.735 ms |
| 워밍업 후 중앙값 | 5.089 ms |
| 워밍업 후 P95 | 10.118 ms |
| 워밍업 후 최소 | 4.097 ms |
| 워밍업 후 최대 | 13.637 ms |
| 초기 PSS | 122,169 kB |
| 모델 초기화 후 PSS | 202,480 kB |
| 반복 추론 후 PSS | 205,765 kB |
| 모델 초기화 PSS 증가량 | 80,311 kB |

## 용량

| 구성요소 | 크기 |
| --- | ---: |
| 결합 ONNX 모델 | 38,326,362 bytes |
| SentencePiece tokenizer | 960,018 bytes |
| ARM64 `libonnxruntime.so` | 32,120,992 bytes |
| ARM64 debug APK | 91,146,297 bytes |

## 해석

현재 구조는 알림이 올 때마다 모델을 초기화하지 않는다. 첫 `REVIEW` 알림에서 한 번 초기화한 뒤 앱 프로세스 안에서 재사용하므로, 정상적인 지속 실행 비용은 워밍업 후 추론 시간에 가깝다.

이 결과는 기능 검증과 변경 전후 비교를 위한 에뮬레이터 기준선이다. 호스트 Mac의 CPU를 사용하는 가상 기기이므로 실제 Android 스마트폰의 속도, RAM, 발열, 배터리 소모로 해석할 수 없다. 물리 기기에서는 동일한 계측 테스트를 다시 실행해야 한다.
