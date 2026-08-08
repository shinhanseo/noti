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

v0.2의 라벨 정책과 스키마는 [`docs/dataset-v0.2-design.md`](docs/dataset-v0.2-design.md)에 정리한다. 현실형 표현과 실데이터 반입 규칙은 [`docs/dataset-v0.3-design.md`](docs/dataset-v0.3-design.md)에 정리한다.

## v0.5 고정 5-Fold와 KoELECTRA 최종 실험

v0.5는 정상 배송, 완료된 결제, 일반 정보, 행동 필요, 광고성 위장 표현을 포함한
정책 검토 합성 문장 160개를 추가했다. 총 680개 중 600개를 학습에 사용하며,
`template_group`이 겹치지 않는 고정 `cv_fold`를 CSV에 저장한다. 상세 설계는
[`docs/dataset-v0.5-design.md`](docs/dataset-v0.5-design.md)에 있다.

```bash
python src/generate_dataset_v05.py
python src/validate_dataset_v05.py

# Linux/Colab에서 fold별 실행
python src/train_koelectra_tensorflow.py --fold-index 0 --skip-artifacts

# 내려받은 5개 fold report 집계
python src/analyze_koelectra_v05_cv.py

# 교차검증 뒤 전체 데이터 최종 학습과 TFLite export
python src/train_koelectra_final_tensorflow.py \
  --decision-threshold 0.6587844491004944
```

5-Fold 평균 Accuracy는 0.922, Recall은 0.938이지만 fold별 Accuracy가
0.800~0.959로 흔들렸다. 모든 OOF 예측에 공통 임계값을 적용하면 Accuracy 0.875,
Precision 0.864, Recall 0.909다. 최종 FP32 TFLite는 약 53.8 MiB이며 변환 전후
logit 최대 차이는 `2.38e-7`이다.

실제 Room 개발 세트에서는 중요한 배송을 잡았지만 일반 11개 중 7개를 중요로
잘못 올렸다. 이 Room 알림은 v0.5 설계에 참고했으므로 독립 테스트가 아니다.
새 실제 홀드아웃을 통과하기 전에는 Android 중요도 점수에 연결하지 않는다. 결과는
[`reports/koelectra_v0.5_training.md`](reports/koelectra_v0.5_training.md)와
[`reports/koelectra_v0.5_cross_validation.md`](reports/koelectra_v0.5_cross_validation.md)에 있다.

## v0.4 행동 필요성과 개인 선호 분리

v0.4부터 공통 KoELECTRA 모델이 학습할 `행동 필요성`과 Android에서 피드백으로
학습할 `사용자 선호`를 분리한다. 상세 정책은
[`docs/dataset-v0.4-design.md`](docs/dataset-v0.4-design.md)에 정리한다.

```bash
python src/generate_dataset_v04.py
python src/validate_dataset_v04.py
```

생성 파일:

- `data/public/train_notifications_v0.4.csv`: 공통 행동 필요성 데이터 520개
- `data/public/context_notifications_v0.4.csv`: 공통 정답을 두지 않은 개인화 문맥 80개
- `data/public/review_notifications_v0.4.csv`: 사람이 확인할 경계 사례 30개
- `data/public/public_evaluation_v0.4.csv`: 공개 실데이터의 검토 전 입구
- `data/public/source_manifest_v0.4.csv`: 출처와 이용 상태

검수용 워크북은 `reports/outputs/v0.4/dataset_v0.4_review.xlsx`에 있다. 노란색
`user_actionability`, `user_preference_sensitive`, `review_note` 열만 작성하면 된다.
검수 결과를 반영해 KoELECTRA 상위 2-layer를 다시 학습하고 TFLite로 변환했다.

```bash
# Linux/Colab 학습과 TFLite export
python src/train_koelectra_tensorflow.py

# 실제 알림 원문을 외부로 보내지 않는 로컬 평가
source .venv-embeddings/bin/activate
python src/evaluate_koelectra_real_room.py
```

첫 group fold에서 Recall은 100%였지만 Accuracy 76.6%, Precision 57.7%였고 설문과
선택형 이벤트 오탐이 22개 발생했다. 실제 Room 12개에서도 배송 출발을 놓치고
5개의 일반 알림을 중요 후보로 올렸으므로 Android 점수에는 아직 반영하지 않는다.
상세 결과와 다음 데이터 개선 방향은 `reports/koelectra_v0.4_training.md`에 있다.

## v0.3 현실형 데이터 초안

```bash
python src/generate_dataset_v03.py
python src/validate_dataset_v03.py
python src/train_baseline.py --dataset-version 0.3
python src/compare_lightweight_models.py --dataset-version 0.3
python src/evaluate_v03_source_holdout.py
```

생성 파일:

- `data/public/train_notifications_v0.3.csv`: v0.2 320개 + 현실형 신규 160개
- `data/public/context_notifications_v0.3.csv`: 문맥 의존 데이터 80개
- `data/public/public_evaluation_v0.3.csv`: 공개 실데이터를 라벨 없이 받을 입구
- `data/public/source_manifest_v0.3.csv`: 출처, 라이선스, 반입 상태

실제 Room CSV는 Git에 포함하지 않고 다음처럼 익명화한다.

```bash
python src/prepare_room_notifications_v03.py \
  data/private/room_notifications_raw.csv
```

공개 데이터와 Room 데이터는 처음부터 학습에 넣지 않는다. `UNLABELED` 상태로 반입한 뒤 importance-policy 기준의 사람 검토를 통과한 행만 `HUMAN_REVIEWED`로 승격한다.

v0.3 REVIEW 데이터 400개의 20회 Group 교차검증에서는 Char TF-IDF + 32-unit MLP가 평균 정확도 98.5%, Recall 99.4%로 가장 높았다. 고정 `multilingual-e5-small` Embedding + MLP는 평균 정확도 97.8%, Recall 97.9%였다. 사전학습 모델이 현재 합성 데이터에서 자동으로 더 좋은 결과를 내지는 않았다.

더 엄격한 출처 홀드아웃에서 v0.2 240개로 학습하고 현실형 신규 160개를 평가했을 때 Char TF-IDF + Logistic Regression, SGD, ComplementNB가 각각 정확도 96.9%, Recall 95.0%를 기록했다. 반대 방향은 80.8%~86.2%로 낮아 문장 스타일과 데이터 범위에 따른 비대칭이 확인됐다. 상세 결과는 `reports/v0.3_lightweight_model_bakeoff.md`, `reports/v0.3_pretrained_embedding_bakeoff.md`, `reports/v0.3_source_holdout.md`에 있다. 이 수치는 합성 중심 데이터 결과이며 실제 알림 성능이 아니다.

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
python src/compare_pretrained_embeddings.py
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

`compare_pretrained_embeddings.py`는 `multilingual-e5-small`, `paraphrase-multilingual-MiniLM-L12-v2`, `EmbeddingGemma 300M`의 고정 문장 Embedding 위에서 Logistic Regression과 32-unit MLP를 동일한 반복 Group 교차 검증으로 비교한다. 기존 Char TF-IDF + MLP도 같은 표에 기준선으로 포함한다. Transformer 계열 패키지가 Python 3.14를 아직 지원하지 않을 수 있으므로 Python 3.12 가상환경을 별도로 사용한다.

```bash
python3.12 -m venv .venv-embeddings
source .venv-embeddings/bin/activate
python -m pip install -r requirements-embeddings.txt

# 빠른 파이프라인 확인
python src/compare_pretrained_embeddings.py \
  --models multilingual_e5_small \
  --quick

# 전체 20회 비교. EmbeddingGemma는 Hugging Face 약관 동의가 필요할 수 있다.
python src/compare_pretrained_embeddings.py
```

임베딩은 `ml/.cache/pretrained_embeddings/`에 저장해 반복 실행 시간을 줄인다. 캐시는 로컬 실험 산출물이므로 Git에 포함하지 않는다. 이 실험의 Mac CPU 시간은 Android 성능이 아니며, 최종 후보는 INT8 LiteRT 변환 후 실제 기기에서 다시 측정해야 한다.

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

## KoELECTRA LiteRT 변환 가능성 검사

`KoELECTRA-small-v3`는 아직 최종 모델이 아니다. 먼저 임의로 초기화된 2-class
분류 헤드를 붙여 모델 구조가 LiteRT/TFLite로 변환되고, 변환 전후 logits가
일치하는지 확인한다. 이 단계에서는 알림 중요도 학습이나 정확도 평가를 하지 않는다.

모델 구조와 실제 파라미터 수, LiteRT Torch의 선행 조건인 `torch.export`
호환성은 기존 Python 3.12 임베딩 환경에서도 확인할 수 있다.

```bash
source .venv-embeddings/bin/activate
python src/probe_koelectra_litert.py --inspect-only
```

LiteRT Torch 변환은 Linux 환경을 기준으로 지원되므로 Google Colab 또는 별도의
Linux Python 3.11/3.12 환경에서 실행한다.

```bash
python3.11 -m venv .venv-litert
source .venv-litert/bin/activate
python -m pip install -r requirements-litert.txt
python src/probe_koelectra_litert.py
```

성공하면 `models/koelectra_litert_probe/` 아래에 다음 로컬 산출물이 생성된다.

- `koelectra_small_probe_fp32.tflite`
- `probe_report.json`
- Python/Android tokenizer 일치 검증에 사용할 tokenizer 파일

이 폴더는 모델 캐시 및 실험 산출물이므로 Git에는 포함하지 않는다. 변환에 성공한
경우에만 실제 v0.3 데이터 학습, 양자화, Android 통합 단계로 진행한다.

실제 검사에서는 LiteRT Torch 직행 변환이 파일 생성에는 성공했지만 변환 후 logits
오차가 크게 발생했다. 반면 독립적인 TensorFlow 경로는 TFLite builtin ops만으로
변환됐고 TensorFlow 대비 TFLite 최대 logits 차이가 약 `2.61e-8`이었다.

```bash
python -m pip install -r requirements-litert-tensorflow.txt
python src/probe_koelectra_tensorflow_litert.py
```

따라서 현재 채택한 배포 경로는 다음과 같다.

```text
KoELECTRA PyTorch checkpoint
→ TensorFlow KoELECTRA
→ TensorFlow Lite Converter
→ .tflite
```

측정값과 판단 근거는 `reports/koelectra_litert_probe.md`에 기록한다.

### v0.3 1차 학습 결과

동일한 TensorFlow 경로로 encoder 전체 고정 모델과 상위 2-layer 미세조정 모델을
학습했다. 상위 2-layer 모델은 합성 group holdout에서 Accuracy 87.0%, Precision
81.8%, Recall 90.0%를 기록했지만 실제 Room 알림 12개에서는 유일한 중요 배송
알림을 놓쳤다. 따라서 아직 Android에 연결하지 않는다.

```bash
# 학습과 TFLite export. Linux/Colab에서 실행
python src/train_koelectra_tensorflow.py

# 실제 알림을 외부로 보내지 않는 로컬 그림자 평가
source .venv-embeddings/bin/activate
python src/evaluate_koelectra_real_room.py
```

상세 결과는 `reports/koelectra_v0.3_training.md`와
`reports/v0.3_koelectra_real_room_evaluation.md`에 기록한다.
