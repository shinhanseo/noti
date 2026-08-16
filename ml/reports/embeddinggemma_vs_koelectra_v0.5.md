# EmbeddingGemma 300M과 KoELECTRA v0.5 비교

## 결론부터

EmbeddingGemma는 합성 중심 교차검증에서는 KoELECTRA보다 높았지만, 실제 알림
6개에서는 더 좋다고 결론 내릴 수 없었다. 현재 상태로 Android 모델을 교체하지
않는다.

## 같은 600개 고정 5-Fold 비교

| 모델 | 구조 | 3단계 Accuracy | Macro F1 | 이진 Accuracy | Precision | Recall |
|---|---|---:|---:|---:|---:|---:|
| KoELECTRA-small-v3 | 상위 encoder fine-tuning | 0.863 | 0.859 | 0.915 | 0.927 | 0.913 |
| EmbeddingGemma 300M | 고정 embedding + Logistic Regression | 0.947 | 0.939 | 0.967 | 0.969 | 0.969 |
| EmbeddingGemma 300M | 고정 embedding + 32-unit MLP | 0.952 | 0.945 | 0.947 | 1.000 | 0.900 |

이 데이터 안에서는 EmbeddingGemma의 의미 표현이 더 잘 분리됐다. 그러나 Fold별
3단계 Accuracy가 MLP 기준 `0.867~1.000`으로 흔들렸고 데이터가 합성 중심이므로,
실제 성능 향상을 증명하는 수치는 아니다.

## 실제 Room 독립 홀드아웃 6개

| 모델 | 개인 Accuracy | Precision | Recall | 공통 Actionability Accuracy |
|---|---:|---:|---:|---:|
| KoELECTRA + Android v2 입력 | 0.833 | 1.000 | 0.750 | 0.667 |
| EmbeddingGemma + Logistic Regression, 0.5 | 0.833 | 1.000 | 0.750 | 0.667 |
| EmbeddingGemma + 32-unit MLP, 0.5 | 0.667 | 1.000 | 0.500 | 0.667 |

실제 데이터에서는 EmbeddingGemma + Logistic Regression이 KoELECTRA와 동률이고,
교차검증 Macro F1로 미리 선택한 MLP는 오히려 낮았다. 6개뿐이라 순위를 확정할
수는 없지만, 최신 모델이라는 이유만으로 자동 개선되지는 않았다.

## 현재 앱 점수와 결합했을 때

선택된 MLP 확률을 기존 `-15~+15` 점수표에 그대로 넣으면 앱 전체 결과는 `3/6`이다.

- 배송 MMS 2개는 규칙 단계에서 `GENERAL 5`가 되어 AI가 실행되지 않는다.
- 입금 알림은 `ATTENTION_WORTHY`로 맞혔지만 중요 확률 `0.798`이 `+10`으로
  변환되어 `25 + 10 = REVIEW 35`에 머문다.
- 현대카드 자동납부만 `30 + 15 = IMPORTANT 45`가 된다.

KoELECTRA용으로 설계한 확률 구간을 EmbeddingGemma에 그대로 적용한 것도 문제다.
OOF 예측으로 Platt calibration을 적용해봤지만 실제 앱 결과는 `3/6`으로 개선되지
않았다. 새 모델을 채택하려면 모델별 확률 보정과 점수 매핑을 별도 검증해야 한다.

## 속도와 크기

| 모델 | 현재 아티팩트 | 크기 | 개발 Mac 단일 알림 지연 |
|---|---|---:|---:|
| KoELECTRA | 동적 범위 TFLite | 14.0 MiB | median 3.67 ms |
| EmbeddingGemma | Hugging Face FP32 원본 | 1210.8 MiB | median 22.35 ms |
| EmbeddingGemma 분류 Head | Joblib | 367 KiB | Embedding 이후는 매우 작음 |

형식과 정밀도가 달라 완전히 공정한 기기 비교는 아니다. EmbeddingGemma는 아직
LiteRT 양자화를 하지 않았으므로 Android 크기·RAM·배터리 결과는 알 수 없다.

## 다음 판단

EmbeddingGemma는 후보에서 탈락한 것은 아니다. 합성 교차검증의 큰 개선은 추가
검증 가치가 있다. 다만 지금 최우선은 변환이 아니라 실제 라벨 알림을 최소 수십
개로 늘리는 것이다. 새 실제 세트에서도 KoELECTRA를 안정적으로 이긴 뒤 LiteRT
변환과 실제 기기 측정으로 넘어간다.
