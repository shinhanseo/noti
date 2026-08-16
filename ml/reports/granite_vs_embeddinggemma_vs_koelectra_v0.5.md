# Granite 97M R2, EmbeddingGemma 300M, KoELECTRA 비교

## 결론

Granite 97M R2는 EmbeddingGemma보다 약 5.8배 작은 로컬 스냅샷과 약 2.4배 빠른
Mac CPU 추론을 보였다. 그러나 실제 Room 홀드아웃에서는 중요한 알림을 과도하게
`GENERAL`로 내려 현재 noti 모델로는 채택하지 않는다.

## 동일 조건 비교

모든 Embedding 실험은 Android v2 전처리, v0.5 학습 데이터 600개, 고정 5-Fold,
32-unit MLP를 사용했다. 실제 6개를 보기 전에 교차검증 Macro F1로 Head를 선택했다.

| 모델 | 3단계 CV Accuracy | 이진 CV Accuracy(0.5) | 실제 6개 Accuracy(0.5) | 공통 Actionability | 앱 전체 | 로컬 크기 | Mac median |
|---|---:|---:|---:|---:|---:|---:|---:|
| KoELECTRA | 0.863 | 0.915* | 0.833 | 0.667 | 4/6 | 14.0 MiB | 3.67 ms |
| EmbeddingGemma + MLP | 0.952 | 0.973 | 0.667 | 0.667 | 3/6 | 1210.8 MiB | 22.35 ms |
| Granite 97M R2 + MLP | 0.943 | 0.995 | 0.500 | 0.500 | 3/6 | 210.0 MiB | 9.35 ms |

`*` KoELECTRA 이진 CV는 기존 선택 임계값 `0.753` 결과이며 나머지 0.5 열과 완전히
같은 임계값 비교는 아니다.

Granite의 Logistic Regression도 실제 Accuracy 0.500으로 MLP와 같았다.

## Granite 실제 오분류

Granite + MLP는 광고 2개를 모두 일반으로 맞혔지만 중요한 4개 중 현대카드
자동납부만 중요 후보로 잡았다.

| 알림 | 사용자 선호 | 중요 확률 | 예측 |
|---|---|---:|---|
| 올웨이즈 | GENERAL | 0.097 | GENERAL |
| 로젠택배 | IMPORTANT | 0.139 | GENERAL |
| CJ대한통운 | IMPORTANT | 0.012 | GENERAL |
| 웰컴저축은행 입금 | IMPORTANT | 0.078 | GENERAL |
| 컬리 쿠폰 | GENERAL | 0.000 | GENERAL |
| 현대카드 자동납부 | IMPORTANT | 0.694 | ATTENTION_WORTHY |

임계값을 낮추는 것만으로는 입금·배송 세 건을 안전하게 복구하기 어렵다. 합성
교차검증이 99.5%인데 실제 Recall이 25%라는 차이는 현재 합성 데이터의 표현과 실제
삼성 MMS가 충분히 닮지 않았음을 보여준다.

## 판단

- 경량성과 속도: Granite가 EmbeddingGemma보다 확실히 우수하다.
- 합성 데이터 분리: Granite도 매우 높다.
- 현재 실제 알림 일반화: KoELECTRA와 EmbeddingGemma보다 낮다.
- Android 적용: 아직 TFLite/LiteRT 변환 전이므로 210 MiB는 최종 앱 크기가 아니다.

Granite를 버릴 필요는 없지만, 모델을 더 바꾸는 것보다 실제 알림 라벨을 늘리고
실제 삼성 MMS 형식의 학습 예시를 보강한 뒤 다시 비교하는 것이 우선이다.
