# LFM2.5 Embedding ONNX 변환 검증 v1

배치 1, 64 tokens, `document:` 프롬프트로 고정한 encoder를 동일한 MLP head와 Room 145개로 검증했다.

| 모델 | 크기 MiB | 동일 FP32 source cosine 평균/최소 | 기존 BF16 cosine 평균/최소 | 예측 불일치 | Room Acc | 중요 Recall | 중요 F1 | median ms | p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| fp32 | 1354.0 | 1.000000 / 1.000000 | 0.995587 / 0.951108 | 1 | 0.938 | 0.846 | 0.710 | 194.28 | 219.70 |
| dynamic_int8 | 532.9 | 0.981127 / 0.960682 | 0.977099 / 0.933870 | 4 | 0.917 | 0.846 | 0.647 | 57.22 | 66.01 |
| weight_int4 | 403.3 | 0.940998 / 0.871168 | 0.936438 / 0.871986 | 5 | 0.924 | 0.923 | 0.686 | 214.87 | 238.34 |

Mac CPU + ONNX Runtime 측정이며 Android 실기기 결과가 아니다.
LFM 공식 bidirectional ShortConv는 배치 크기에 따라 출력이 조금 달라져 배포 계약과 검증 기준을 모두 batch 1로 고정했다.
INT4가 가장 작지만 403 MiB이고 `com.microsoft::MatMulNBits`를 사용하므로 현재 상태로 앱에 채택하지 않는다.
다음 후보는 더 작은 backbone을 찾거나 LFM 지식을 작은 학생 모델로 증류해야 한다.
