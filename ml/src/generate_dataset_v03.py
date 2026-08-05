import csv
from dataclasses import dataclass
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_DIR / "data" / "public"

V02_TRAIN_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.2.csv"
V02_CONTEXT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.2.csv"
TRAIN_OUTPUT_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.3.csv"
CONTEXT_OUTPUT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.3.csv"
PUBLIC_EVALUATION_PATH = PUBLIC_DATA_DIR / "public_evaluation_v0.3.csv"

V02_FIELDS = [
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

METADATA_FIELDS = [
    "source_detail",
    "source_url",
    "license",
    "is_real",
    "is_public",
    "label_status",
    "original_source_id",
]

FIELD_NAMES = V02_FIELDS + METADATA_FIELDS


@dataclass(frozen=True)
class BrandProfile:
    name: str
    slug: str
    domain: str
    subject: str
    offer: str


BRANDS = (
    BrandProfile("쿠팡", "coupang", "commerce", "주문 상품", "와우회원 전용 특가"),
    BrandProfile("오늘의집", "ohouse", "commerce", "가구 주문", "인기 가구 할인"),
    BrandProfile("네이버 쇼핑", "naver_shopping", "commerce", "쇼핑 주문", "네이버페이 추가 적립"),
    BrandProfile("무신사", "musinsa", "commerce", "패션 상품", "회원 전용 브랜드 할인"),
    BrandProfile("지그재그", "zigzag", "commerce", "스토어 주문", "오늘만 추가 할인"),
    BrandProfile("에이블리", "ably", "commerce", "마켓 주문", "찜한 상품 쿠폰"),
    BrandProfile("올리브영", "oliveyoung", "commerce", "뷰티 상품", "멤버십 데이 특가"),
    BrandProfile("11번가", "elevenst", "commerce", "온라인 주문", "타임딜 할인"),
    BrandProfile("G마켓", "gmarket", "commerce", "배송 상품", "스마일클럽 쿠폰"),
    BrandProfile("신한 SOL페이", "shinhan_solpay", "card", "신한카드", "이번 달 맞춤 혜택"),
    BrandProfile("KB Pay", "kbpay", "card", "KB국민카드", "생활비 할인 혜택"),
    BrandProfile("현대카드", "hyundaicard", "card", "현대카드", "M포인트 사용 혜택"),
    BrandProfile("삼성카드", "samsungcard", "card", "삼성카드", "쇼핑 할인 혜택"),
    BrandProfile("카카오페이", "kakaopay", "payment", "카카오페이 결제", "페이포인트 적립 이벤트"),
    BrandProfile("토스", "toss", "payment", "토스 결제", "첫 결제 캐시백"),
    BrandProfile("배달의민족", "baemin", "food", "배달 주문", "오늘 쓸 수 있는 배달 쿠폰"),
    BrandProfile("요기요", "yogiyo", "food", "배달 주문", "포장 주문 할인"),
    BrandProfile("CJ대한통운", "cjlogistics", "parcel", "택배 물품", "택배 이용 고객 이벤트"),
    BrandProfile("한진택배", "hanjin", "parcel", "배송 물품", "배송 서비스 이벤트"),
    BrandProfile("롯데ON", "lotteon", "commerce", "쇼핑 주문", "엘포인트 추가 적립"),
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=FIELD_NAMES,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def migrate_v02(row: dict[str, str]) -> dict[str, object]:
    migrated: dict[str, object] = dict(row)
    migrated.update(
        {
            "source_detail": "noti_v0.2_generator",
            "source_url": "",
            "license": "PROJECT_OWNED",
            "is_real": "false",
            "is_public": "true",
            "label_status": (
                "POLICY_REVIEWED" if row["label"] else "UNLABELED_CONTEXT"
            ),
            "original_source_id": row["id"],
            "dataset_version": "0.3",
        }
    )
    return migrated


def make_row(
    *,
    row_id: str,
    app: BrandProfile,
    title: str,
    body: str,
    label: int,
    notification_type: str,
    template_group: str,
    reason_code: str,
    android_category: str = "msg",
    rule_score: int = 25,
) -> dict[str, object]:
    return {
        "id": row_id,
        "app_name": app.name,
        "package_name": f"synthetic.brand.{app.slug}",
        "title": title,
        "body": body,
        "label": label,
        "notification_type": notification_type,
        "template_group": template_group,
        "clarity": "CLEAR",
        "reason_code": reason_code,
        "android_category": android_category,
        "is_ongoing": "false",
        "rule_score": rule_score,
        "rule_level": "REVIEW",
        "forced": "false",
        "model_eligible": "true",
        "source": "SYNTHETIC_REALISTIC_REVIEWED",
        "dataset_version": "0.3",
        "source_detail": "brand_style_seed_written_for_noti",
        "source_url": "",
        "license": "PROJECT_OWNED",
        "is_real": "false",
        "is_public": "true",
        "label_status": "POLICY_REVIEWED",
        "original_source_id": "",
    }


def scenarios_for(app: BrandProfile) -> tuple[list[tuple[str, ...]], list[tuple[str, ...]]]:
    if app.domain == "commerce":
        promote = [
            (app.name, f"{app.subject} 결제가 완료되지 않았어요. 결제 수단을 확인해주세요.", "payment_failure", "payment_failure", "concrete_failure_or_exception"),
            ("배송지 확인이 필요해요", f"{app.subject}의 주소 정보가 부족해 배송이 보류됐습니다.", "address_action", "address_action", "concrete_user_confirmation"),
            ("주문 취소 안내", f"재고 부족으로 {app.subject}이 취소되었습니다. 환불 상태를 확인해주세요.", "order_cancelled", "order_cancelled", "concrete_failure_or_exception"),
            ("환불 처리 지연", f"{app.subject} 환불이 예정일에 완료되지 않았습니다.", "refund_exception", "refund_exception", "concrete_failure_or_exception"),
        ]
        keep = [
            ("장바구니에 상품이 남아 있어요", "지금 주문하면 받을 수 있는 예상 날짜를 확인해보세요.", "cart_reminder", "cart_reminder", "optional_marketing_reminder"),
            ("(광고) 오늘 도착한 혜택", f"{app.offer}, 앱에서 확인해보세요. 수신거부는 설정에서 가능합니다.", "promotion", "explicit_promotion", "explicit_promotion"),
            ("가격이 내려갔어요", "관심 상품의 가격 변동 소식을 확인해보세요.", "price_drop", "price_drop", "optional_marketing_reminder"),
            (app.name, "최근 본 상품과 비슷한 상품을 모아봤어요.", "recommendation", "recommendation", "personalized_recommendation"),
        ]
    elif app.domain == "card":
        promote = [
            ("승인 거절", f"{app.subject} 결제가 승인되지 않았습니다. 이용 상태를 확인해주세요.", "card_declined", "card_declined", "concrete_failure_or_exception"),
            (app.name, "평소와 다른 해외 결제가 감지되었습니다. 본인 결제인지 확인해주세요.", "suspicious_payment", "suspicious_payment", "concrete_user_confirmation"),
            ("자동납부 실패", f"{app.subject} 자동납부가 처리되지 않았습니다.", "autopay_failure", "autopay_failure", "concrete_failure_or_exception"),
            ("카드 배송지 확인", "재발급 카드 배송을 위해 주소 확인이 필요합니다.", "address_action", "card_address_action", "concrete_user_confirmation"),
        ]
        keep = [
            ("(광고) 이번 달 카드 혜택", f"{app.offer}을 확인해보세요. 수신거부는 설정에서 가능합니다.", "promotion", "card_promotion", "explicit_promotion"),
            ("소비 리포트가 도착했어요", "지난달 이용 내역을 카테고리별로 확인해보세요.", "summary", "card_summary", "informational_summary"),
            ("포인트 사용처 추천", "보유 포인트로 이용할 수 있는 혜택을 모아봤어요.", "recommendation", "point_recommendation", "personalized_recommendation"),
            (app.name, "이번 주 인기 이벤트에 참여해보세요.", "optional_event", "card_event", "optional_participation_request"),
        ]
    elif app.domain == "payment":
        promote = [
            ("결제 실패", f"{app.subject}가 처리되지 않았습니다. 결제 수단을 확인해주세요.", "payment_failure", "payment_failure", "concrete_failure_or_exception"),
            (app.name, "새 기기에서 결제가 시도되었습니다. 본인이 아니라면 확인해주세요.", "suspicious_payment", "payment_security", "concrete_user_confirmation"),
            ("송금 보류", "받는 사람 정보 확인이 필요해 송금이 보류되었습니다.", "transfer_hold", "transfer_hold", "concrete_user_confirmation"),
            ("환불 확인 필요", "환불 계좌 정보가 일치하지 않아 처리가 중단되었습니다.", "refund_exception", "refund_exception", "concrete_failure_or_exception"),
        ]
        keep = [
            ("(광고) 포인트 혜택", f"{app.offer}을 확인해보세요. 수신거부는 설정에서 가능합니다.", "promotion", "pay_promotion", "explicit_promotion"),
            ("이번 주 소비 요약", "카테고리별 지출 변화를 확인해보세요.", "summary", "pay_summary", "informational_summary"),
            ("내게 맞는 금융 콘텐츠", "최근 이용 내역을 바탕으로 콘텐츠를 추천해드려요.", "recommendation", "finance_recommendation", "personalized_recommendation"),
            (app.name, "친구 초대 이벤트가 진행 중이에요.", "optional_event", "pay_event", "optional_participation_request"),
        ]
    elif app.domain == "food":
        promote = [
            ("결제 실패", f"{app.subject} 결제가 완료되지 않았습니다.", "payment_failure", "food_payment_failure", "concrete_failure_or_exception"),
            (app.name, "가게 사정으로 주문이 취소되었습니다. 환불 상태를 확인해주세요.", "order_cancelled", "food_order_cancelled", "concrete_failure_or_exception"),
            ("주소 확인 요청", "배달 기사님이 상세 주소를 확인하고 있습니다.", "address_action", "food_address_action", "concrete_user_confirmation"),
            ("환불 처리 지연", "취소한 주문의 환불이 아직 완료되지 않았습니다.", "refund_exception", "food_refund_exception", "concrete_failure_or_exception"),
        ]
        keep = [
            ("(광고) 오늘의 쿠폰", f"{app.offer}을 확인해보세요. 수신거부는 설정에서 가능합니다.", "promotion", "food_promotion", "explicit_promotion"),
            ("뭐 먹을지 고민된다면", "최근 주문한 메뉴와 비슷한 맛집을 모아봤어요.", "recommendation", "food_recommendation", "personalized_recommendation"),
            ("리뷰를 기다리고 있어요", "지난 주문은 어떠셨나요? 경험을 남겨주세요.", "optional_survey", "food_review", "optional_participation_request"),
            (app.name, "찜한 가게에 새로운 메뉴가 등록됐어요.", "interest_update", "food_interest", "optional_marketing_reminder"),
        ]
    else:
        promote = [
            ("배송지 확인 필요", f"{app.subject} 주소가 확인되지 않아 배송이 보류되었습니다.", "address_action", "parcel_address_action", "concrete_user_confirmation"),
            (app.name, "수취인 부재로 배송하지 못했습니다. 재배송 방법을 선택해주세요.", "delivery_exception", "parcel_delivery_exception", "concrete_failure_or_exception"),
            ("반송 예정 안내", f"보관 기한이 지나면 {app.subject}이 반송됩니다. 수령 방법을 확인해주세요.", "deadline_action", "parcel_deadline", "deadline_with_action"),
            ("배송 상태 확인", "운송 중 문제가 발생해 도착 예정일이 변경되었습니다.", "schedule_change", "parcel_schedule_change", "meaningful_schedule_change"),
        ]
        keep = [
            ("(광고) 고객 이벤트", f"{app.offer}를 확인해보세요. 수신거부는 설정에서 가능합니다.", "promotion", "parcel_promotion", "explicit_promotion"),
            ("배송 서비스 만족도 조사", "최근 이용한 배송 서비스에 대한 의견을 남겨주세요.", "optional_survey", "parcel_survey", "optional_participation_request"),
            ("이번 달 배송 요약", "이번 달 받은 택배 기록을 확인해보세요.", "summary", "parcel_summary", "informational_summary"),
            (app.name, "택배 이용에 도움이 되는 생활 정보를 확인해보세요.", "recommendation", "parcel_content", "personalized_recommendation"),
        ]
    return promote, keep


def build_realistic_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    row_number = 1
    for app in BRANDS:
        promote, keep = scenarios_for(app)
        for label, scenarios in ((1, promote), (0, keep)):
            for title, body, notification_type, group, reason in scenarios:
                rows.append(
                    make_row(
                        row_id=f"V03_REALISTIC_{row_number:03d}",
                        app=app,
                        title=title,
                        body=body,
                        label=label,
                        notification_type=notification_type,
                        template_group=f"v03_{app.domain}_{group}",
                        reason_code=reason,
                        android_category=("promo" if notification_type == "promotion" else "msg"),
                    )
                )
                row_number += 1
    return rows


def main() -> None:
    if not V02_TRAIN_PATH.exists() or not V02_CONTEXT_PATH.exists():
        raise FileNotFoundError("먼저 python src/generate_dataset_v02.py 를 실행하세요.")

    train_rows = [migrate_v02(row) for row in read_csv(V02_TRAIN_PATH)]
    train_rows.extend(build_realistic_rows())
    context_rows = [migrate_v02(row) for row in read_csv(V02_CONTEXT_PATH)]

    write_csv(TRAIN_OUTPUT_PATH, train_rows)
    write_csv(CONTEXT_OUTPUT_PATH, context_rows)
    write_csv(PUBLIC_EVALUATION_PATH, [])

    print("v0.3 데이터 생성 완료")
    print(f"학습·대조 데이터: {len(train_rows)}개")
    print(f"  - v0.2 이관: {len(train_rows) - len(build_realistic_rows())}개")
    print(f"  - 현실형 신규: {len(build_realistic_rows())}개")
    print(f"문맥 의존 데이터: {len(context_rows)}개")
    print("공개 실데이터 평가 파일: 0개 (원문 수집 후 UNLABELED로 추가)")


if __name__ == "__main__":
    main()
