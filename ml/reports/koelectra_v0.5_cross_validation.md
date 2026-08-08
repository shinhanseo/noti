# KoELECTRA v0.5 고정 5-Fold 교차검증

## 실험 조건

- 학습 가능 데이터: 600개
- 같은 `template_group`은 하나의 fold에만 배치
- 각 fold마다 나머지 4개 fold로 학습하고 보지 않은 1개 fold를 평가
- 모델: `monologg/koelectra-small-v3-discriminator`
- 분류 헤드 3 epoch + 상위 encoder 2개 layer 6 epoch 미세조정

## Fold별 결과

| Fold | Rows | Threshold | Accuracy | Precision | Recall | F1 | FP | FN |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 118 | 0.858 | 0.949 | 0.939 | 0.969 | 0.954 | 4 | 2 |
| 1 | 122 | 0.392 | 0.959 | 0.938 | 0.984 | 0.961 | 4 | 1 |
| 2 | 120 | 0.814 | 0.950 | 1.000 | 0.903 | 0.949 | 0 | 6 |
| 3 | 120 | 0.731 | 0.800 | 0.762 | 0.924 | 0.836 | 19 | 5 |
| 4 | 120 | 0.701 | 0.950 | 1.000 | 0.909 | 0.952 | 0 | 6 |

## 요약

- Fold 평균 Accuracy: 0.922 (표준편차 0.061)
- Fold 평균 Precision: 0.928
- Fold 평균 Recall: 0.938
- Fold 평균 F1: 0.930
- OOF 공통 임계값: 0.658784
- 공통 임계값 OOF Accuracy: 0.875
- 공통 임계값 OOF Precision: 0.864
- 공통 임계값 OOF Recall: 0.909
- 공통 임계값 OOF F1: 0.886
- 공통 임계값 오탐/미탐: FP 46, FN 29

## 오분류 집중 유형

- `SURVEY`: 16개
- `GENERAL_INFORMATION`: 15개
- `PROCESS_FAILURE`: 10개
- `USER_ACTION`: 9개
- `PROMOTION`: 8개
- `SCHEDULE_CHANGE`: 7개
- `OPTIONAL_CONTENT`: 7개
- `ADDRESS_ACTION`: 2개
- `DELIVERY_STATUS`: 1개

## 해석과 제한

- Fold 3 Accuracy가 0.800으로 다른 fold보다 크게 낮아 문장군에 따른 편차가 여전히 크다.
- 각 fold가 고른 임계값도 0.392~0.858로 달라 확률 보정이 안정적이지 않다.
- 합성 중심 데이터의 교차검증 결과이므로 실제 사용자 알림 성능으로 해석하지 않는다.
- 최종 모델의 임계값은 모든 OOF 예측을 합쳐 Recall 0.9 이상 조건으로 정한 값이다.
- Android 연결 전 새 사용자·새 시점에서 모은 미사용 실제 알림 평가가 필요하다.
