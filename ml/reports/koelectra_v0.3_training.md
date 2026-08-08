# KoELECTRA-small-v3 알림 중요도 1차 학습

## 공통 조건

- 데이터: v0.3 모델 학습 대상 400개
- 입력: `title + body`
- 최대 길이: 64 tokens
- 분리: `StratifiedGroupKFold`의 첫 fold
- 학습: 308개
- 검증: 92개
- `template_group` 중복: 0개
- 배포 변환: TensorFlow → TFLite builtin ops

## 실험 비교

| 실험 | 검증 기준 | Accuracy | Precision | Recall | F1 | FP | FN |
|---|---|---:|---:|---:|---:|---:|---:|
| Encoder 전체 고정 | threshold 0.5 | 50.0% | 0.465 | 1.000 | 0.635 | 46 | 0 |
| Encoder 전체 고정 | Recall 90% threshold | 63.0% | 0.545 | 0.900 | 0.679 | 30 | 4 |
| 상위 2-layer 미세조정 | threshold 0.5 | 58.7% | 0.513 | 1.000 | 0.678 | 38 | 0 |
| 상위 2-layer 미세조정 | Recall 90% threshold | 87.0% | 0.818 | 0.900 | 0.857 | 8 | 4 |

상위 2개 transformer layer를 푼 실험이 합성 검증 fold에서는 크게 개선됐다. 선택된
Recall 중심 threshold는 `0.7543189`다.

## 변환 결과

- FP32 TFLite 크기: 56,407,808 bytes(약 53.79 MiB)
- TensorFlow와 TFLite 최대 logits 차이: `2.384e-7`
- 변환 결과의 수치 일치: 통과

## 실제 Room 알림 12개 평가

- 일반 라벨: 11개
- 중요 라벨: 1개
- Accuracy: 91.7%
- Precision: 0
- Recall: 0
- FP: 0
- FN: 1
- Mac CPU median latency: 3.40ms

모델은 일반 알림 11개를 모두 일반으로 판단했지만 유일한 중요 알림인 `배송 출발`을
놓쳤다. 배송 알림의 중요 확률은 약 `0.459`로, 일반 알림 다수보다도 낮았다. 따라서
threshold만 낮춰 해결할 수 있는 문제가 아니며 현재 모델을 Android 중요도 점수에
연결하면 안 된다.

## 판단

학습부터 TFLite 변환, 로컬 실제 추론까지 전체 기술 파이프라인은 성공했다. 반면 실제
성능은 아직 배포 기준을 충족하지 못했다. 모델 구조나 변환보다 실제 알림 학습 데이터
부족과 합성 데이터의 문장 분포 차이가 현재의 우선 문제다.

다음 단계는 모델 복잡도를 더 올리는 것이 아니라 실제 REVIEW 알림과 사용자 라벨을
더 확보하고, 특히 배송·결제 실패·일정 변경 같은 실제 중요 문장 변형을 학습 데이터에
반영한 뒤 동일한 실제 holdout을 다시 평가하는 것이다.
