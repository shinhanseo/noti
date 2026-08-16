# Room Active Learning 검수 후보 선정

## 결과

- 비강제 자동 판정 알림: 354개
- 패키지+전처리 문장 중복 제거 후: 299개
- 의미 군집 대표 검수 후보: 40개
- 후보 패키지 수: 21개
- 모델·규칙 중요 여부 불일치 후보: 32개
- 3단계 모델 불일치 후보: 26개
- Kotlin REVIEW 후보: 1개
- 명시적 광고 문구 후보: 5개
- 동일 패키지 최대 후보: 3개

## 선정 방식

1. 사용자 피드백이 아닌 비강제 알림만 사용했다.
2. Android v2 전처리 후 패키지와 문장이 같은 중복을 합쳤다.
3. KoELECTRA, EmbeddingGemma, Granite와 Kotlin 규칙의 불일치를 계산했다.
4. Granite 의미 Embedding을 검수 후보 수의 두 배인 군집으로 묶었다.
5. 군집 대표를 우선하되, 명시적 광고는 최대 5개·동일 패키지는 최대 3개로 제한했다.

## 검수 방법

Git 제외 private CSV의 마지막 세 열만 작성한다.

- `user_common_actionability`: GENERAL / ATTENTION_WORTHY / ACTION_REQUIRED
- `user_personal_preference`: GENERAL / IMPORTANT
- `review_note`: 선택 사항

알림 원문과 개별 예측은 private CSV에만 저장했다.
