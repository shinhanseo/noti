# LiteRT 모바일 후보 비교 v1

## 결론

`noti.`의 1차 Android 적용 후보는 **EmbeddingGemma 300M INT8**로 결정한다.
실제 삼성 SM-S711N에서도 Granite보다 정확하고, 빠르고, 실행 메모리가 작았다.
배포 파일은 약 300 MiB로 크지만 Granite의 작은 파일이 실제 실행 비용 절감으로
이어지지 않았다. INT4는 파일과 RAM을 줄였지만 속도와 중요 Recall이 나빠져
채택하지 않는다.

## 변환 조건

| 항목 | Granite 97M R2 | EmbeddingGemma 300M |
| --- | --- | --- |
| 입력 | `input_ids`, `attention_mask` | `input_ids`, `attention_mask` |
| 고정 길이 | 64 tokens | 64 tokens |
| pooling | CLS + L2 normalize | mean + Dense 2개 + L2 normalize |
| 양자화 | INT8 weight-only | INT8 dynamic |
| 출력 차원 | 384 | 768 |
| TFLite 크기 | 96.1 MiB | 299.5 MiB |

EmbeddingGemma는 `litert-torch 0.9.3`에 포함된 Google 공식 전용 변환 구현을
사용했다. Granite는 Hugging Face `ModernBERT` encoder에 모델 설정과 동일한 CLS
pooling 및 L2 정규화를 붙인 뒤 LiteRT Torch로 변환했다.

## 양자화 후 품질 보존

기존 동일조건 실험에서 저장한 MLP 32-unit head를 바꾸지 않고, Room 100개의
임베딩만 TFLite 출력으로 교체했다.

| 모델 | 원본과 평균 cosine | 최소 cosine | 원본 대비 예측 변경 | Room Accuracy | 중요 F1 | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Granite 97M R2 INT8 | 0.999565 | 0.999069 | 1/100 | 89% | 0.522 | 9 | 2 |
| EmbeddingGemma 300M INT8 | 0.997700 | 0.996057 | 0/100 | 92% | 0.600 | 6 | 2 |
| EmbeddingGemma 300M INT4 block32 | 0.943396 | 0.915503 | 6/100 | 92% | 0.500 | 4 | 4 |

Granite는 양자화 경계에서 일반 알림 1개의 예측이 바뀌어 Accuracy가 90%에서
89%로 내려갔다. EmbeddingGemma INT8은 100개 예측이 모두 유지됐다.
INT4 EmbeddingGemma는 전체 Accuracy는 같지만 중요한 알림 Recall이 0.75에서
0.50으로 내려갔으므로 동일 품질 모델로 보지 않는다.

## Android 에뮬레이터 CPU 벤치마크

- 기기: `sdk_gphone16k_arm64` Android 17 / API 37 emulator
- ABI: `arm64-v8a`
- runtime: Google LiteRT `benchmark_model`, CPU XNNPACK
- 입력: batch 1, 64 tokens, attention mask 전체 활성
- 반복: 모델별 3 trial × 50 inference, trial마다 3 warm-up
- 표의 값: 세 trial의 중앙값

| 모델 | 평균 추론 | 최소 추론 | 초기화 | 첫 warm-up | Init footprint | Overall footprint |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Granite 97M R2 INT8 | 40.53 ms | 39.92 ms | 108.92 ms | 227.97 ms | 255.75 MB | 651.78 MB |
| EmbeddingGemma 300M INT8 | 35.22 ms | 34.33 ms | 76.70 ms | 40.45 ms | 234.08 MB | 238.59 MB |

EmbeddingGemma는 파일이 더 큰데도 steady-state 추론이 약 13% 빨랐다. Granite는
그래프 대부분이 XNNPACK에 위임됐지만, weight-only 가중치를 실행용으로 패킹하는
비용 때문에 첫 실행과 메모리 footprint가 커진 것으로 추정된다. EmbeddingGemma는
RMSNorm과 attention 관련 subgraph가 다수로 분리됐지만 동적 INT8 실행 경로가
에뮬레이터에서는 더 효율적이었다.

## 삼성 SM-S711N 실기기 CPU 벤치마크

- 기기: Samsung SM-S711N, Android 16 / API 36, 8-core ARM64
- runtime: Google LiteRT `benchmark_model`, CPU XNNPACK
- 조건: batch 1, 64 tokens, 모델별 3 trial × 50 inference
- 표의 값: 세 trial의 중앙값

| 모델 | TFLite | 평균 추론 | 초기화 | 첫 warm-up | Init footprint | Overall footprint |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Granite INT8 weight-only | 96.1 MiB | 66.52 ms | 220.10 ms | 451.36 ms | 255.64 MB | 652.33 MB |
| EmbeddingGemma INT8 dynamic | 299.5 MiB | 58.41 ms | 210.00 ms | 71.71 ms | 232.97 MB | 263.89 MB |
| EmbeddingGemma INT4 block32 | 166.8 MiB | 85.68 ms | 110.40 ms | 101.78 ms | 136.69 MB | 167.51 MB |

Granite의 약 652 MB footprint가 실기기에서도 재현됐다. EmbeddingGemma INT8은
파일은 크지만 Granite보다 약 12% 빠르고 실행 footprint는 약 60% 작다. INT4는
RAM을 더 줄이지만 INT8보다 약 47% 느리고 중요한 알림 품질도 낮아졌다.

### EmbeddingGemma INT8 지속 부하

500번 연속 추론에서는 평균 52.83 ms, 중앙값 50.24 ms, 최소 49.46 ms였다.
실행 중 `top`의 CPU 사용률은 약 98.5~100%로 코어 1개를 가득 쓰는 수준이었고,
RSS는 약 302 MB였다. 배터리 온도는 34.4°C에서 35.3°C로 약 0.9°C 상승했다.
실제 앱은 알림 도착 때 한 번만 약 50~60 ms 실행하므로 이 연속 부하보다 훨씬
낮은 duty cycle이다. USB 충전 중이어서 배터리 소모량 자체는 판정하지 않았다.

## 해석 제한

- 에뮬레이터 수치는 실제 스마트폰 SoC의 CPU, 발열, 메모리 대역폭, 배터리를
  대표하지 않는다.
- footprint는 LiteRT benchmark 도구가 보고한 값이며 앱 프로세스의 Android Studio
  Profiler peak RSS와 동일한 지표가 아니다.
- 에뮬레이터 첫 trial에는 스케줄링 이상치가 관찰돼 3 trial 중앙값을 사용했다.
- tokenizer 시간과 Kotlin 전처리 시간은 포함하지 않은 순수 모델 추론 시간이다.
- tokenizer 시간과 앱의 Kotlin/Room 처리 시간은 이후 통합 측정에 추가해야 한다.

## 다음 판단 기준

1. EmbeddingGemma INT8을 앱의 shadow mode에 연결한다.
2. tokenizer와 MLP head를 포함한 end-to-end latency 및 앱 RSS를 측정한다.
3. AI 점수는 바로 사용자 화면 판정에 반영하지 않고 예측·피드백만 Room에 기록한다.
4. 배포 파일 300 MiB는 앱 번들 포함 또는 최초 실행 후 다운로드 전략을 별도로
   결정한다.

원본 수치는 `litert_android_emulator_benchmark_v1.json`,
`litert_samsung_sm_s711n_benchmark_v1.json`,
`litert_samsung_sm_s711n_embeddinggemma_int4_benchmark_v1.json`,
`litert_quantized_quality_v1.json`에 저장한다.
