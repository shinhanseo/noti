# 신규 온디바이스 후보 동일조건 비교 v1

기존 비교에 사용한 모델은 제외하고, 세 신규 encoder를 고정한 뒤 동일한 v0.5 600개, Android v2 전처리, 고정 5-Fold, MLP 32-unit으로 비교했다.

## 성능

| 모델 | 합성 CV Acc | 합성 CV Macro F1 | Room 100 Acc | Room 45 Acc | Room 145 Acc | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| kor_static_embedding_128 | 0.832 | 0.820 | 0.630 | 0.689 | 0.648 | 0.148 | 0.615 | 0.239 | 46 | 5 |
| lfm2_5_embedding_350m | 0.960 | 0.956 | 0.930 | 0.933 | 0.931 | 0.579 | 0.846 | 0.688 | 8 | 2 |
| nomic_embed_text_v2_moe | 0.970 | 0.964 | 0.910 | 0.933 | 0.917 | 0.524 | 0.846 | 0.647 | 10 | 2 |

## 로컬 CPU 참고 측정

| 모델 | 파라미터 | 원본 스냅샷 MiB | 차원 | 단일 median ms | 단일 p95 ms | Head KiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| kor_static_embedding_128 | 4,096,000 | 16.3 | 128 | 0.67 | 1.32 | 79.9 |
| lfm2_5_embedding_350m | 354,483,968 | 680.8 | 1024 | 438.33 | 593.68 | 525.4 |
| nomic_embed_text_v2_moe | 475,292,928 | 1834.3 | 768 | 43.57 | 54.44 | 397.9 |

## 해석 주의

- Room 145개 라벨은 모델 예측 전에 이미 확인했으므로, 신규 모델에 대한 최종 블라인드 성능이 아니라 회고적 개발 비교다.
- 로컬 CPU + PyTorch/SentenceTransformers 수치는 Android ONNX Runtime 수치가 아니다.
- Android 채택 전에는 승자 1개를 ONNX로 변환한 뒤 새 Room 알림을 예측 봉인하고 라벨링해야 한다.
- HiEmbed_base_onnx_v1은 공식 external weight 파일과 ONNX tensor offset이 맞지 않아 품질 비교 전에 제외했다.
