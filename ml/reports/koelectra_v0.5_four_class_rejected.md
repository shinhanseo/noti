# KoELECTRA v0.5 4-Class 실험 — 기각

## 시도한 출력

```text
PROMOTIONAL
INFORMATIONAL
ATTENTION_WORTHY
ACTION_REQUIRED
```

v0.5 학습 가능 데이터 600개와 고정 5-Fold를 사용했다. 분류 헤드 3 epoch,
상위 encoder 2개 layer 6 epoch를 학습한 첫 실험 결과는 다음과 같다.

- Fold 평균 4-class Accuracy: 0.632 ± 0.106
- Fold 평균 Macro F1: 0.489 ± 0.102
- Pooled 4-class Accuracy: 0.632
- Pooled Macro F1: 0.497
- `INFORMATIONAL` Recall: 0.000 (82개 중 0개 정분류)
- 중요 확률 합산 Binary Accuracy: 0.860
- 중요 확률 합산 Binary Precision: 0.845
- 중요 확률 합산 Binary Recall: 0.903

역빈도 class weight를 적용한 fold 0도 `INFORMATIONAL` Recall이 0이었고 전체
Accuracy가 0.525로 하락했다. 상위 4개 layer를 12 epoch 학습하면 fold 0 Accuracy가
0.873까지 올랐지만 `INFORMATIONAL` Recall은 계속 0이었다.

## 기각 이유

현재 데이터에서 `INFORMATIONAL`과 `PROMOTIONAL`을 별도 softmax 클래스로 안정적으로
분리할 수 없다. 더 중요한 점은 제품의 규칙 엔진이 광고 신호를 이미 -35점으로
처리하므로 REVIEW 구간의 AI가 두 클래스를 반드시 구분할 필요가 없다는 것이다.

따라서 온디바이스 모델은 다음 3단계만 예측한다.

```text
GENERAL = PROMOTIONAL + INFORMATIONAL
ATTENTION_WORTHY
ACTION_REQUIRED
```

광고 여부의 설명과 감점은 규칙 엔진에 유지하고, AI는 애매한 알림이 일반인지,
확인 가치가 있는지, 행동이 필요한지만 보조 판단한다.
