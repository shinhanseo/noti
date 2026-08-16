# Frozen Backbone 동일조건 모델 비교 v1

## 목적

데이터나 학습 방식의 차이가 아니라 사전학습 encoder 자체의 표현력을 비교한다.
이 프로토콜은 결과를 실행하기 전에 고정하며, 모델별로 hyperparameter를 조정하지
않는다.

## 비교 모델

- `ibm-granite/granite-embedding-97m-multilingual-r2`
- `google/embeddinggemma-300m`
- `monologg/koelectra-small-v3-discriminator`

## 고정 조건

| 항목 | 조건 |
| --- | --- |
| 학습 데이터 | v0.5 학습 가능 600개 |
| 실제 평가 | 봉인 후 검수된 Room 100개 |
| 전처리 | `android-importance-text-v2` |
| 최대 token 길이 | 64 |
| encoder | 전체 frozen |
| embedding | attention-mask mean pooling 계열 + L2 normalize |
| head | MLP 32-unit, ReLU, alpha 0.001 |
| class weight | balanced sample weight |
| random seed | 42 |
| CV | 저장된 동일 5개 group fold |
| 출력 | GENERAL / ATTENTION_WORTHY / ACTION_REQUIRED |

EmbeddingGemma는 공식 classification query prefix를 사용한다. Granite와
KoELECTRA는 prefix를 사용하지 않는다. tokenizer와 내부 pooling 구현은 각 모델에
필요한 입력 어댑터이므로 서로 같게 강제하지 않으며, 데이터·분할·head·평가 기준은
동일하게 유지한다.

KoELECTRA는 문장 embedding 전용 모델이 아니므로 `ElectraModel` 마지막 hidden
state를 attention mask로 mean pooling한 뒤 L2 정규화한다. 이 비교의 KoELECTRA는
기존 end-to-end fine-tuned KoELECTRA와 다른 frozen-backbone 대조군이다.

## 해석 제한

Room 100개의 사람 라벨을 확인한 뒤 이 프로토콜을 만들었다. 모델별 설정은 이
문서대로 한 번만 실행하고 결과에 따라 조정하지 않지만, 완전한 사전등록 블라인드
테스트는 아니다. 최종 모델은 세 후보의 설정과 예측을 먼저 봉인한 다음 수집한 새
시간순 알림에서 확정한다.
