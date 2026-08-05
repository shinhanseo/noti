# noti. ML Lab

`noti.`의 알림 중요도 분류 모델을 학습하고 평가하는 Python 실험 공간이다.

Android 앱 코드는 루트의 `app/`에서 관리하고, 머신러닝 코드는 이 `ml/` 폴더에서 관리한다.

## 진행 순서

1. v0.1 합성 알림으로 학습 파이프라인 검증
2. 실제 모델 실행 구간에 맞춘 v0.2 데이터셋 설계
3. v0.2 데이터 생성과 품질 검사
4. 제목과 본문을 문자 n-gram TF-IDF로 변환
5. Logistic Regression 학습
6. REVIEW 구간 성능과 오분류 분석
7. 실제 익명화 알림으로 그림자 모드 검증
8. Android 적용용 모델 변환 검토

v0.2의 라벨 정책과 스키마는 [`docs/dataset-v0.2-design.md`](docs/dataset-v0.2-design.md)에 정리한다.

## v0.2 데이터 생성과 검사

```bash
python src/generate_dataset_v02.py
python src/validate_dataset_v02.py
python src/train_baseline.py
python src/analyze_baseline_errors.py
python src/evaluate_stability.py
python src/train_final_model.py
python src/verify_portable_model.py
python src/compare_lightweight_models.py
python src/train_selected_model.py
python src/verify_selected_portable_model.py
```

생성 파일:

- `data/public/train_notifications_v0.2.csv`: 라벨이 있는 학습·대조 데이터 320개
- `data/public/context_notifications_v0.2.csv`: 정답을 강제하지 않는 문맥 의존 데이터 80개

검토용 워크북은 `reports/outputs/v0.2/dataset_v0.2_review.xlsx`에 생성되어 있다. 원본 CSV가 학습 데이터의 기준이다.

`train_baseline.py`는 `clarity=CLEAR`이면서 `model_eligible=true`인 REVIEW 데이터만 사용하고, 같은 `template_group`이 학습과 평가에 겹치지 않는 5-Fold 교차 검증을 수행한다.

`analyze_baseline_errors.py`는 동일한 교차 검증의 오분류를 Fold, 문장 템플릿, 알림 유형, 앱별로 분해하고 `reports/v0.2_error_analysis.md`를 생성한다.

`evaluate_stability.py`는 같은 모델을 20개의 `random_state`로 반복 평가하고 `reports/v0.2_stability_evaluation.md`를 생성한다. 현재 평균 정확도는 91.7%, 반복별 표준편차는 0.026, 범위는 83.3%~95.0%다.

`train_final_model.py`는 REVIEW 학습 대상 240개 전체로 최종 기준 모델을 학습하고 `models/`에 Python용 `joblib`, 구현 중립적인 가중치 JSON, 메타데이터와 기준 예측값을 저장한다. 저장된 모델은 다음처럼 확인할 수 있다.

```bash
python src/predict_notification.py \
  --title "결제 상태 안내" \
  --body "자동이체 처리 중 문제가 발생했습니다."
```

`compare_lightweight_models.py`는 동일한 반복 Group 교차 검증으로 다섯 경량 후보를 비교한다. 현재 합성 v0.2 데이터에서는 Char TF-IDF + 32-unit MLP가 평균 정확도 94.5%, 평균 Recall 95.2%로 임시 1위다. `train_selected_model.py`가 이 모델을 전체 데이터로 학습해 저장하며, 상세 판단과 한계는 `reports/v0.2_model_selection.md`에 기록한다.

일정형 문장을 중요·일반 라벨별 2개에서 5개 구조로 확장한 뒤, 동일한 모델의 정확도는 76.7%에서 87.9%로 상승했고 오분류는 56개에서 29개로 감소했다. 합성 데이터 안에서의 비교 결과이므로 실제 알림에 대한 성능으로 해석하지 않는다.

## 예정 구조

```text
ml/
├── data/
│   ├── public/
│   └── private/
├── src/
├── models/
├── reports/
├── requirements.txt
└── README.md
```

실제 알림 원문과 개인 데이터는 `data/private/`에만 보관하며 Git에 커밋하지 않는다.
