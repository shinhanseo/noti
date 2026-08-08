# KoELECTRA-small-v3 LiteRT 변환 사전 검사

## 목적

알림 중요도 학습을 시작하기 전에 `monologg/koelectra-small-v3-discriminator`가
LiteRT/TFLite 변환 파이프라인에 들어갈 수 있는 구조인지 확인한다. 현재 분류 헤드는
임의 초기화 상태이므로 이 결과는 정확도 실험이 아니다.

## 로컬 검사 결과

- 실행 환경: macOS arm64, Python 3.12.13
- 모델 파라미터: 14,122,498개
- FP32 파라미터 메모리: 53.87 MiB
- Vocabulary: 35,000개
- 고정 입력 길이: 64 tokens
- 입력: `input_ids`, `attention_mask`, `token_type_ids`
- 입력 shape: 각 `[1, 64]`
- 입력 dtype: 각 `int32`
- PyTorch forward: 성공
- `torch.export`: 성공

## Linux 변환 결과

두 개의 독립 경로를 Colab Linux CPU에서 검사했다.

### PyTorch → LiteRT Torch

- `.tflite` 생성: 성공
- SDPA 모델 크기: 33.92 MiB
- SDPA 최대 logits 차이: 0.04468385
- Eager attention 모델 크기: 31.38 MiB
- Eager attention 최대 logits 차이: 0.06177248
- Eager attention 최대 확률 차이: 0.02361432
- 원본 PyTorch와 `torch.export` logits 차이: 0
- 변환 전후 원본 PyTorch logits 차이: 0

파일은 생성됐지만 LiteRT lowering 이후에만 의미 있는 수치 오차가 발생했다. 현재
LiteRT Torch 직행 경로는 noti.의 중요도 분류 모델 배포 경로로 채택하지 않는다.

### PyTorch checkpoint → TensorFlow → TFLite Converter

- `.tflite` 생성: 성공
- TensorFlow: 2.20.0
- FP32 모델 크기: 56,406,552 bytes(약 53.79 MiB)
- TensorFlow와 TFLite 최대 logits 차이: 0.000000026077
- 최대 확률 차이: 0
- TFLite builtin ops만 사용한 변환: 성공

## 결론

KoELECTRA-small-v3의 TFLite 배포 가능성을 확인했다. 현재 검증된 변환 경로는
`PyTorch checkpoint → TensorFlow model → TFLite Converter`다. 이 결과물의 분류
헤드는 아직 임의 초기화 상태이므로 알림 중요도 모델은 아니며, 다음 단계에서 동일한
TensorFlow 구조를 v0.3 데이터로 학습한 후 다시 변환·수치 검증해야 한다.

FP32 파일은 약 53.79 MiB이므로 최종 배포 판단 전 FP16과 INT8 양자화, 실제 정확도,
Galaxy S23 FE의 지연 시간과 메모리 측정이 필요하다.
