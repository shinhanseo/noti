# KoELECTRA v0.5 4-Class Actionability 교차검증

## 출력 계약

```text
0 PROMOTIONAL
1 INFORMATIONAL
2 ATTENTION_WORTHY
3 ACTION_REQUIRED
```

`important_probability = P(ATTENTION_WORTHY) + P(ACTION_REQUIRED)`로 계산한다.

## Fold별 결과

| Fold | Rows | 4-class Acc | Macro F1 | Binary threshold | Binary P | Binary R |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 118 | 0.763 | 0.600 | 0.645 | 0.938 | 0.938 |
| 1 | 122 | 0.697 | 0.570 | 0.554 | 0.905 | 0.919 |
| 2 | 120 | 0.650 | 0.539 | 0.647 | 0.966 | 0.903 |
| 3 | 120 | 0.450 | 0.343 | 0.586 | 0.690 | 0.909 |
| 4 | 120 | 0.600 | 0.393 | 0.547 | 0.941 | 0.970 |

## 전체 OOF 결과

- Fold 평균 4-class Accuracy: 0.632 ± 0.106
- Fold 평균 Macro F1: 0.489 ± 0.102
- Pooled 4-class Accuracy: 0.632
- Pooled Macro F1: 0.497
- 공통 중요 확률 임계값: 0.595726
- 공통 임계값 Binary Accuracy: 0.860
- 공통 임계값 Binary Precision: 0.845
- 공통 임계값 Binary Recall: 0.903
- 공통 임계값 FP/FN: 53/31

## 클래스별 OOF 결과

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| PROMOTIONAL | 0.657 | 0.783 | 0.714 | 198 |
| INFORMATIONAL | 0.000 | 0.000 | 0.000 | 82 |
| ATTENTION_WORTHY | 0.664 | 0.500 | 0.570 | 142 |
| ACTION_REQUIRED | 0.595 | 0.860 | 0.703 | 178 |

## 제한

- 데이터는 합성 중심이므로 실제 알림 일반화 성능이 아니다.
- 4-class 성능과 중요/일반 합산 성능을 함께 통과해야 Android에 반영한다.
- 기존 Room 12개는 데이터 설계에 참고했으므로 독립 테스트로 사용하지 않는다.
- 개인 선호는 이 공통 모델의 정답이 아니라 Android 보정 계층에서 처리한다.
