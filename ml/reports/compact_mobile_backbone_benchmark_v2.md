# Compact mobile backbone 동일조건 비교 v2

기존 후보를 제외하고 새 소형 후보 세 개를 v0.5 600개, Android v2 전처리, 고정 5-Fold, 동일 MLP 32-unit, Room 145개로 비교했다.

## 성능과 배포 크기

| 모델 | 합성 CV Acc | Room 100 Acc | Room 45 Acc | Room 145 Acc | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN | 모델+토크나이저 MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bekko_embedding_v1_a8m | 0.927 | 0.880 | 0.911 | 0.890 | 0.440 | 0.846 | 0.579 | 14 | 2 | 156.8 |
| bekko_embedding_v1_a25m | 0.970 | 0.930 | 0.978 | 0.945 | 0.632 | 0.923 | 0.750 | 7 | 1 | 151.0 |
| koen_e5_tiny | 0.943 | 0.900 | 0.978 | 0.924 | 0.545 | 0.923 | 0.686 | 10 | 1 | 39.3 |

## Python CPU 참고 측정

| 모델 | 전체 파라미터 | 차원 | 단일 median ms | 단일 p95 ms | 배포 artifact |
| --- | ---: | ---: | ---: | ---: | --- |
| bekko_embedding_v1_a8m | 105,975,168 | 384 | 8.65 | 11.60 | default ONNX with int8 token embedding table |
| bekko_embedding_v1_a25m | 123,234,432 | 384 | 7.83 | 10.16 | ARM64 qint8 ONNX |
| koen_e5_tiny | 37,517,184 | 384 | 6.89 | 14.02 | ARM64 qint8 ONNX |

Room 145개는 회고적 개발 비교이며 최종 블라인드 결과가 아니다.
배포 크기는 Hugging Face 저장소에서 확인한 모델 파일과 tokenizer.json의 합이며 Android 라이브러리 용량은 제외한다.
실제 채택 전 승자의 ONNX 출력을 검증하고 Android 실기기에서 속도·메모리·배터리를 측정해야 한다.
