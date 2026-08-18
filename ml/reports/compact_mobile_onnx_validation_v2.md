# Compact mobile ARM64 INT8 ONNX 검증 v2

원본 PyTorch 후보 평가와 동일한 데이터·전처리·5-Fold·MLP head를 실제 양자화 ONNX 출력으로 다시 평가했다.

| 모델 | Room 145 Acc | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN | 원본과 평균 cosine | ONNX MiB | 단일 median ms* |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bekko_embedding_v1_a25m_arm64_int8 | 0.938 | 0.625 | 0.769 | 0.690 | 6 | 3 | 0.987841 | 118.2 | 5.39 |
| koen_e5_tiny_arm64_int8 | 0.910 | 0.500 | 0.923 | 0.649 | 12 | 1 | 0.986650 | 36.5 | 3.71 |

\* Apple Silicon Mac의 Python ONNX Runtime 참고값이며 Android 실기기 수치가 아니다.
토크나이저와 Android 런타임 라이브러리 용량은 ONNX MiB 열에 포함하지 않았다.
