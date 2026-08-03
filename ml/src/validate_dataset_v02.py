import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
TRAIN_DATA_PATH = PROJECT_DIR / "data" / "public" / "train_notifications_v0.2.csv"
CONTEXT_DATA_PATH = (
    PROJECT_DIR / "data" / "public" / "context_notifications_v0.2.csv"
)

REQUIRED_COLUMNS = {
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
}

SUSPICIOUS_FRAGMENTS = (
    "정보 정보",
    "일정 일정",
    "리포트 주간 리포트",
    "설문에 대한 간단한 설문",
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return reader.fieldnames or [], list(reader)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def parse_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"boolean 값이 아닙니다: {value}")


def expected_level(score: int) -> str:
    if score >= 40:
        return "IMPORTANT"
    if score >= 25:
        return "REVIEW"
    return "GENERAL"


def validate() -> list[str]:
    errors: list[str] = []

    for path in (TRAIN_DATA_PATH, CONTEXT_DATA_PATH):
        if not path.exists():
            errors.append(f"파일이 없습니다: {path}")

    if errors:
        return errors

    train_columns, train_rows = read_csv(TRAIN_DATA_PATH)
    context_columns, context_rows = read_csv(CONTEXT_DATA_PATH)

    for path, columns in (
        (TRAIN_DATA_PATH, train_columns),
        (CONTEXT_DATA_PATH, context_columns),
    ):
        missing = REQUIRED_COLUMNS - set(columns)
        if missing:
            errors.append(f"{path.name}: 필수 컬럼 누락 {sorted(missing)}")

    if len(train_rows) != 320:
        errors.append(f"학습·대조 데이터는 320개여야 합니다: {len(train_rows)}")

    if len(context_rows) != 80:
        errors.append(f"문맥 의존 데이터는 80개여야 합니다: {len(context_rows)}")

    all_rows = train_rows + context_rows
    ids = [row["id"] for row in all_rows]
    duplicate_ids = [item for item, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"중복 ID가 있습니다: {duplicate_ids[:5]}")

    normalized_notifications: dict[str, list[str]] = defaultdict(list)
    app_counts = Counter(row["app_name"] for row in all_rows)

    for row in all_rows:
        row_id = row["id"]

        if not row["title"].strip() and not row["body"].strip():
            errors.append(f"{row_id}: 제목과 본문이 모두 비어 있습니다")

        normalized = normalize_text(f'{row["title"]} {row["body"]}')
        normalized_notifications[normalized].append(row_id)

        for fragment in SUSPICIOUS_FRAGMENTS:
            if fragment in row["body"]:
                errors.append(f"{row_id}: 어색한 반복 표현이 있습니다 ({fragment})")

        try:
            score = int(row["rule_score"])
            forced = parse_bool(row["forced"])
            model_eligible = parse_bool(row["model_eligible"])
            parse_bool(row["is_ongoing"])
        except ValueError as error:
            errors.append(f"{row_id}: {error}")
            continue

        level = expected_level(score)
        if row["rule_level"] != level:
            errors.append(
                f"{row_id}: rule_level={row['rule_level']}, 예상값={level}"
            )

        expected_eligible = not forced and level == "REVIEW"
        if model_eligible != expected_eligible:
            errors.append(
                f"{row_id}: model_eligible={model_eligible}, "
                f"예상값={expected_eligible}"
            )

        if row["dataset_version"] != "0.2":
            errors.append(f"{row_id}: dataset_version이 0.2가 아닙니다")

    duplicate_notifications = [
        row_ids
        for row_ids in normalized_notifications.values()
        if len(row_ids) > 1
    ]
    if duplicate_notifications:
        errors.append(
            "동일한 제목·본문이 중복됩니다: "
            f"{duplicate_notifications[:3]}"
        )

    for row in train_rows:
        if row["clarity"] != "CLEAR":
            errors.append(f"{row['id']}: 학습 데이터 clarity는 CLEAR여야 합니다")
        if row["label"] not in {"0", "1"}:
            errors.append(f"{row['id']}: 학습 데이터 label은 0 또는 1이어야 합니다")

    for row in context_rows:
        if row["clarity"] != "CONTEXT_DEPENDENT":
            errors.append(
                f"{row['id']}: 문맥 데이터 clarity는 CONTEXT_DEPENDENT여야 합니다"
            )
        if row["label"] != "":
            errors.append(f"{row['id']}: 문맥 데이터 label은 비어 있어야 합니다")

    train_label_counts = Counter(row["label"] for row in train_rows)
    if train_label_counts != Counter({"0": 160, "1": 160}):
        errors.append(f"전체 라벨 균형이 맞지 않습니다: {dict(train_label_counts)}")

    eligible_rows = [
        row for row in train_rows if row["model_eligible"] == "true"
    ]
    eligible_label_counts = Counter(row["label"] for row in eligible_rows)
    if len(eligible_rows) != 240:
        errors.append(f"REVIEW 학습 대상은 240개여야 합니다: {len(eligible_rows)}")
    if eligible_label_counts != Counter({"0": 120, "1": 120}):
        errors.append(
            f"REVIEW 라벨 균형이 맞지 않습니다: {dict(eligible_label_counts)}"
        )

    labels_by_app: dict[str, Counter[str]] = defaultdict(Counter)
    for row in train_rows:
        labels_by_app[row["app_name"]][row["label"]] += 1

    for app_name, counts in labels_by_app.items():
        if set(counts) != {"0", "1"}:
            errors.append(f"{app_name}: 두 라벨이 모두 존재하지 않습니다")
            continue

        total = sum(counts.values())
        largest_share = max(counts.values()) / total
        if largest_share > 0.7:
            errors.append(
                f"{app_name}: 한 라벨 비중이 70%를 넘습니다 ({largest_share:.1%})"
            )

    total_count = len(all_rows)
    for app_name, count in app_counts.items():
        share = count / total_count
        if share > 0.05:
            errors.append(f"{app_name}: 전체 비중이 5%를 넘습니다 ({share:.1%})")

    return errors


def print_summary() -> None:
    _, train_rows = read_csv(TRAIN_DATA_PATH)
    _, context_rows = read_csv(CONTEXT_DATA_PATH)

    eligible_rows = [
        row for row in train_rows if row["model_eligible"] == "true"
    ]

    print("v0.2 데이터 품질 검사")
    print(f"학습·대조 데이터: {len(train_rows)}")
    print(f"문맥 의존 데이터: {len(context_rows)}")
    print(f"REVIEW 학습 대상: {len(eligible_rows)}")
    print(f"전체 Label: {dict(Counter(row['label'] for row in train_rows))}")
    print(
        "REVIEW Label: "
        f"{dict(Counter(row['label'] for row in eligible_rows))}"
    )
    print(f"앱 개수: {len(set(row['app_name'] for row in train_rows))}")
    print(
        "알림 유형 개수: "
        f"{len(set(row['notification_type'] for row in train_rows))}"
    )


def main() -> None:
    errors = validate()

    if errors:
        print("v0.2 데이터 품질 검사 실패")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    print_summary()
    print("결과: PASS")


if __name__ == "__main__":
    main()
