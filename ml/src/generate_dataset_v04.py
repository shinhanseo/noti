import csv
from collections import defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_DIR / "data" / "public"

V03_TRAIN_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.3.csv"
V03_CONTEXT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.3.csv"
V03_PUBLIC_EVALUATION_PATH = PUBLIC_DATA_DIR / "public_evaluation_v0.3.csv"
V03_SOURCE_MANIFEST_PATH = PUBLIC_DATA_DIR / "source_manifest_v0.3.csv"

TRAIN_OUTPUT_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.4.csv"
CONTEXT_OUTPUT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.4.csv"
PUBLIC_EVALUATION_OUTPUT_PATH = PUBLIC_DATA_DIR / "public_evaluation_v0.4.csv"
SOURCE_MANIFEST_OUTPUT_PATH = PUBLIC_DATA_DIR / "source_manifest_v0.4.csv"
REVIEW_OUTPUT_PATH = PUBLIC_DATA_DIR / "review_notifications_v0.4.csv"

V04_FIELDS = [
    "previous_label",
    "event_type",
    "actionability",
    "base_label",
    "preference_sensitive",
    "personalization_scope",
    "training_eligible",
    "base_label_status",
    "label_definition_version",
]

ACTION_REQUIRED_TYPES = {
    "action_required",
    "address_action",
    "autopay_failure",
    "card_declined",
    "deadline_action",
    "delivery_exception",
    "exception",
    "payment_failure",
    "refund_exception",
    "security_change",
    "suspicious_payment",
    "transfer_hold",
    "urgent_action",
}

ATTENTION_WORTHY_TYPES = {
    "delivery_status",
    "order_cancelled",
    "payment_status",
    "schedule_change",
}

INFORMATIONAL_TYPES = {
    "interest_update",
    "passive_update",
    "summary",
}

PROMOTIONAL_TYPES = {
    "cart_reminder",
    "optional_event",
    "optional_schedule",
    "optional_survey",
    "price_drop",
    "promotion",
    "recommendation",
}

PREFERENCE_SENSITIVE_TYPES = {
    "cart_reminder",
    "delivery_status",
    "interest_update",
    "optional_event",
    "optional_schedule",
    "order_cancelled",
    "passive_update",
    "price_drop",
    "recommendation",
    "schedule_change",
    "summary",
}

EVENT_TYPE_BY_NOTIFICATION_TYPE = {
    "action_required": "USER_ACTION",
    "address_action": "ADDRESS_ACTION",
    "autopay_failure": "PAYMENT_PROBLEM",
    "card_declined": "PAYMENT_PROBLEM",
    "cart_reminder": "CART_REMINDER",
    "deadline_action": "DEADLINE_ACTION",
    "delivery_exception": "DELIVERY_PROBLEM",
    "delivery_status": "DELIVERY_STATUS",
    "exception": "PROCESS_FAILURE",
    "interest_update": "INTEREST_UPDATE",
    "optional_event": "OPTIONAL_EVENT",
    "optional_schedule": "OPTIONAL_CONTENT",
    "optional_survey": "SURVEY",
    "order_cancelled": "ORDER_STATUS",
    "passive_update": "PASSIVE_STATUS",
    "payment_failure": "PAYMENT_PROBLEM",
    "payment_status": "PAYMENT_STATUS",
    "price_drop": "PRICE_DROP",
    "promotion": "PROMOTION",
    "recommendation": "RECOMMENDATION",
    "refund_exception": "REFUND_PROBLEM",
    "schedule_change": "SCHEDULE_CHANGE",
    "security_change": "SECURITY",
    "summary": "SUMMARY",
    "suspicious_payment": "SECURITY",
    "transfer_hold": "PAYMENT_PROBLEM",
    "urgent_action": "URGENT_ACTION",
    "relationship_message": "MESSAGE",
    "personal_schedule": "PERSONAL_SCHEDULE",
    "personal_habit": "PERSONAL_REMINDER",
}

REVIEW_SAMPLE_COUNTS = {
    "delivery_status": 3,
    "payment_status": 3,
    "schedule_change": 4,
    "order_cancelled": 3,
    "summary": 2,
    "price_drop": 1,
    "cart_reminder": 1,
    "optional_schedule": 2,
    "relationship_message": 3,
    "personal_schedule": 3,
    "interest_update": 3,
    "personal_habit": 2,
}

DELIVERY_SEEDS = (
    ("쿠팡", "coupang", "배송 출발", "주문하신 상품이 배송을 시작했습니다. 오늘 오후 도착 예정입니다."),
    ("오늘의집", "ohouse", "배송이 시작됐어요", "주문하신 가구가 출고되어 내일 도착할 예정이에요."),
    ("네이버 쇼핑", "naver_shopping", "상품 발송 안내", "판매자가 상품을 발송했습니다. 도착 예정일은 내일입니다."),
    ("무신사", "musinsa", "배송 시작", "주문 상품이 택배사로 전달됐습니다. 오늘 밤 도착 예정입니다."),
    ("지그재그", "zigzag", "배송 예정", "주문하신 상품이 이동 중이며 오늘 오후 도착할 예정입니다."),
    ("에이블리", "ably", "상품이 출발했어요", "주문 상품이 출고됐습니다. 내일 오전 도착 예정이에요."),
    ("올리브영", "oliveyoung", "오늘 도착 예정", "주문 상품이 배송 중이며 오늘 오후 도착할 예정입니다."),
    ("11번가", "elevenst", "배송 출발 안내", "상품이 발송되어 내일 도착할 예정입니다."),
    ("CJ대한통운", "cjlogistics", "배송 출발", "택배가 배송지로 출발했습니다. 오늘 오후 도착 예정입니다."),
    ("한진택배", "hanjin", "배송 예정 안내", "택배가 이동 중입니다. 오늘 저녁 도착할 예정입니다."),
)

PAYMENT_STATUS_SEEDS = (
    ("토스", "toss", "입금 완료", "계좌로 입금이 완료되었습니다. 거래 내역을 확인할 수 있습니다."),
    ("카카오뱅크", "kakaobank", "이체 완료", "요청하신 계좌이체가 정상적으로 완료되었습니다."),
    ("신한 SOL페이", "shinhan_solpay", "결제 승인", "카드 결제가 정상적으로 승인되었습니다."),
    ("KB Pay", "kbpay", "결제 완료", "요청하신 카드 결제가 완료되었습니다."),
    ("현대카드", "hyundaicard", "이용 알림", "카드 이용이 정상적으로 승인되었습니다."),
    ("삼성카드", "samsungcard", "승인 완료", "카드 결제가 승인되었습니다. 이용 내역에서 확인할 수 있습니다."),
    ("카카오페이", "kakaopay", "송금 완료", "요청하신 송금이 정상적으로 완료되었습니다."),
    ("네이버페이", "naverpay", "결제 완료", "네이버페이 결제가 정상적으로 완료되었습니다."),
    ("쿠팡", "coupang", "결제 완료", "주문 상품의 결제가 정상적으로 완료되었습니다."),
    ("배달의민족", "baemin", "주문 결제 완료", "배달 주문 결제가 정상적으로 완료되었습니다."),
)

REVIEW_FIELDS = [
    "id",
    "app_name",
    "title",
    "body",
    "source_dataset",
    "previous_label",
    "proposed_event_type",
    "proposed_actionability",
    "proposed_base_label",
    "proposed_preference_sensitive",
    "why_selected",
    "user_actionability",
    "user_preference_sensitive",
    "review_note",
]

USER_REVIEW_DECISIONS = {
    "V04_REALISTIC_001": ("ATTENTION_WORTHY", "true", ""),
    "V04_REALISTIC_007": ("ATTENTION_WORTHY", "true", ""),
    "V04_REALISTIC_013": ("ATTENTION_WORTHY", "true", ""),
    "V04_REALISTIC_021": ("ATTENTION_WORTHY", "false", ""),
    "V04_REALISTIC_027": ("ATTENTION_WORTHY", "false", ""),
    "V04_REALISTIC_033": ("ATTENTION_WORTHY", "false", ""),
    "V02_TRAIN_003": ("ATTENTION_WORTHY", "false", ""),
    "V02_TRAIN_083": ("ATTENTION_WORTHY", "false", ""),
    "V02_TRAIN_163": ("ATTENTION_WORTHY", "false", ""),
    "V02_TRAIN_243": ("ATTENTION_WORTHY", "true", ""),
    "V03_REALISTIC_003": ("ATTENTION_WORTHY", "true", ""),
    "V03_REALISTIC_035": ("ATTENTION_WORTHY", "true", ""),
    "V03_REALISTIC_067": ("ATTENTION_WORTHY", "true", ""),
    "V02_TRAIN_007": ("INFORMATIONAL", "true", ""),
    "V02_TRAIN_199": ("INFORMATIONAL", "true", ""),
    "V03_REALISTIC_007": ("PROMOTIONAL", "true", ""),
    "V03_REALISTIC_005": (
        "PROMOTIONAL",
        "true",
        "actionability 미입력; 정책 제안값 유지",
    ),
    "V02_TRAIN_009": ("PROMOTIONAL", "true", ""),
    "V02_TRAIN_169": ("PROMOTIONAL", "true", ""),
    "V02_CONTEXT_001": ("INFORMATIONAL", "true", ""),
    "V02_CONTEXT_025": ("INFORMATIONAL", "true", ""),
    "V02_CONTEXT_049": ("INFORMATIONAL", "true", ""),
    "V02_CONTEXT_002": ("INFORMATIONAL", "true", ""),
    "V02_CONTEXT_026": ("INFORMATIONAL", "true", ""),
    "V02_CONTEXT_050": ("INFORMATIONAL", "true", ""),
    "V03_REALISTIC_128": ("INFORMATIONAL", "true", ""),
    "V02_CONTEXT_023": ("INFORMATIONAL", "true", ""),
    "V02_CONTEXT_051": ("INFORMATIONAL", "true", ""),
    "V02_CONTEXT_004": ("INFORMATIONAL", "true", ""),
    "V02_CONTEXT_044": ("INFORMATIONAL", "true", ""),
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return reader.fieldnames or [], list(reader)


def write_csv(
    path: Path,
    field_names: list[str],
    rows: list[dict[str, object]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=field_names,
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def classify_actionability(notification_type: str) -> str:
    if notification_type in ACTION_REQUIRED_TYPES:
        return "ACTION_REQUIRED"
    if notification_type in ATTENTION_WORTHY_TYPES:
        return "ATTENTION_WORTHY"
    if notification_type in INFORMATIONAL_TYPES:
        return "INFORMATIONAL"
    if notification_type in PROMOTIONAL_TYPES:
        return "PROMOTIONAL"
    raise ValueError(f"지원하지 않는 notification_type: {notification_type}")


def migrate_train_row(row: dict[str, str]) -> dict[str, object]:
    notification_type = row["notification_type"]
    actionability = classify_actionability(notification_type)
    base_label = 1 if actionability in {"ACTION_REQUIRED", "ATTENTION_WORTHY"} else 0
    preference_sensitive = notification_type in PREFERENCE_SENSITIVE_TYPES
    review_decision = USER_REVIEW_DECISIONS.get(row["id"])
    if review_decision is not None:
        reviewed_actionability, reviewed_preference, _ = review_decision
        if reviewed_actionability != actionability:
            raise ValueError(
                f"{row['id']}: 정책과 사용자 검수 actionability가 다릅니다 "
                f"({actionability} != {reviewed_actionability})"
            )
        preference_sensitive = reviewed_preference == "true"

    migrated: dict[str, object] = dict(row)
    migrated.update(
        {
            "previous_label": row["label"],
            "label": base_label,
            "event_type": EVENT_TYPE_BY_NOTIFICATION_TYPE[notification_type],
            "actionability": actionability,
            "base_label": base_label,
            "preference_sensitive": str(preference_sensitive).lower(),
            "personalization_scope": (
                "APP_EVENT_TYPE" if preference_sensitive else "NONE"
            ),
            "training_eligible": "true",
            "base_label_status": (
                "HUMAN_REVIEWED_V04"
                if review_decision is not None
                else "POLICY_APPROVED_V04"
            ),
            "label_definition_version": "0.4",
            "dataset_version": "0.4",
            "label_status": (
                "HUMAN_REVIEWED"
                if review_decision is not None
                else row["label_status"]
            ),
        }
    )
    return migrated


def make_v04_seed_rows(
    base_fields: list[str],
) -> list[dict[str, str]]:
    seed_rows: list[dict[str, str]] = []
    row_number = 1
    seed_groups = (
        ("delivery_status", "delivery_status_personal_preference", DELIVERY_SEEDS),
        ("payment_status", "completed_financial_status_personal_preference", PAYMENT_STATUS_SEEDS),
    )

    for notification_type, reason_code, seeds in seed_groups:
        for app_name, slug, title, body in seeds:
            variants = (
                (title, body, "a"),
                (
                    app_name,
                    body.replace("정상적으로 ", "").replace("주문하신 ", ""),
                    "b",
                ),
            )
            for variant_title, variant_body, variant in variants:
                values = {
                    "id": f"V04_REALISTIC_{row_number:03d}",
                    "app_name": app_name,
                    "package_name": f"synthetic.brand.{slug}",
                    "title": variant_title,
                    "body": variant_body,
                    "label": "",
                    "notification_type": notification_type,
                    "template_group": f"v04_{notification_type}_{variant}",
                    "clarity": "CLEAR",
                    "reason_code": reason_code,
                    "android_category": "msg",
                    "is_ongoing": "false",
                    "rule_score": "30" if notification_type == "delivery_status" else "25",
                    "rule_level": "REVIEW",
                    "forced": "false",
                    "model_eligible": "true",
                    "source": "SYNTHETIC_PERSONALIZATION_REVIEWED",
                    "dataset_version": "0.3",
                    "source_detail": "v0.4_personalization_seed_written_for_noti",
                    "source_url": "",
                    "license": "PROJECT_OWNED",
                    "is_real": "false",
                    "is_public": "true",
                    "label_status": "POLICY_REVIEWED",
                    "original_source_id": "",
                }
                seed_rows.append({field: values.get(field, "") for field in base_fields})
                row_number += 1

    return seed_rows


def migrate_context_row(row: dict[str, str]) -> dict[str, object]:
    notification_type = row["notification_type"]
    migrated: dict[str, object] = dict(row)
    migrated.update(
        {
            "previous_label": row["label"],
            "event_type": EVENT_TYPE_BY_NOTIFICATION_TYPE[notification_type],
            "actionability": "",
            "base_label": "",
            "preference_sensitive": "true",
            "personalization_scope": "APP_EVENT_TYPE",
            "training_eligible": "false",
            "base_label_status": "UNLABELED_CONTEXT",
            "label_definition_version": "0.4",
            "dataset_version": "0.4",
        }
    )
    return migrated


def migrate_evaluation_row(row: dict[str, str]) -> dict[str, object]:
    migrated: dict[str, object] = dict(row)
    migrated.update(
        {
            "previous_label": row.get("label", ""),
            "event_type": "",
            "actionability": "",
            "base_label": "",
            "preference_sensitive": "",
            "personalization_scope": "",
            "training_eligible": "false",
            "base_label_status": "UNLABELED",
            "label_definition_version": "0.4",
            "dataset_version": "0.4",
        }
    )
    return migrated


def select_review_rows(
    train_rows: list[dict[str, object]],
    context_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    candidates: dict[str, list[tuple[str, dict[str, object]]]] = defaultdict(list)
    for source_dataset, rows in (
        ("train_v0.4", train_rows),
        ("context_v0.4", context_rows),
    ):
        for row in rows:
            candidates[str(row["notification_type"])].append((source_dataset, row))

    review_rows: list[dict[str, object]] = []
    for notification_type, count in REVIEW_SAMPLE_COUNTS.items():
        rows = candidates[notification_type]
        if len(rows) < count:
            raise ValueError(
                f"{notification_type} 검수 후보가 부족합니다: {len(rows)} < {count}"
            )

        step = max(1, len(rows) // count)
        selected = [rows[index] for index in range(0, len(rows), step)][:count]
        for source_dataset, row in selected:
            actionability = str(row["actionability"])
            proposed_base_label = str(row["base_label"])
            proposed_preference_sensitive = str(
                str(row["notification_type"]) in PREFERENCE_SENSITIVE_TYPES
            ).lower()
            if source_dataset == "context_v0.4":
                actionability = "INFORMATIONAL"
                proposed_base_label = "0"
                proposed_preference_sensitive = "true"

            review_rows.append(
                {
                    "id": row["id"],
                    "app_name": row["app_name"],
                    "title": row["title"],
                    "body": row["body"],
                    "source_dataset": source_dataset,
                    "previous_label": row["previous_label"],
                    "proposed_event_type": row["event_type"],
                    "proposed_actionability": actionability,
                    "proposed_base_label": proposed_base_label,
                    "proposed_preference_sensitive": proposed_preference_sensitive,
                    "why_selected": notification_type,
                    "user_actionability": USER_REVIEW_DECISIONS[str(row["id"])][0],
                    "user_preference_sensitive": USER_REVIEW_DECISIONS[str(row["id"])][1],
                    "review_note": USER_REVIEW_DECISIONS[str(row["id"])][2],
                }
            )
    return review_rows


def build_source_manifest(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    migrated = [dict(row) for row in rows]
    migrated.append(
        {
            "source_id": "noti_v04_policy_migration",
            "name": "noti v0.4 actionability policy migration",
            "url": "",
            "license": "PROJECT_OWNED",
            "intended_use": "TRAIN_AND_PERSONALIZATION_DESIGN",
            "status": "INCLUDED",
            "notes": (
                "480 v0.3 rows relabeled as actionability; personal preference is "
                "kept separate from the shared base label"
            ),
        }
    )
    migrated.append(
        {
            "source_id": "noti_v04_personalization_seeds",
            "name": "delivery and completed-payment personalization seeds",
            "url": "",
            "license": "PROJECT_OWNED",
            "intended_use": "TRAIN",
            "status": "INCLUDED",
            "notes": (
                "40 policy-reviewed synthetic rows for normal delivery and completed "
                "financial status; no copied production message text"
            ),
        }
    )
    return migrated


def main() -> None:
    required_paths = (
        V03_TRAIN_PATH,
        V03_CONTEXT_PATH,
        V03_PUBLIC_EVALUATION_PATH,
        V03_SOURCE_MANIFEST_PATH,
    )
    missing_paths = [path.name for path in required_paths if not path.exists()]
    if missing_paths:
        raise FileNotFoundError(f"v0.3 입력 파일이 없습니다: {missing_paths}")

    train_fields, v03_train_rows = read_csv(V03_TRAIN_PATH)
    _, v03_context_rows = read_csv(V03_CONTEXT_PATH)
    _, v03_evaluation_rows = read_csv(V03_PUBLIC_EVALUATION_PATH)
    manifest_fields, v03_manifest_rows = read_csv(V03_SOURCE_MANIFEST_PATH)

    output_fields = train_fields + V04_FIELDS
    train_seed_rows = v03_train_rows + make_v04_seed_rows(train_fields)
    train_rows = [migrate_train_row(row) for row in train_seed_rows]
    context_rows = [migrate_context_row(row) for row in v03_context_rows]
    evaluation_rows = [migrate_evaluation_row(row) for row in v03_evaluation_rows]
    review_rows = select_review_rows(train_rows, context_rows)

    write_csv(TRAIN_OUTPUT_PATH, output_fields, train_rows)
    write_csv(CONTEXT_OUTPUT_PATH, output_fields, context_rows)
    write_csv(PUBLIC_EVALUATION_OUTPUT_PATH, output_fields, evaluation_rows)
    write_csv(REVIEW_OUTPUT_PATH, REVIEW_FIELDS, review_rows)
    write_csv(
        SOURCE_MANIFEST_OUTPUT_PATH,
        manifest_fields,
        build_source_manifest(v03_manifest_rows),
    )

    actionability_counts: dict[str, int] = defaultdict(int)
    for row in train_rows:
        actionability_counts[str(row["actionability"])] += 1

    print("v0.4 데이터 생성 완료")
    print(f"학습·대조 데이터: {len(train_rows)}개")
    print(f"문맥 의존 데이터: {len(context_rows)}개")
    print(f"사용자 검수 표본: {len(review_rows)}개")
    print(f"Actionability: {dict(actionability_counts)}")


if __name__ == "__main__":
    main()
