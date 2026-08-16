# EmbeddingGemma Actionability v1 Android 전달 명세

## 결론

`noti_embeddinggemma_actionability_v1_int8.tflite`는 EmbeddingGemma INT8 encoder와
학습된 32-unit MLP 분류 Head를 하나의 LiteRT/TFLite 그래프로 결합한 Android
전달용 모델이다. 모델 출력은 embedding이 아니라 세 Actionability 확률이다.

## 전달 파일

- `models/noti_embeddinggemma_actionability_v1/noti_embeddinggemma_actionability_v1_int8.tflite`
- `models/noti_embeddinggemma_actionability_v1/tokenizer/`
- `models/noti_embeddinggemma_actionability_v1/model_metadata.json`
- `models/noti_embeddinggemma_actionability_v1/golden_test_cases.json`
- `models/noti_embeddinggemma_actionability_v1/README.md`

모델 파일은 314,284,128 bytes이며 SHA-256은
`122f6463c72d6a80e9ee5825782c78910342392f6e257f59921fff3b032b3cb3`이다.

## 입출력 계약

| Signature 이름 | 의미 | dtype | shape |
| --- | --- | --- | --- |
| `args_0` | `input_ids` | int64 | `[1, 64]` |
| `args_1` | `attention_mask` | int64 | `[1, 64]` |
| `output_0` | Actionability 확률 | float32 | `[1, 3]` |

출력 순서는 고정이다.

1. `GENERAL`
2. `ATTENTION_WORTHY`
3. `ACTION_REQUIRED`

출력에는 Softmax가 포함돼 있으므로 Android에서 다시 Softmax를 적용하지 않는다.

## 문자열과 토큰 계약

1. Kotlin `ImportanceTextPreprocessor`로 제목과 본문을 정규화한다.
2. 정규화된 문자열 앞에 `task: classification | query: `를 붙인다.
3. 제공된 EmbeddingGemma tokenizer로 Token ID를 만든다.
4. 최대 64 token에서 자르고 오른쪽을 `pad_token_id=0`으로 채운다.
5. 실제 token은 `attention_mask=1`, padding은 `attention_mask=0`으로 만든다.

특수 Token ID는 다음과 같다.

- PAD: `0`
- EOS: `1`
- BOS: `2`

Android tokenizer 구현은 반드시 `golden_test_cases.json`의 64개 `input_ids` 및
`attention_mask`와 완전히 같은지 단위 테스트해야 한다. 확률 비교 전에 Token ID가
하나라도 다르면 모델 문제가 아니라 tokenizer 계약 불일치로 본다.

## 품질 검증

기존의 `EmbeddingGemma INT8 encoder -> sklearn MLP` 분리 파이프라인과 최종 단일
TFLite를 실제 알림 145개에서 비교했다.

- 최종 예측 불일치: `0/145`
- 확률 최대 절대 오차: `0.0093475`
- 확률 평균 절대 오차: `0.0005551`

잘못된 광고 라벨 두 건을 수정한 기존 Room 100개 결과:

- Accuracy: `94.0%`
- 중요 Precision: `0.500`
- 중요 Recall: `1.000`
- 중요 F1: `0.667`
- FP: `6`
- FN: `0`

시간상 독립된 새 Room 45개 블라인드 결과:

- Accuracy: `93.3%`
- 중요 Precision: `0.833`
- 중요 Recall: `0.714`
- 중요 F1: `0.769`
- FP: `1`
- FN: `2`

합계 145개 참고 결과:

- Accuracy: `93.8%`
- 중요 Precision: `0.611`
- 중요 Recall: `0.846`
- 중요 F1: `0.710`
- FP: `7`
- FN: `2`

145개 합계는 서로 평가 설계가 다른 두 세트를 합친 참고값이며, 주 결과는 새 45개
블라인드 평가다.

## 에뮬레이터 최종 모델 Benchmark

- 기기: ARM64 Android 17 emulator
- Runtime: LiteRT `benchmark_model`, CPU XNNPACK
- 조건: 3 trial, trial별 50회, warm-up 3회
- 평균 추론 시간 중앙값: `36.79 ms`
- 초기화 중앙값: `80.12 ms`
- Init footprint 중앙값: `233.66 MB`
- Overall footprint 중앙값: `238.66 MB`

엄마 폰은 최종 Benchmark 직전에 ADB 연결이 해제돼 단일 모델 실기기 수치는 아직
추가하지 못했다. 기존 encoder-only SM-S711N 수치는 평균 `58.41 ms`, Overall
footprint `263.89 MB`였다. 폰을 다시 연결하면 최종 단일 모델로 다시 측정한다.

## Android 적용 순서

1. 모델과 tokenizer 배포 방식을 결정한다.
2. Kotlin tokenizer를 구현하거나 지원 Runtime을 선택한다.
3. `golden_test_cases.json`으로 전처리와 Token ID 계약을 단위 테스트한다.
4. LiteRT에서 `serving_default` signature를 호출한다.
5. 처음에는 결과와 추론 시간만 Room에 저장하는 shadow mode로 연결한다.
6. 모델 실패 시 기존 Kotlin 규칙 결과를 그대로 유지한다.
7. 실사용 데이터가 충분히 쌓인 뒤에만 최대 ±15점 보조 점수를 활성화한다.

약 300 MiB 모델과 약 37 MiB tokenizer 전체를 기본 APK assets에 포함하면 설치
용량이 크게 증가한다. 최초 기능 활성화 시 다운로드하고 앱 내부 저장소에서 SHA-256을
검증하는 방식도 함께 검토해야 한다.
