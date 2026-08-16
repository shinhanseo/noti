# Frozen Backbone 동일조건 모델 비교 v1

세 encoder를 고정하고 동일한 v0.5 600개, Android v2 전처리, 고정 5-Fold, MLP 32-unit으로 비교했다.

## 성능

| 모델 | 합성 CV Accuracy | 합성 CV Macro F1 | Room Accuracy | Room 등장 클래스 Macro F1 | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| granite_97m_r2 | 0.943 | 0.930 | 0.900 | 0.758 | 0.429 | 0.750 | 0.545 | 8 | 2 |
| embeddinggemma_300m | 0.952 | 0.945 | 0.920 | 0.778 | 0.500 | 0.750 | 0.600 | 6 | 2 |
| koelectra_small_v3 | 0.825 | 0.807 | 0.730 | 0.570 | 0.214 | 0.750 | 0.333 | 22 | 2 |

## 동일 Room 행 대응 비교

| 비교 | Accuracy 차이 | Paired bootstrap 95% CI | 중요 F1 차이 | 중요 F1 95% CI | McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: |
| embeddinggemma_300m_minus_granite_97m_r2 | +0.020 | +0.000~+0.050 | +0.055 | +0.000~+0.147 | 0.500000 |
| koelectra_small_v3_minus_granite_97m_r2 | -0.170 | -0.250~-0.090 | -0.212 | -0.354~-0.087 | 0.000076 |
| koelectra_small_v3_minus_embeddinggemma_300m | -0.190 | -0.270~-0.120 | -0.267 | -0.421~-0.128 | 0.000004 |

## 로컬 CPU 참고 측정

| 모델 | 파라미터 | 원본 스냅샷 MiB | Embedding 차원 | 단일 median ms | 단일 p95 ms | Head KiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| granite_97m_r2 | 97,441,152 | 210.0 | 384 | 25.86 | 37.58 | 208.2 |
| embeddinggemma_300m | 307,581,696 | 1210.8 | 768 | 34.07 | 38.29 | 397.4 |
| koelectra_small_v3 | 14,056,192 | 54.2 | 256 | 3.61 | 5.10 | 150.4 |

Mac CPU + PyTorch/SentenceTransformers 측정이므로 Android TFLite 성능이 아니다.
Room 100개 라벨을 확인한 뒤 프로토콜을 고정했으므로 최종 블라인드 확정 결과가 아니라 통제된 탐색 비교다.
품질 점 추정치는 EmbeddingGemma가 1위지만 Granite와의 차이는 통계적으로 확정되지 않았다.
Granite는 EmbeddingGemma보다 다운로드 스냅샷이 작고 로컬 추론이 빨라 현재 모바일 균형 후보로 유지한다.
