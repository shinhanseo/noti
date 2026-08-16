# ibm-granite/granite-embedding-97m-multilingual-r2 + Thin Head v0.5 실험

## 조건

- 학습 데이터: 600개
- 분할: 고정 5-Fold, template_group 중복 0
- 입력 전처리: `android-importance-text-v2`
- 프롬프트: ``
- `ibm-granite/granite-embedding-97m-multilingual-r2`은 고정하고 얇은 분류 Head만 학습

## 교차검증

| Head | 3단계 Accuracy | Macro F1 | 이진 Accuracy | Precision | Recall | FP | FN | 임계값 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `logistic_regression` | 0.887 | 0.865 | 0.947 | 1.000 | 0.900 | 0 | 32 | 0.715 |
| `mlp_32` | 0.943 | 0.930 | 0.947 | 1.000 | 0.900 | 0 | 32 | 0.965 |

선택 Head: `mlp_32` (홀드아웃을 보기 전에 Macro F1로 선택)

## 실제 Room 독립 홀드아웃 6개

| Head | 개인 Accuracy(0.5) | Precision | Recall | CV 임계값 Accuracy | 공통 Actionability Accuracy |
|---|---:|---:|---:|---:|---:|
| `logistic_regression` | 0.500 | 1.000 | 0.250 | 0.333 | 0.333 |
| `mlp_32` | 0.500 | 1.000 | 0.250 | 0.333 | 0.500 |

선택 Head의 앱 전체 파이프라인 Accuracy: 0.500 (3/6)
- 공통 Actionability Accuracy: 0.500
- 공통 Actionability Macro F1: 0.324

## 개발 Mac CPU 참고값

- 원본 Hugging Face 스냅샷: 210.0 MiB
- 분류 Head: 190.2 KiB
- 모델 로딩: 0.62초
- 단일 알림 Embedding median/P95: 9.35/10.10 ms

## 제한

- 학습 데이터 600개는 합성 중심이며 실제 홀드아웃은 6개뿐이다.
- 이 수치는 Python FP32 모델의 Mac CPU 결과이며 Android LiteRT 성능이 아니다.
- 모델 전체를 미세조정한 것이 아니라 고정 Embedding 위의 분류 Head만 학습했다.
- Android 채택 전 양자화·변환·실제 기기 RAM/배터리 측정이 필요하다.
