import csv
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_DIR / "data" / "public"

TRAIN_OUTPUT_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.2.csv"
CONTEXT_OUTPUT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.2.csv"

FIELD_NAMES = [
    "id",
    "app_name",
    "package_name",
    "title",
    "body",
    "label",
    "notification_type",
    "template_group",
    "clarity",
    "reason_code",
    "android_category",
    "is_ongoing",
    "rule_score",
    "rule_level",
    "forced",
    "model_eligible",
    "source",
    "dataset_version",
]


@dataclass(frozen=True)
class AppProfile:
    name: str
    slug: str
    domain: str
    critical: tuple[str, str, str]
    optional: tuple[str, str, str]
    context: tuple[str, str, str, str]
    offer: str


APP_PROFILES = (
    AppProfile(
        "토스",
        "toss",
        "finance",
        ("자동이체", "카드대금 출금", "송금 정보"),
        ("주간 소비 리포트", "자산 현황 보기", "서비스 만족도"),
        ("가족 송금", "저축 목표", "금융 콘텐츠", "소비 기록"),
        "첫 결제 캐시백 혜택",
    ),
    AppProfile(
        "카카오뱅크",
        "kakaobank",
        "finance",
        ("계좌이체", "대출이자 납부", "받는 계좌 정보"),
        ("이번 달 자산 리포트", "저금통 현황", "앱 이용 설문"),
        ("모임통장 대화", "저축 일정", "금융 소식", "용돈 기록"),
        "예금 가입 이벤트",
    ),
    AppProfile(
        "삼성카드",
        "samsungcard",
        "card_payment",
        ("해외 결제", "카드대금 납부", "결제 수단 정보"),
        ("이번 달 이용 내역", "카드 혜택 캘린더", "서비스 설문"),
        ("가족카드 사용", "결제 예정 일정", "카드 생활 소식", "소비 목표"),
        "온라인 쇼핑 할인 혜택",
    ),
    AppProfile(
        "네이버페이",
        "naverpay",
        "card_payment",
        ("간편결제", "후불결제 납부", "환불 계좌 정보"),
        ("포인트 사용 리포트", "멤버십 캘린더", "결제 서비스 설문"),
        ("선물 받은 포인트", "포인트 적립 일정", "쇼핑 소식", "결제 습관"),
        "포인트 추가 적립 이벤트",
    ),
    AppProfile(
        "쿠팡",
        "coupang",
        "shopping",
        ("상품 주문 결제", "배송 예정일", "반품 수거 정보"),
        ("최근 본 상품 요약", "장바구니 알림", "쇼핑 경험 설문"),
        ("선물 주문", "재입고 일정", "상품 후기 소식", "생필품 구매 기록"),
        "와우회원 전용 특가",
    ),
    AppProfile(
        "오늘의집",
        "ohou",
        "shopping",
        ("가구 주문 결제", "설치 배송일", "교환 수거 주소"),
        ("집들이 콘텐츠 요약", "관심 상품 일정", "인테리어 취향 설문"),
        ("가족과 공유한 상품", "셀프 인테리어 일정", "집들이 새 글", "공간 꾸미기 목표"),
        "인기 가구 최대 할인",
    ),
    AppProfile(
        "당근",
        "daangn",
        "local_market",
        ("송금 처리", "거래 약속 시간", "거래 장소 정보"),
        ("동네 활동 요약", "관심 물품 알림", "거래 경험 설문"),
        ("이웃과의 채팅", "중고 거래 일정", "동네 소식", "관심 키워드"),
        "동네 가게 단골 쿠폰",
    ),
    AppProfile(
        "CJ대한통운",
        "cjlogistics",
        "parcel",
        ("배송지 확인", "택배 도착 예정일", "반송 접수 정보"),
        ("주간 배송 요약", "택배 조회 일정", "배송 만족도 설문"),
        ("가족이 보낸 택배", "수령 일정", "택배 이용 소식", "배송 조회 기록"),
        "택배 이용 고객 이벤트",
    ),
    AppProfile(
        "배달의민족",
        "baemin",
        "food_delivery",
        ("배달 주문 결제", "배달 도착 예정 시간", "배달 주소"),
        ("이번 주 주문 요약", "찜한 가게 알림", "배달 경험 설문"),
        ("가족 주문", "저녁 주문 일정", "동네 맛집 소식", "식사 기록"),
        "첫 주문 할인 쿠폰",
    ),
    AppProfile(
        "요기요",
        "yogiyo",
        "food_delivery",
        ("주문 승인", "포장 완료 예정 시간", "수령 장소"),
        ("최근 주문 요약", "즐겨찾기 가게 일정", "주문 만족도 설문"),
        ("친구와 함께한 주문", "점심 주문 일정", "신규 가게 소식", "메뉴 취향 기록"),
        "오늘만 배달비 할인",
    ),
    AppProfile(
        "카카오 T",
        "kakaot",
        "transport",
        ("택시 자동결제", "예약 호출 시간", "탑승 위치"),
        ("이번 달 이동 리포트", "출근길 알림", "이동 서비스 설문"),
        ("가족 택시 호출", "공항 이동 일정", "주변 교통 소식", "이동 기록"),
        "공항 이동 할인 쿠폰",
    ),
    AppProfile(
        "코레일톡",
        "korailtalk",
        "transport",
        ("승차권 결제", "열차 출발 시간", "탑승객 정보"),
        ("여행 기록 요약", "관심 노선 일정", "열차 이용 설문"),
        ("동행자 승차권", "주말 여행 일정", "노선 운행 소식", "기차 여행 기록"),
        "주말 여행 상품 할인",
    ),
    AppProfile(
        "에브리타임",
        "everytime",
        "education",
        ("과제 제출", "시험 일정", "수강 신청 정보"),
        ("주간 게시판 요약", "동아리 모집 일정", "학교생활 설문"),
        ("친구의 쪽지", "동아리 모임", "학교 게시판 소식", "공부 기록"),
        "대학생 제휴 할인",
    ),
    AppProfile(
        "클래스101",
        "class101",
        "education",
        ("수강 결제", "라이브 수업 시간", "과제 제출 정보"),
        ("학습 리포트", "추천 클래스 일정", "수강 만족도 설문"),
        ("강사의 메시지", "개인 학습 일정", "크리에이터 소식", "학습 습관"),
        "인기 클래스 할인",
    ),
    AppProfile(
        "Slack",
        "slack",
        "work",
        ("배포 승인", "고객 회의 시간", "담당 업무 정보"),
        ("주간 채널 요약", "사내 행사 일정", "협업 방식 설문"),
        ("동료의 메시지", "팀 회의", "프로젝트 채널 소식", "업무 집중 기록"),
        "업무 생산성 웨비나",
    ),
    AppProfile(
        "Notion",
        "notion",
        "work",
        ("문서 승인", "프로젝트 마감 일정", "작업 담당자 정보"),
        ("워크스페이스 요약", "템플릿 소개 일정", "제품 사용 설문"),
        ("공유 문서 댓글", "개인 작업 일정", "워크스페이스 소식", "작업 기록"),
        "팀용 템플릿 프로모션",
    ),
    AppProfile(
        "똑닥",
        "ddocdoc",
        "health",
        ("진료비 결제", "병원 예약 시간", "환자 정보"),
        ("건강 기록 요약", "건강 콘텐츠 일정", "진료 경험 설문"),
        ("보호자의 메시지", "건강검진 일정", "병원 소식", "복약 기록"),
        "건강검진 제휴 혜택",
    ),
    AppProfile(
        "정부24",
        "gov24",
        "public_service",
        ("민원 수수료 결제", "서류 제출 기한", "신청인 정보"),
        ("이용 내역 요약", "정책 안내 일정", "서비스 개선 설문"),
        ("담당자의 안내", "민원 처리 일정", "생활 정책 소식", "전자문서 기록"),
        "생활지원 정책 이벤트",
    ),
    AppProfile(
        "카카오톡",
        "kakaotalk",
        "messenger",
        ("송금 받기", "약속 시간", "공유 계정 정보"),
        ("주간 대화 요약", "오픈채팅 일정", "메신저 이용 설문"),
        ("가족 채팅방", "친구 모임", "단체 채팅방 소식", "답장 기록"),
        "이모티콘 할인 이벤트",
    ),
    AppProfile(
        "SmartThings",
        "smartthings",
        "smart_home",
        ("현관문 센서", "보안 모드 일정", "가족 구성원 권한"),
        ("주간 에너지 요약", "자동화 실행 일정", "스마트홈 이용 설문"),
        ("가족의 기기 제어", "취침 자동화", "새 기기 소식", "전력 사용 기록"),
        "스마트 기기 제휴 할인",
    ),
)


def level_for_score(score: int) -> str:
    if score >= 40:
        return "IMPORTANT"
    if score >= 25:
        return "REVIEW"
    return "GENERAL"


def create_row(
    *,
    row_id: str,
    app: AppProfile,
    title: str,
    body: str,
    label: int | None,
    notification_type: str,
    template_group: str,
    clarity: str,
    reason_code: str,
    android_category: str,
    rule_score: int,
    is_ongoing: bool = False,
) -> dict[str, object]:
    forced = False
    rule_level = level_for_score(rule_score)
    model_eligible = not forced and rule_level == "REVIEW"

    return {
        "id": row_id,
        "app_name": app.name,
        "package_name": f"synthetic.kr.{app.slug}",
        "title": title,
        "body": body,
        "label": "" if label is None else label,
        "notification_type": notification_type,
        "template_group": template_group,
        "clarity": clarity,
        "reason_code": reason_code,
        "android_category": android_category,
        "is_ongoing": str(is_ongoing).lower(),
        "rule_score": rule_score,
        "rule_level": rule_level,
        "forced": str(forced).lower(),
        "model_eligible": str(model_eligible).lower(),
        "source": "SYNTHETIC_REVIEWED",
        "dataset_version": "0.2",
    }


def promote_body(subject: str, scenario: int, variant: int) -> str:
    bodies = (
        (
            f"{subject} 처리가 정상적으로 완료되지 않았습니다.",
            f"{subject} 처리 중 문제가 발생했습니다.",
        ),
        (
            f"{subject}: 오늘 오후 6시로 변경되었습니다.",
            f"{subject}: 예정 시간이 내일 오전 9시로 바뀌었습니다.",
        ),
        (
            f"확인이 필요합니다: {subject}",
            f"{subject} 관련 확인이 필요합니다.",
        ),
    )
    return bodies[scenario][variant]


def keep_body(subject: str, scenario: int, variant: int) -> str:
    bodies = (
        (
            f"{subject}: 이번 주 요약이 도착했습니다.",
            f"{subject} 세부 내용을 확인해주세요.",
        ),
        (
            f"{subject} 관련 새 내용이 오늘 오후 3시에 공개됩니다.",
            f"{subject} 관련 내용이 내일 오전 10시에 업데이트됩니다.",
        ),
        (
            f"{subject} 참여 요청이 도착했습니다.",
            f"{subject} 관련 의견을 남겨주세요.",
        ),
    )
    return bodies[scenario][variant]


def build_train_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    row_number = 1

    for app in APP_PROFILES:
        for scenario, subject in enumerate(app.critical):
            for variant in range(2):
                titles = (app.name, f"{subject} 안내")
                scores = (25, 30, 25)
                types = ("exception", "schedule_change", "action_required")
                reasons = (
                    "concrete_failure_or_exception",
                    "meaningful_schedule_change",
                    "concrete_user_confirmation",
                )

                rows.append(
                    create_row(
                        row_id=f"V02_TRAIN_{row_number:03d}",
                        app=app,
                        title=titles[variant],
                        body=promote_body(subject, scenario, variant),
                        label=1,
                        notification_type=types[scenario],
                        template_group=(
                            f"eligible_promote_{scenario}_{variant}"
                        ),
                        clarity="CLEAR",
                        reason_code=reasons[scenario],
                        android_category="msg",
                        rule_score=scores[scenario],
                    )
                )
                row_number += 1

        for scenario, subject in enumerate(app.optional):
            for variant in range(2):
                titles = (app.name, f"{subject} 안내")
                types = ("summary", "optional_schedule", "optional_survey")
                reasons = (
                    "informational_summary",
                    "optional_timed_content",
                    "optional_participation_request",
                )

                rows.append(
                    create_row(
                        row_id=f"V02_TRAIN_{row_number:03d}",
                        app=app,
                        title=titles[variant],
                        body=keep_body(subject, scenario, variant),
                        label=0,
                        notification_type=types[scenario],
                        template_group=f"eligible_keep_{scenario}_{variant}",
                        clarity="CLEAR",
                        reason_code=reasons[scenario],
                        android_category=(
                            "reminder" if scenario == 1 else "msg"
                        ),
                        rule_score=25,
                    )
                )
                row_number += 1

        clear_important = (
            (
                "긴급 확인",
                f"{app.critical[0]} 문제로 오늘까지 처리가 필요합니다. 즉시 확인해주세요.",
                "urgent_action",
                "urgent_and_action_required",
                45,
            ),
            (
                "보안 알림",
                f"새로운 기기에서 {app.critical[2]} 변경이 감지되었습니다.",
                "security_change",
                "explicit_security_change",
                50,
            ),
        )

        for variant, (title, body, notification_type, reason, score) in enumerate(
            clear_important
        ):
            rows.append(
                create_row(
                    row_id=f"V02_TRAIN_{row_number:03d}",
                    app=app,
                    title=title,
                    body=body,
                    label=1,
                    notification_type=notification_type,
                    template_group=f"clear_important_{variant}",
                    clarity="CLEAR",
                    reason_code=reason,
                    android_category="alarm" if variant == 0 else "msg",
                    rule_score=score,
                )
            )
            row_number += 1

        clear_general = (
            (
                "(광고) 오늘의 혜택",
                f"{app.offer}, 오늘만 확인하세요. 수신거부는 설정에서 가능합니다.",
                "promotion",
                "explicit_promotion",
                -15,
            ),
            (
                "업데이트 완료",
                f"{app.optional[0]} 업데이트가 완료되었습니다. 별도 작업은 필요하지 않습니다.",
                "passive_update",
                "no_action_status",
                -10,
            ),
        )

        for variant, (title, body, notification_type, reason, score) in enumerate(
            clear_general
        ):
            rows.append(
                create_row(
                    row_id=f"V02_TRAIN_{row_number:03d}",
                    app=app,
                    title=title,
                    body=body,
                    label=0,
                    notification_type=notification_type,
                    template_group=f"clear_general_{variant}",
                    clarity="CLEAR",
                    reason_code=reason,
                    android_category="promo" if variant == 0 else "status",
                    rule_score=score,
                )
            )
            row_number += 1

    return rows


def build_context_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    row_number = 1

    for app in APP_PROFILES:
        bodies = (
            f"{app.context[0]} 관련 새 메시지가 도착했습니다.",
            f"{app.context[1]} 시작까지 한 시간 남았습니다.",
            f"{app.context[2]} 새 소식이 등록되었습니다.",
            f"설정한 {app.context[3]} 리마인더 시간입니다.",
        )
        titles = (app.name, "일정 알림", "새 소식", "리마인더")
        types = (
            "relationship_message",
            "personal_schedule",
            "interest_update",
            "personal_habit",
        )
        reasons = (
            "sender_relationship_required",
            "personal_schedule_context_required",
            "personal_interest_required",
            "personal_preference_required",
        )
        scores = (5, 25, 5, 25)
        categories = ("msg", "reminder", "social", "reminder")

        for variant in range(4):
            rows.append(
                create_row(
                    row_id=f"V02_CONTEXT_{row_number:03d}",
                    app=app,
                    title=titles[variant],
                    body=bodies[variant],
                    label=None,
                    notification_type=types[variant],
                    template_group=f"context_{variant}",
                    clarity="CONTEXT_DEPENDENT",
                    reason_code=reasons[variant],
                    android_category=categories[variant],
                    rule_score=scores[variant],
                )
            )
            row_number += 1

    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELD_NAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    train_rows = build_train_rows()
    context_rows = build_context_rows()

    write_csv(TRAIN_OUTPUT_PATH, train_rows)
    write_csv(CONTEXT_OUTPUT_PATH, context_rows)

    print(f"학습·대조 데이터: {len(train_rows)}개")
    print(TRAIN_OUTPUT_PATH)
    print(f"문맥 의존 데이터: {len(context_rows)}개")
    print(CONTEXT_OUTPUT_PATH)


if __name__ == "__main__":
    main()
