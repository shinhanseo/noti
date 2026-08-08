import csv
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_DIR / "data" / "public"

V04_TRAIN_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.4.csv"
V04_CONTEXT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.4.csv"
V04_PUBLIC_EVALUATION_PATH = PUBLIC_DATA_DIR / "public_evaluation_v0.4.csv"
V04_SOURCE_MANIFEST_PATH = PUBLIC_DATA_DIR / "source_manifest_v0.4.csv"

TRAIN_OUTPUT_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.5.csv"
CONTEXT_OUTPUT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.5.csv"
PUBLIC_EVALUATION_OUTPUT_PATH = PUBLIC_DATA_DIR / "public_evaluation_v0.5.csv"
SOURCE_MANIFEST_OUTPUT_PATH = PUBLIC_DATA_DIR / "source_manifest_v0.5.csv"

CV_FOLDS = 5
ACTIONABILITY_VALUES = (
    "ACTION_REQUIRED",
    "ATTENTION_WORTHY",
    "INFORMATIONAL",
    "PROMOTIONAL",
)

DELIVERY_PROFILES = (
    ("쿠팡", "coupang", "주문 상품"),
    ("오늘의집", "ohouse", "가구 주문"),
    ("CJ대한통운", "cjlogistics", "택배 물품"),
    ("컬리", "kurly", "식품 주문"),
)

PAYMENT_PROFILES = (
    ("토스", "toss", "계좌 거래"),
    ("카카오뱅크", "kakaobank", "이체 거래"),
    ("KB Pay", "kbpay", "카드 결제"),
    ("카카오페이", "kakaopay", "간편 결제"),
)

GENERAL_PROFILES = (
    ("네이버", "naver", "이용 기록"),
    ("Notion", "notion", "공유 문서"),
    ("에브리타임", "everytime", "학교 소식"),
    ("SmartThings", "smartthings", "기기 상태"),
)

ACTION_PROFILES = (
    ("토스", "toss", "자동이체"),
    ("쿠팡", "coupang", "상품 주문"),
    ("정부24", "gov24", "민원 신청"),
    ("Slack", "slack", "업무 요청"),
)

PROMOTION_PROFILES = (
    ("지역 소식", "local_campaign", "참여 안내"),
    ("쇼핑 소식", "shopping_push", "상품 혜택"),
    ("카드 소식", "card_push", "카드 혜택"),
    ("서비스 소식", "service_push", "서비스 이벤트"),
)

DELIVERY_TEMPLATES = (
    ("배송이 시작됐어요", "{subject}이 출고되었습니다. 오늘 오후 도착할 예정입니다."),
    ("오늘 배송 예정", "{subject}이 배송지로 이동 중이며 오늘 저녁 도착 예정입니다."),
    ("배송 기사 출발", "{subject}을 실은 차량이 출발했습니다. 오후 중 방문 예정입니다."),
    ("수령 예정 안내", "{subject}이 오전 10시부터 오후 8시 사이 도착할 예정입니다."),
    ("문 앞 배송 예정", "{subject}은 부재 시 문 앞에 전달될 예정입니다."),
    ("상품 발송 완료", "판매자가 {subject}을 발송했습니다. 내일 도착 예정입니다."),
    ("택배 이동 중", "{subject}이 가까운 배송 터미널에 도착했습니다."),
    ("도착 시간 안내", "{subject}의 예상 도착 시간이 오늘 오후로 등록되었습니다."),
)

PAYMENT_TEMPLATES = (
    ("입금 완료", "{subject}의 입금 처리가 완료되었습니다."),
    ("이체 완료", "요청하신 {subject}가 정상적으로 처리되었습니다."),
    ("결제 승인", "{subject}가 정상적으로 승인되었습니다."),
    ("환불 완료", "{subject}의 환불 금액이 계좌로 입금되었습니다."),
)

INFORMATIONAL_TEMPLATES = (
    ("주간 요약", "{subject}의 이번 주 요약이 새로 등록되었습니다."),
    ("기록 업데이트", "{subject}이 최신 내용으로 업데이트되었습니다."),
    ("새 소식", "{subject}과 관련된 일반 소식이 올라왔습니다."),
    ("이용 내역", "{subject}의 지난 이용 내역을 확인할 수 있습니다."),
    ("공지 등록", "{subject}에 새로운 공지가 등록되었습니다."),
    ("상태 안내", "{subject}이 정상 상태로 유지되고 있습니다."),
    ("문서 공유", "{subject}의 읽기 전용 문서가 공유되었습니다."),
    ("월간 리포트", "{subject}의 이번 달 리포트가 생성되었습니다."),
)

ACTION_TEMPLATES = (
    ("처리 실패", "{subject} 처리가 실패했습니다. 다시 확인해주세요."),
    ("보안 확인", "새로운 기기에서 {subject} 변경이 감지되었습니다. 본인이 아니라면 확인해주세요."),
    ("오늘까지 필요", "{subject} 관련 제출이 오늘 마감됩니다. 완료해주세요."),
    ("정보 확인 요청", "{subject} 정보가 부족해 처리가 중단되었습니다. 내용을 입력해주세요."),
    ("승인 요청", "{subject}에 대한 승인이 필요합니다. 요청을 확인해주세요."),
    ("계정 이용 제한", "{subject} 문제로 계정 이용이 제한되었습니다. 본인 확인이 필요합니다."),
    ("환불 오류", "{subject} 환불이 완료되지 않았습니다. 계좌 정보를 확인해주세요."),
    ("예약 확인 필요", "{subject} 예약을 유지하려면 오늘 안에 확인해주세요."),
)

PROMOTIONAL_TEMPLATES = (
    ("투표 참여 안내", "오늘 밤 9시까지 온라인 투표가 진행됩니다. 참여를 부탁드립니다."),
    ("캠페인 소식", "관심 있는 후보와 캠페인 소식을 확인하고 응원해주세요."),
    ("지역 참여 요청", "우리 지역 설문과 홍보 활동에 참여해주세요."),
    ("멀티미디어 메시지", "메시지 크기 12KB, 콘텐츠 만료는 이번 주 금요일 오후 6시입니다."),
    ("친구 초대", "친구를 초대하면 추가 혜택을 받을 수 있는 이벤트가 진행 중입니다."),
    ("만족도 조사", "최근 이용한 서비스에 대한 만족도 설문을 부탁드립니다."),
    ("의견을 들려주세요", "더 나은 서비스를 위한 간단한 설문에 참여해주세요."),
    ("오늘만 혜택", "오늘 자정까지 사용할 수 있는 한정 혜택을 확인해보세요."),
    ("쿠폰 도착", "이번 주에 사용할 수 있는 맞춤 쿠폰이 발급되었습니다."),
    ("추천 소식", "최근 관심 기록을 바탕으로 새로운 상품을 추천해드려요."),
    ("이벤트 마감 임박", "참여형 이벤트가 오늘 종료됩니다. 지금 확인해보세요."),
    ("구독 혜택 안내", "멤버십 이용자를 위한 이번 달 혜택이 공개되었습니다."),
)


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


def make_seed_row(
    *,
    row_id: str,
    app_name: str,
    slug: str,
    title: str,
    body: str,
    notification_type: str,
    event_type: str,
    actionability: str,
    template_group: str,
    preference_sensitive: bool,
    rule_score: int,
    base_fields: list[str],
) -> dict[str, object]:
    base_label = 1 if actionability in {"ACTION_REQUIRED", "ATTENTION_WORTHY"} else 0
    values: dict[str, object] = {
        "id": row_id,
        "app_name": app_name,
        "package_name": f"synthetic.v05.{slug}",
        "title": title,
        "body": body,
        "label": base_label,
        "notification_type": notification_type,
        "template_group": template_group,
        "clarity": "CLEAR",
        "reason_code": f"v05_{notification_type}_diversity",
        "android_category": "msg",
        "is_ongoing": "false",
        "rule_score": rule_score,
        "rule_level": "REVIEW",
        "forced": "false",
        "model_eligible": "true",
        "source": "SYNTHETIC_DIVERSITY_REVIEWED",
        "dataset_version": "0.5",
        "source_detail": "v0.5_diverse_korean_notification_templates",
        "source_url": "",
        "license": "PROJECT_OWNED",
        "is_real": "false",
        "is_public": "true",
        "label_status": "POLICY_REVIEWED",
        "original_source_id": "",
        "previous_label": "",
        "event_type": event_type,
        "actionability": actionability,
        "base_label": base_label,
        "preference_sensitive": str(preference_sensitive).lower(),
        "personalization_scope": (
            "APP_EVENT_TYPE" if preference_sensitive else "NONE"
        ),
        "training_eligible": "true",
        "base_label_status": "POLICY_APPROVED_V05",
        "label_definition_version": "0.4",
        "cv_fold": "",
    }
    return {field: values.get(field, "") for field in base_fields}


def build_rows_for_templates(
    *,
    start_number: int,
    profiles: tuple[tuple[str, str, str], ...],
    templates: tuple[tuple[str, str], ...],
    notification_type: str,
    event_type: str,
    actionability: str,
    preference_sensitive: bool,
    rule_score: int,
    base_fields: list[str],
) -> tuple[list[dict[str, object]], int]:
    rows: list[dict[str, object]] = []
    row_number = start_number
    for template_index, (title_template, body_template) in enumerate(templates, 1):
        for app_name, slug, subject in profiles:
            rows.append(
                make_seed_row(
                    row_id=f"V05_DIVERSITY_{row_number:03d}",
                    app_name=app_name,
                    slug=slug,
                    title=title_template.format(app=app_name, subject=subject),
                    body=body_template.format(app=app_name, subject=subject),
                    notification_type=notification_type,
                    event_type=event_type,
                    actionability=actionability,
                    template_group=f"v05_{notification_type}_{template_index:02d}",
                    preference_sensitive=preference_sensitive,
                    rule_score=rule_score,
                    base_fields=base_fields,
                )
            )
            row_number += 1
    return rows, row_number


def build_diversity_rows(base_fields: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    row_number = 1
    scenarios = (
        (DELIVERY_PROFILES, DELIVERY_TEMPLATES, "delivery_status", "DELIVERY_STATUS", "ATTENTION_WORTHY", True, 30),
        (PAYMENT_PROFILES, PAYMENT_TEMPLATES, "payment_status", "PAYMENT_STATUS", "ATTENTION_WORTHY", False, 25),
        (GENERAL_PROFILES, INFORMATIONAL_TEMPLATES, "general_information", "GENERAL_INFORMATION", "INFORMATIONAL", True, 25),
        (ACTION_PROFILES, ACTION_TEMPLATES, "diverse_action", "USER_ACTION", "ACTION_REQUIRED", False, 30),
        (PROMOTION_PROFILES, PROMOTIONAL_TEMPLATES, "disguised_promotion", "PROMOTION", "PROMOTIONAL", True, 25),
    )
    for profiles, templates, notification_type, event_type, actionability, preference_sensitive, rule_score in scenarios:
        scenario_rows, row_number = build_rows_for_templates(
            start_number=row_number,
            profiles=profiles,
            templates=templates,
            notification_type=notification_type,
            event_type=event_type,
            actionability=actionability,
            preference_sensitive=preference_sensitive,
            rule_score=rule_score,
            base_fields=base_fields,
        )
        rows.extend(scenario_rows)
    return rows


def fold_balance_score(
    fold_counts: list[Counter[str]],
    fold_sizes: list[int],
    class_targets: dict[str, float],
    size_target: float,
) -> float:
    score = 0.0
    for fold in range(CV_FOLDS):
        for value in ACTIONABILITY_VALUES:
            target = max(class_targets[value], 1.0)
            score += ((fold_counts[fold][value] - target) / target) ** 2
        score += 0.25 * ((fold_sizes[fold] - size_target) / size_target) ** 2
    return score


def assign_cv_folds(rows: list[dict[str, object]]) -> None:
    eligible_rows = [
        row
        for row in rows
        if str(row["model_eligible"]).lower() == "true"
        and str(row["training_eligible"]).lower() == "true"
        and row["clarity"] == "CLEAR"
    ]
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in eligible_rows:
        grouped[str(row["template_group"])].append(row)

    group_stats = []
    total_counts: Counter[str] = Counter()
    for group_name, group_rows in grouped.items():
        counts = Counter(str(row["actionability"]) for row in group_rows)
        total_counts.update(counts)
        group_stats.append((group_name, len(group_rows), counts))

    class_targets = {
        value: total_counts[value] / CV_FOLDS
        for value in ACTIONABILITY_VALUES
    }
    size_target = len(eligible_rows) / CV_FOLDS
    best_assignment: dict[str, int] | None = None
    best_score = math.inf

    for seed in range(500):
        randomizer = random.Random(seed)
        ordered = list(group_stats)
        randomizer.shuffle(ordered)
        ordered.sort(key=lambda item: -item[1])
        fold_counts = [Counter() for _ in range(CV_FOLDS)]
        fold_sizes = [0 for _ in range(CV_FOLDS)]
        assignment: dict[str, int] = {}

        for group_name, group_size, counts in ordered:
            candidates = []
            for fold in range(CV_FOLDS):
                next_counts = [Counter(value) for value in fold_counts]
                next_sizes = list(fold_sizes)
                next_counts[fold].update(counts)
                next_sizes[fold] += group_size
                candidates.append(
                    (
                        fold_balance_score(
                            next_counts,
                            next_sizes,
                            class_targets,
                            size_target,
                        ),
                        fold_sizes[fold],
                        fold,
                    )
                )
            selected_fold = min(candidates)[2]
            assignment[group_name] = selected_fold
            fold_counts[selected_fold].update(counts)
            fold_sizes[selected_fold] += group_size

        score = fold_balance_score(
            fold_counts,
            fold_sizes,
            class_targets,
            size_target,
        )
        if score < best_score:
            best_score = score
            best_assignment = assignment

    if best_assignment is None:
        raise RuntimeError("cv_fold 배정을 만들지 못했습니다.")
    for row in rows:
        row["cv_fold"] = (
            best_assignment.get(str(row["template_group"]), "")
            if row in eligible_rows
            else ""
        )


def migrate_rows(
    rows: list[dict[str, str]],
    output_fields: list[str],
) -> list[dict[str, object]]:
    migrated: list[dict[str, object]] = []
    for row in rows:
        values: dict[str, object] = dict(row)
        values["dataset_version"] = "0.5"
        values["cv_fold"] = ""
        migrated.append({field: values.get(field, "") for field in output_fields})
    return migrated


def main() -> None:
    required = (
        V04_TRAIN_PATH,
        V04_CONTEXT_PATH,
        V04_PUBLIC_EVALUATION_PATH,
        V04_SOURCE_MANIFEST_PATH,
    )
    missing = [path.name for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"v0.4 입력 파일이 없습니다: {missing}")

    train_fields, v04_train_rows = read_csv(V04_TRAIN_PATH)
    _, v04_context_rows = read_csv(V04_CONTEXT_PATH)
    _, v04_evaluation_rows = read_csv(V04_PUBLIC_EVALUATION_PATH)
    manifest_fields, manifest_rows = read_csv(V04_SOURCE_MANIFEST_PATH)
    output_fields = train_fields + ["cv_fold"]

    train_rows = migrate_rows(v04_train_rows, output_fields)
    diversity_rows = build_diversity_rows(output_fields)
    train_rows.extend(diversity_rows)
    assign_cv_folds(train_rows)
    context_rows = migrate_rows(v04_context_rows, output_fields)
    evaluation_rows = migrate_rows(v04_evaluation_rows, output_fields)

    manifest = [dict(row) for row in manifest_rows]
    manifest.append(
        {
            "source_id": "noti_v05_diversity_seeds",
            "name": "v0.5 delivery and disguised-promotion diversity seeds",
            "url": "",
            "license": "PROJECT_OWNED",
            "intended_use": "TRAIN",
            "status": "INCLUDED",
            "notes": (
                "160 policy-reviewed synthetic rows across delivery, payment, "
                "informational, action-required, and disguised-promotion templates"
            ),
        }
    )

    write_csv(TRAIN_OUTPUT_PATH, output_fields, train_rows)
    write_csv(CONTEXT_OUTPUT_PATH, output_fields, context_rows)
    write_csv(PUBLIC_EVALUATION_OUTPUT_PATH, output_fields, evaluation_rows)
    write_csv(SOURCE_MANIFEST_OUTPUT_PATH, manifest_fields, manifest)

    eligible = [row for row in train_rows if row["cv_fold"] != ""]
    print("v0.5 데이터 생성 완료")
    print(f"학습·대조 데이터: {len(train_rows)}개")
    print(f"신규 다양성 데이터: {len(diversity_rows)}개")
    print(f"모델 학습 대상: {len(eligible)}개")
    for fold in range(CV_FOLDS):
        fold_rows = [row for row in eligible if int(row["cv_fold"]) == fold]
        print(
            f"Fold {fold}: {len(fold_rows)}개 "
            f"{dict(Counter(row['actionability'] for row in fold_rows))}"
        )


if __name__ == "__main__":
    main()
