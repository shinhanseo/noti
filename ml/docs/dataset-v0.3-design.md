# noti. 알림 데이터셋 v0.3 설계

## 목표

v0.3은 v0.2의 학습 파이프라인을 유지하면서 실제 한국 사용자에게 올 법한 알림 표현을 늘리는 버전이다. 실제 알림처럼 보이는 문장과 실제로 수집된 문장은 구분한다.

핵심 원칙은 다음과 같다.

1. `label=1`은 AI가 REVIEW 알림에 중요도 가점을 주는 방향, `label=0`은 가점을 주지 않는 방향이다.
2. 공개 데이터나 Room 원문이라는 이유만으로 정답 라벨을 자동 부여하지 않는다.
3. 학습 파일에는 `POLICY_REVIEWED` 또는 `HUMAN_REVIEWED` 라벨만 들어간다.
4. 같은 문장 템플릿은 같은 `template_group`으로 묶어 학습·평가 Fold를 넘나들지 못하게 한다.
5. 앱 이름이나 패키지만 보고 정답을 외우지 않도록 모델 입력은 계속 `title + body`를 기본으로 한다.

## 오늘 생성한 구성

| 파일 | 행 수 | 용도 |
|---|---:|---|
| `train_notifications_v0.3.csv` | 480 | 라벨 검토가 끝난 학습·대조 데이터 |
| `context_notifications_v0.3.csv` | 80 | 개인 관계·일정 등 정답을 강제하지 않는 데이터 |
| `public_evaluation_v0.3.csv` | 0 | 공개 실데이터를 검토 전 보관할 빈 입구 |
| `source_manifest_v0.3.csv` | 7 sources | 출처·라이선스·현재 반입 상태 기록 |

학습 데이터 480개는 v0.2 이관분 320개와 현실형 신규 문장 160개로 구성된다. 전체 라벨은 240:240이며, 현실형 신규 문장도 80:80이다.

## 현실형 신규 문장의 범위

다음 20개 앱 스타일을 참고해 직접 작성한 합성 문장이다.

- 쇼핑: 쿠팡, 오늘의집, 네이버 쇼핑, 무신사, 지그재그, 에이블리, 올리브영, 11번가, G마켓, 롯데ON
- 카드·결제: 신한 SOL페이, KB Pay, 현대카드, 삼성카드, 카카오페이, 토스
- 배달: 배달의민족, 요기요
- 택배: CJ대한통운, 한진택배

앱에서 복사한 실제 문장이 아니다. 브랜드명, `(광고)`, 짧은 제목, 앱 이름만 있는 제목, 행동 요청, 실패·보류·취소 문구처럼 실제 푸시에서 흔한 형태를 반영했다.

중요 방향 예시는 결제 실패, 승인 거절, 의심 결제 확인, 주소 확인, 환불 지연, 배송 예외다. 일반 방향 예시는 할인 광고, 장바구니 리마인더, 상품 추천, 소비 요약, 선택형 설문이다.

## 추가 메타데이터

v0.2 컬럼 뒤에 다음 필드를 추가했다.

- `source_detail`: 생성기 또는 반입 경로
- `source_url`: 공개 원본 주소
- `license`: 재사용 조건
- `is_real`: 실제 발송 문장 여부
- `is_public`: Git에 둘 수 있는 데이터인지 여부
- `label_status`: `POLICY_REVIEWED`, `HUMAN_REVIEWED`, `UNLABELED`, `UNLABELED_CONTEXT`
- `original_source_id`: 원본과 다시 대조할 때 사용하는 식별자

## 공개 데이터 사용 원칙

공공데이터의 제목과 본문은 한국어 표현의 현실성을 확인하고 모델의 실패 사례를 찾는 데 쓴다. 처음 반입할 때는 아래 값을 강제한다.

```text
label=
clarity=UNREVIEWED
model_eligible=false
source=PUBLIC_REAL_UNLABELED
label_status=UNLABELED
```

공개 데이터의 `문자`, `알림톡`, `재난문자`, `스팸` 같은 원래 분류는 noti.의 중요도 라벨과 다르다. 따라서 사람이 importance-policy 기준으로 검토하기 전에는 학습 데이터로 승격하지 않는다.

## 내일 Room 데이터가 오면

원본 CSV는 `ml/data/private/`에만 두며 이 폴더는 Git에서 제외된다. 우선 아래 명령으로 익명화된 후보 파일을 만든다.

```bash
python src/prepare_room_notifications_v03.py \
  data/private/room_notifications_raw.csv
```

Room 컬럼명이 다르면 명시한다.

```bash
python src/prepare_room_notifications_v03.py \
  data/private/room_notifications_raw.csv \
  --title-column notificationTitle \
  --body-column notificationText \
  --app-column appName \
  --package-column packageName
```

변환기는 URL, 이메일, 휴대전화, 긴 카드·계좌번호, 원 단위 금액, 인증코드를 마스킹한다. 원문은 터미널에 출력하지 않는다. 사람 이름이나 주소처럼 정규식만으로 안전하게 판별하기 어려운 정보는 병합 전에 별도로 눈으로 확인해야 한다.

그다음 순서는 중복 제거 → template group 부여 → 정책 점수 재현 → 사람이 애매한 문장 검토 → 그림자 평가 → 일부만 `HUMAN_REVIEWED`로 승격이다.

## 아직 하지 않은 것

- 공개 원문을 학습 라벨로 사용하지 않았다.
- 엄마 폰 데이터가 없으므로 실제 사용자 분포를 반영했다고 주장하지 않는다.
- v0.3 모델을 다시 학습하거나 정확도를 발표하지 않았다.
- 실제 Android 기기의 속도·메모리·배터리를 측정하지 않았다.

현재 v0.3은 현실성 보강과 안전한 데이터 반입 구조까지 만든 초안이다. 실제 성능 판단은 Room 데이터가 들어온 뒤 진행한다.
