# KoELECTRA v0.5 3-Tier Actionability 교차검증

## 출력 계약

```text
0 GENERAL
1 ATTENTION_WORTHY
2 ACTION_REQUIRED
```

`important_probability = P(ATTENTION_WORTHY) + P(ACTION_REQUIRED)`로 계산한다.

## Fold별 결과

| Fold | Rows | 3-tier Acc | Macro F1 | Binary threshold | Binary P | Binary R |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 118 | 0.898 | 0.900 | 0.958 | 0.983 | 0.906 |
| 1 | 122 | 0.705 | 0.606 | 0.300 | 0.939 | 1.000 |
| 2 | 120 | 0.917 | 0.905 | 0.877 | 1.000 | 0.903 |
| 3 | 120 | 0.842 | 0.856 | 0.942 | 0.984 | 0.924 |
| 4 | 120 | 0.958 | 0.953 | 0.938 | 1.000 | 0.909 |

## 전체 OOF 결과

- Fold 평균 3-tier Accuracy: 0.864 ± 0.088
- Fold 평균 Macro F1: 0.844 ± 0.123
- Pooled 3-tier Accuracy: 0.863
- Pooled Macro F1: 0.859
- 공통 중요 확률 임계값: 0.753454
- 공통 임계값 Binary Accuracy: 0.915
- 공통 임계값 Binary Precision: 0.927
- 공통 임계값 Binary Recall: 0.912
- 공통 임계값 FP/FN: 23/28

## 클래스별 OOF 결과

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| GENERAL | 0.901 | 0.875 | 0.888 | 280 |
| ATTENTION_WORTHY | 0.813 | 0.951 | 0.877 | 142 |
| ACTION_REQUIRED | 0.852 | 0.775 | 0.812 | 178 |

## 제한

- 데이터는 합성 중심이므로 실제 알림 일반화 성능이 아니다.
- 3-tier 성능과 중요/일반 합산 성능을 함께 통과해야 Android에 반영한다.
- 기존 Room 12개는 데이터 설계에 참고했으므로 독립 테스트로 사용하지 않는다.
- 개인 선호는 이 공통 모델의 정답이 아니라 Android 보정 계층에서 처리한다.
