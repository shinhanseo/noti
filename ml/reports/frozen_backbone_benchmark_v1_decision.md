# Frozen Backbone 동일조건 비교 판정

## 순수 품질 순위

동일한 v0.5 600개, Android v2 전처리, 고정 5-Fold, frozen encoder, MLP 32-unit
조건에서 품질 점 추정치 순위는 다음과 같다.

1. EmbeddingGemma 300M
2. Granite Embedding 97M R2
3. KoELECTRA-small-v3 frozen mean pooling

| 모델 | Room Accuracy | 중요 F1 | FP | FN |
| --- | ---: | ---: | ---: | ---: |
| EmbeddingGemma 300M | 92.0% | 0.600 | 6 | 2 |
| Granite 97M R2 | 90.0% | 0.545 | 8 | 2 |
| KoELECTRA-small-v3 | 73.0% | 0.333 | 22 | 2 |

EmbeddingGemma는 Granite가 맞힌 실제 90개를 모두 맞히고 일반 알림 2개를 추가로
맞혔다. 그러나 두 모델의 discordant row가 2개뿐이라 McNemar exact p-value는
0.5다. Accuracy +2%p와 중요 F1 +0.055는 현재 표본에서 통계적으로 확정된 차이가
아니다.

Frozen KoELECTRA는 Granite보다 Accuracy 17%p, EmbeddingGemma보다 19%p 낮았다.
두 비교의 McNemar p-value는 각각 약 0.000076, 0.000004로 차이가 명확했다.

## 로컬 실행 비용

| 모델 | 파라미터 | 다운로드 스냅샷 | Mac 단일 median |
| --- | ---: | ---: | ---: |
| EmbeddingGemma 300M | 307.6M | 1210.8 MiB | 34.07 ms |
| Granite 97M R2 | 97.4M | 210.0 MiB | 25.86 ms |
| KoELECTRA-small-v3 | 14.1M | 54.2 MiB | 3.61 ms |

다운로드 스냅샷은 Android 배포 파일 크기가 아니다. 실제 앱 크기·RAM·지연시간은
동일한 양자화 조건으로 변환한 뒤 물리 기기에서 다시 측정해야 한다.

## 현재 선택

- 정확도만 최대화하면 EmbeddingGemma가 1위다.
- 정확도와 모바일 비용의 균형 후보는 Granite다.
- Frozen embedding 방식의 KoELECTRA는 성능 부족으로 제외한다.
- 기존 end-to-end fine-tuned KoELECTRA는 다른 학습 방식이므로 이 결과만으로
  제외하지 않는다.

따라서 다음 온디바이스 단계는 EmbeddingGemma와 Granite 두 모델만 동일 조건으로
변환·양자화해 실제 Android 크기, peak RAM, cold start, median/p95 latency를 비교한다.

## 후속 LiteRT 결과

64 tokens INT8 변환과 ARM64 Android 에뮬레이터 비교를 완료했다. Granite는
96.1 MiB / 평균 추론 중앙값 40.53 ms, EmbeddingGemma는 299.5 MiB / 35.22 ms였다.
양자화 후 Room Accuracy는 각각 89%, 92%였다. 후속 Samsung SM-S711N 실기기에서
Granite는 66.52 ms / overall footprint 652.33 MB, EmbeddingGemma INT8은
58.41 ms / 263.89 MB였다. Granite의 작은 파일이 실행 비용 이점으로 이어지지
않았으므로 1차 앱 적용 후보는 EmbeddingGemma INT8로 변경한다. INT4
EmbeddingGemma는 중요 Recall 하락과 85.68 ms 지연시간으로 제외한다. 상세 결과는
`litert_mobile_benchmark_v1.md`에 기록했다.

## 한계

이 프로토콜은 Room 100개의 정답을 확인한 뒤 고정했다. 실행 중 모델별 튜닝은 하지
않았지만 완전한 사전등록 블라인드 비교는 아니다. 최종 채택 전 세팅을 봉인하고
새 시간순 알림으로 한 번 더 평가해야 한다.
