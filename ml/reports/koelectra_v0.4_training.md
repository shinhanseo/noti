# KoELECTRA-small-v3 v0.4 학습 결과

## 조건

- 전체 v0.4 데이터: 520개
- 규칙 점수 REVIEW이며 학습 가능한 데이터: 440개
- 입력: `title + body`
- 최대 길이: 64 tokens
- 분리: `StratifiedGroupKFold` 첫 fold
- 학습: 346개
- 검증: 94개
- `template_group` 중복: 0개
- 학습: 분류 헤드 3 epochs + 상위 2개 encoder layer 6 epochs
- 배포 변환: TensorFlow → TFLite builtin ops

## 검증 결과

Recall 90% 이상을 만족하면서 precision이 가장 높은 임계값은 `0.5159286`이었다.

| 기준 | Accuracy | Precision | Recall | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| threshold 0.5 | 76.6% | 0.577 | 1.000 | 0.732 | 22 | 0 |
| Recall 중심 threshold | 76.6% | 0.577 | 1.000 | 0.732 | 22 | 0 |

검증 fold에서 `ACTION_REQUIRED` 2개와 `ATTENTION_WORTHY` 28개는 모두 잡았다. 반면 프로모션 62개 중 22개를 중요 후보로 잘못 올렸다. 주요 오류는 동일 템플릿 계열의 설문 20개와 선택형 이벤트 2개였다.

## 검증 분할의 한계

첫 fold의 구성은 다음처럼 불균형했다.

| Actionability | 행 수 |
|---|---:|
| `ACTION_REQUIRED` | 2 |
| `ATTENTION_WORTHY` | 28 |
| `INFORMATIONAL` | 2 |
| `PROMOTIONAL` | 62 |

라벨은 stratify했지만 큰 `template_group` 단위로 분리하면서 세부 유형이 한 fold에 치우쳤다. 정상 배송과 완료 금융 상태 템플릿은 이 validation fold에 포함되지 않았다. 따라서 현재 한 번의 76.6%를 v0.4 전체 성능으로 해석할 수 없으며, 다음 실험은 여러 fold와 이벤트 유형까지 고려해야 한다.

## TFLite 변환

- FP32 TFLite 크기: 56,407,808 bytes(약 53.79 MiB)
- TensorFlow와 TFLite 최대 logits 차이: `5.960e-7`
- 변환 수치 일치: 통과

## v0.3과의 비교

| 데이터 | Accuracy | Precision | Recall | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| v0.3 첫 fold | 87.0% | 0.818 | 0.900 | 0.857 | 8 | 4 |
| v0.4 첫 fold | 76.6% | 0.577 | 1.000 | 0.732 | 22 | 0 |

두 실험은 라벨 정의와 validation fold 구성이 달라 직접적인 순위 비교가 아니다. v0.4는 중요 후보 누락을 줄였지만 프로모션 오탐이 크게 늘었다.

## 실제 Room 그림자 평가

- 실제 사용자 라벨: 중요 1개, 일반 11개
- 배송 출발 중요 확률: 약 `0.447`
- Accuracy: 50.0%
- Precision: 0
- Recall: 0
- FP: 5
- FN: 1

v0.3에서 놓쳤던 배송 출발을 v0.4도 잡지 못했다. 중요 예측 5개 중 하나는 완료된 금융 상태로 v0.4 공통 정책에서는 `ATTENTION_WORTHY`지만 이 사용자는 일반으로 표시한 개인차 사례다. 나머지 네 개는 선택적 메시지·프로모션 계열로 공통 모델에서도 오탐에 가깝다.

이 12개는 v0.4 결과를 확인하는 과정에서 문장을 확인했으므로 이후 데이터 개선에 사용하면 더 이상 독립 holdout으로 볼 수 없다.

## 결론

v0.4는 `ACTION_REQUIRED`와 `ATTENTION_WORTHY`를 분리하고 TFLite까지 학습하는 파이프라인을 완성했다. 그러나 현재 모델은 배송 표현 일반화에 실패했고 설문·선택형 메시지 오탐이 많으므로 Android 점수에 연결하지 않는다.

다음 우선순위는 모델 크기를 키우는 것이 아니다.

1. 이벤트 유형이 각 fold에 고르게 들어가는 반복 group 교차검증을 만든다.
2. 실제 한국 배송 문장 구조와 SMS·MMS 프로모션 표현을 독립적인 합성 템플릿으로 늘린다.
3. 기존 12개는 개발 세트로 전환하고 새 실사용 알림을 최종 holdout으로 확보한다.
4. 개선 데이터로 다시 학습한 뒤 새 holdout과 Android 실기기에서 평가한다.
