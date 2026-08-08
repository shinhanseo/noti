# KoELECTRA v0.5 학습 및 TFLite 변환 결과

## 결론

고정 5-Fold 교차검증과 600개 전체 데이터 최종 학습, TFLite 변환까지 완료했다.
기술적으로 Android에 포함할 수 있는 모델 파일은 만들어졌지만, 실제 알림에서 오탐이
많고 독립 실제 테스트가 없으므로 아직 앱 중요도 점수에는 연결하지 않는다.

## 교차검증

- Fold 평균 Accuracy: 0.922 ± 0.061
- Fold 평균 Precision: 0.928
- Fold 평균 Recall: 0.938
- Fold 평균 F1: 0.930
- Fold별 Accuracy 범위: 0.800~0.959
- Fold별 선택 임계값 범위: 0.392~0.858

모든 out-of-fold 예측을 합쳐 Recall 0.9 이상 조건으로 고른 공통 임계값은
`0.6587844491`이다. 이 임계값에서 Accuracy 0.875, Precision 0.864,
Recall 0.909, F1 0.886이며 FP 46개, FN 29개다.

Fold 3의 Accuracy가 0.800까지 낮아졌고 임계값 범위도 넓다. 합성 문장군에 따른
편차와 확률 보정 문제가 남아 있다. 세부 표는
`reports/koelectra_v0.5_cross_validation.md`에 있다.

## 최종 모델

- 원본: `monologg/koelectra-small-v3-discriminator`
- 학습 행: 600개 (`label 0=280`, `label 1=320`)
- 분류 헤드: encoder 고정 3 epoch
- 미세조정: 상위 encoder 2개 layer 6 epoch
- 최종 학습 정확도: 0.968 (학습 데이터 값이며 일반화 성능이 아님)
- TFLite FP32 크기: 56,407,808 bytes (약 53.8 MiB)
- TensorFlow/TFLite 최대 logit 차이: `2.38e-7`
- 임계값: `0.6587844491` (pooled OOF에서 선택)

로컬 모델 산출물은 `models/koelectra_tensorflow_v0.5_final/`에 저장하며 Git에는
포함하지 않는다.

## 실제 Room 개발 세트

기존 실제 알림 12개에는 사용자 중요 1개, 일반 11개가 있다. v0.5는 중요한 배송
출발을 잡아 Recall 1.0이었지만 일반 7개를 중요로 잘못 올려 Precision 0.125,
Accuracy 0.417이었다. 특히 MMS 형식의 정치·홍보 메시지와 완료된 입금 알림을
공통 중요 후보로 과도하게 올렸다.

이 12개는 v0.5 문장군 설계에 참고했으므로 독립적인 최종 평가가 아니다. 한 사용자의
개인 선호도 공통 행동 필요성 정답과 다르다. 따라서 이 결과는 문제 발견용으로만
사용한다.

## 다음 통과 조건

1. 새 시점 또는 새 사용자에서 실제 REVIEW 알림을 별도로 수집한다.
2. 공통 `actionability`와 개인 `user_label`을 나눠 검수한다.
3. 새 실제 홀드아웃에서 Recall뿐 아니라 오탐과 유형별 오류를 확인한다.
4. 기준을 통과한 뒤 Android에 그림자 모드로 연결한다.
5. 실제 Android 기기에서 지연 시간, 메모리, CPU, 배터리를 측정한다.
