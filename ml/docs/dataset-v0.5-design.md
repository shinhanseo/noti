# noti. 알림 데이터셋 v0.5 설계

## 목표

v0.4 KoELECTRA는 첫 group holdout에서 Recall 1.0을 기록했지만 설문·선택형 이벤트를
중요 알림으로 올렸고, 실제 Room 개발 세트에서는 사용자가 중요하다고 표시한 배송
출발을 놓쳤다. v0.5의 목표는 이 실패 유형을 그대로 복사하는 것이 아니라 일반화한
문장군을 보강하고, 실행 환경에 따라 바뀌지 않는 고정 교차검증을 만드는 것이다.

공통 정답 정책은 v0.4를 유지한다.

| Actionability | 이진 라벨 | 의미 |
|---|---:|---|
| `ACTION_REQUIRED` | 1 | 사용자의 확인이나 행동이 필요함 |
| `ATTENTION_WORTHY` | 1 | 직접 행동은 없어도 먼저 확인할 가치가 있음 |
| `INFORMATIONAL` | 0 | 알아두면 되는 일반 정보 |
| `PROMOTIONAL` | 0 | 선택적 참여나 소비를 유도함 |

## 신규 문장 160개

실제 Room 원문은 학습 데이터로 복사하지 않았다. 관찰한 실패 유형을 바탕으로
프로젝트가 직접 작성하고 정책 검토한 한국어 알림 문장군을 추가했다.

| 문장군 | 수 | Actionability | 목적 |
|---|---:|---|---|
| 정상 배송 상태 | 32 | `ATTENTION_WORTHY` | 출고·이동·오늘 도착·수령 예정 표현 확장 |
| 완료된 결제 상태 | 16 | `ATTENTION_WORTHY` | 입금·이체·결제·환불 완료 표현 확장 |
| 일반 정보 | 32 | `INFORMATIONAL` | 요약·기록·일반 소식·읽기 전용 공유 대조군 |
| 행동 필요 | 32 | `ACTION_REQUIRED` | 실패·보안·마감·정보 입력·승인 요청 확장 |
| 광고성 위장 표현 | 48 | `PROMOTIONAL` | 투표·캠페인·MMS 만료·설문·초대·쿠폰 대조군 |

`SYNTHETIC_DIVERSITY_REVIEWED`, `POLICY_APPROVED_V05`로 출처와 검토 상태를
표시했다. 한 사용자의 개인 선호 라벨은 공통 모델의 정답으로 승격하지 않았다.

## 생성 결과

| 파일 | 행 수 | 용도 |
|---|---:|---|
| `train_notifications_v0.5.csv` | 680 | 공통 학습·대조 데이터 전체 |
| `context_notifications_v0.5.csv` | 80 | 공통 정답을 두지 않은 개인화 문맥 |
| `public_evaluation_v0.5.csv` | 0 | 공개 실데이터의 검토 전 입구 |
| `source_manifest_v0.5.csv` | 10 sources | 출처와 이용 상태 |

전체 680개 중 `clarity=CLEAR`, `model_eligible=true`,
`training_eligible=true` 조건을 통과한 600개만 모델 학습과 교차검증에 사용한다.

| Actionability | 전체 | 학습 가능 |
|---|---:|---:|
| `ACTION_REQUIRED` | 218 | 178 |
| `ATTENTION_WORTHY` | 142 | 142 |
| `INFORMATIONAL` | 102 | 82 |
| `PROMOTIONAL` | 218 | 198 |

학습 가능한 이진 라벨은 `1=320`, `0=280`이다.

## 고정 5-Fold

scikit-learn 버전에 따라 런타임 분할 결과가 달라지는 문제를 피하기 위해 각 행의
`cv_fold`를 CSV에 저장한다. 같은 `template_group`은 반드시 하나의 fold에만 속한다.

| Fold | 행 수 | ACTION_REQUIRED | ATTENTION_WORTHY | INFORMATIONAL | PROMOTIONAL |
|---:|---:|---:|---:|---:|---:|
| 0 | 118 | 36 | 28 | 14 | 40 |
| 1 | 122 | 36 | 26 | 20 | 40 |
| 2 | 120 | 34 | 28 | 20 | 38 |
| 3 | 120 | 36 | 30 | 14 | 40 |
| 4 | 120 | 36 | 30 | 14 | 40 |

분할은 모델 결과를 보고 수동으로 옮기지 않는다. 생성 스크립트가 group 단위로
배치하고 검사 스크립트가 group 누수와 분포를 확인한다.

```bash
python src/generate_dataset_v05.py
python src/validate_dataset_v05.py
```

## 평가 규칙

- 다섯 번 모두 해당 fold를 완전히 제외하고 학습한다.
- fold별 성능뿐 아니라 모든 out-of-fold 예측을 합친 공통 임계값 성능을 기록한다.
- 최종 모델은 교차검증이 끝난 뒤 600개 전체로 한 번만 학습한다.
- 기존 Room 12개는 실패 유형을 설계에 참고했으므로 독립 테스트가 아니라 개발 세트다.
- Android 중요도 점수 연결 전 새 사용자·새 시점의 미사용 실제 알림이 필요하다.

## 최종 모델 출력 계약

4개 원본 actionability를 그대로 분류한 실험은 `INFORMATIONAL` Recall이 0이어서
채택하지 않았다. 온디바이스 후보는 다음 3개 클래스를 예측한다.

| 모델 클래스 | 원본 데이터 |
|---|---|
| `GENERAL` | `PROMOTIONAL`, `INFORMATIONAL` |
| `ATTENTION_WORTHY` | `ATTENTION_WORTHY` |
| `ACTION_REQUIRED` | `ACTION_REQUIRED` |

기존 중요도 정책에 전달하는 값은
`P(ATTENTION_WORTHY) + P(ACTION_REQUIRED)`로 고정한다. 모델 버전이 달라져도
Android가 임의로 클래스 순서를 추측하지 않도록 label order와 확률 계산 규칙을
`model_contract.json`에 함께 저장한다.

결과는 `reports/koelectra_actionability_triage_v0.5_training.md`,
`reports/koelectra_actionability_triage_v0.5_cross_validation.md`,
`reports/v0.5_koelectra_actionability_room.md`에 기록한다.
