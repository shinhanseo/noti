import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_DIR / "data" / "public"
TRAIN_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.4.csv"
CONTEXT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.4.csv"
EVALUATION_PATH = PUBLIC_DATA_DIR / "public_evaluation_v0.4.csv"
REVIEW_PATH = PUBLIC_DATA_DIR / "review_notifications_v0.4.csv"

REQUIRED_COLUMNS = {
    "id",
    "app_name",
    "package_name",
    "title",
    "body",
    "label",
    "notification_type",
    "template_group",
    "model_eligible",
    "dataset_version",
    "previous_label",
    "event_type",
    "actionability",
    "base_label",
    "preference_sensitive",
    "personalization_scope",
    "training_eligible",
    "base_label_status",
    "label_definition_version",
}

EXPECTED_ACTIONABILITY_COUNTS = Counter(
    {
        "ACTION_REQUIRED": 186,
        "ATTENTION_WORTHY": 94,
        "INFORMATIONAL": 70,
        "PROMOTIONAL": 170,
    }
)

PII_PATTERNS = {
    "전화번호": re.compile(r"(?<!\d)01[016789][- ]?\d{3,4}[- ]?\d{4}(?!\d)"),
    "이메일": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "카드·계좌번호": re.compile(r"(?<!\d)(?:\d[- ]?){12,18}\d(?!\d)"),
}


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return reader.fieldnames or [], list(reader)


def normalize_text(value: str) -> str:
    value = re.sub(r"\(광고\)|\[광고\]", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\d+", "<num>", value)
    return re.sub(r"\s+", " ", value.strip().lower())


def validate() -> list[str]:
    errors: list[str] = []
    for path in (TRAIN_PATH, CONTEXT_PATH, EVALUATION_PATH, REVIEW_PATH):
        if not path.exists():
            errors.append(f"파일이 없습니다: {path.name}")
    if errors:
        return errors

    train_columns, train_rows = read_csv(TRAIN_PATH)
    context_columns, context_rows = read_csv(CONTEXT_PATH)
    evaluation_columns, evaluation_rows = read_csv(EVALUATION_PATH)
    review_columns, review_rows = read_csv(REVIEW_PATH)

    for path, columns in (
        (TRAIN_PATH, train_columns),
        (CONTEXT_PATH, context_columns),
        (EVALUATION_PATH, evaluation_columns),
    ):
        missing = REQUIRED_COLUMNS - set(columns)
        if missing:
            errors.append(f"{path.name}: 필수 컬럼 누락 {sorted(missing)}")

    required_review_columns = {
        "id",
        "source_dataset",
        "proposed_actionability",
        "proposed_base_label",
        "proposed_preference_sensitive",
        "user_actionability",
        "user_preference_sensitive",
        "review_note",
    }
    missing_review_columns = required_review_columns - set(review_columns)
    if missing_review_columns:
        errors.append(f"검수 파일 필수 컬럼 누락: {sorted(missing_review_columns)}")

    all_rows = train_rows + context_rows + evaluation_rows
    ids = [row["id"] for row in all_rows]
    duplicate_ids = [value for value, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"중복 ID: {duplicate_ids[:5]}")

    exact_texts: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in all_rows:
        row_id = row["id"]
        text = f'{row["title"]} {row["body"]}'.strip()
        if not text:
            errors.append(f"{row_id}: 제목과 본문이 모두 비어 있습니다")
            continue

        exact_texts[normalize_text(text)].append(row)
        if row["dataset_version"] != "0.4":
            errors.append(f"{row_id}: dataset_version이 0.4가 아닙니다")
        if row["label_definition_version"] != "0.4":
            errors.append(f"{row_id}: label_definition_version 오류")
        if row["training_eligible"] not in {"true", "false"}:
            errors.append(f"{row_id}: training_eligible boolean 오류")

        for name, pattern in PII_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{row_id}: 마스킹되지 않은 {name} 의심 값")

    unsafe_duplicates = []
    for rows in exact_texts.values():
        if len(rows) < 2:
            continue
        labels = {row["base_label"] for row in rows}
        event_types = {row["event_type"] for row in rows}
        if len(labels) > 1 or len(event_types) > 1:
            unsafe_duplicates.append([row["id"] for row in rows])
    if unsafe_duplicates:
        errors.append(f"동일 문장의 라벨·이벤트 충돌: {unsafe_duplicates[:3]}")

    for row in train_rows:
        if row["actionability"] not in {
            "ACTION_REQUIRED",
            "ATTENTION_WORTHY",
            "INFORMATIONAL",
            "PROMOTIONAL",
        }:
            errors.append(f"{row['id']}: actionability 오류")
        expected_label = (
            "1"
            if row["actionability"] in {"ACTION_REQUIRED", "ATTENTION_WORTHY"}
            else "0"
        )
        if row["base_label"] != expected_label or row["label"] != expected_label:
            errors.append(f"{row['id']}: actionability와 base_label 불일치")
        if row["preference_sensitive"] not in {"true", "false"}:
            errors.append(f"{row['id']}: preference_sensitive boolean 오류")
        if row["training_eligible"] != "true":
            errors.append(f"{row['id']}: 학습 데이터 training_eligible 오류")
        if row["base_label_status"] not in {
            "POLICY_APPROVED_V04",
            "HUMAN_REVIEWED_V04",
        }:
            errors.append(f"{row['id']}: base_label_status 오류")
        if not row["event_type"]:
            errors.append(f"{row['id']}: event_type 누락")

    for row in context_rows:
        if row["label"] or row["base_label"] or row["actionability"]:
            errors.append(f"{row['id']}: 문맥 데이터에 공통 정답이 들어갔습니다")
        if row["preference_sensitive"] != "true":
            errors.append(f"{row['id']}: 문맥 데이터 preference_sensitive 오류")
        if row["training_eligible"] != "false":
            errors.append(f"{row['id']}: 문맥 데이터가 학습 대상으로 설정됐습니다")
        if row["base_label_status"] != "UNLABELED_CONTEXT":
            errors.append(f"{row['id']}: 문맥 데이터 label 상태 오류")

    for row in evaluation_rows:
        if row["label"] or row["base_label"] or row["training_eligible"] == "true":
            errors.append(f"{row['id']}: 공개 평가 데이터가 학습 대상으로 설정됐습니다")

    actionability_counts = Counter(row["actionability"] for row in train_rows)
    if actionability_counts != EXPECTED_ACTIONABILITY_COUNTS:
        errors.append(
            "actionability 분포가 예상과 다릅니다: "
            f"{dict(actionability_counts)}"
        )

    base_label_counts = Counter(row["base_label"] for row in train_rows)
    if base_label_counts != Counter({"1": 280, "0": 240}):
        errors.append(f"base_label 분포 오류: {dict(base_label_counts)}")

    changed_rows = [
        row
        for row in train_rows
        if row["id"].startswith(("V02_", "V03_"))
        and row["previous_label"] != row["label"]
    ]
    if changed_rows:
        errors.append(f"v0.3 이관 데이터의 기존 방향이 변경됐습니다: {len(changed_rows)}")
    changed_types = Counter(row["notification_type"] for row in changed_rows)
    if changed_types:
        errors.append(f"변경 라벨 유형 오류: {dict(changed_types)}")

    if len(review_rows) != 30:
        errors.append(f"검수 표본은 30개여야 합니다: {len(review_rows)}")
    if len({row["id"] for row in review_rows}) != len(review_rows):
        errors.append("검수 표본 ID가 중복됩니다")
    incomplete_review_rows = [
        row["id"]
        for row in review_rows
        if row["user_actionability"] not in {
            "ACTION_REQUIRED",
            "ATTENTION_WORTHY",
            "INFORMATIONAL",
            "PROMOTIONAL",
        }
        or row["user_preference_sensitive"] not in {"true", "false"}
    ]
    if incomplete_review_rows:
        errors.append(f"사용자 검수가 완료되지 않은 행: {incomplete_review_rows}")

    human_reviewed_train_rows = [
        row for row in train_rows if row["base_label_status"] == "HUMAN_REVIEWED_V04"
    ]
    if len(human_reviewed_train_rows) != 20:
        errors.append(
            "학습 데이터의 사용자 검수 반영 행은 20개여야 합니다: "
            f"{len(human_reviewed_train_rows)}"
        )

    return errors


def main() -> None:
    errors = validate()
    if errors:
        print("v0.4 데이터 품질 검사 실패")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    _, train_rows = read_csv(TRAIN_PATH)
    _, context_rows = read_csv(CONTEXT_PATH)
    _, review_rows = read_csv(REVIEW_PATH)
    changed_rows = [
        row
        for row in train_rows
        if row["id"].startswith(("V02_", "V03_"))
        and row["previous_label"] != row["label"]
    ]

    print("v0.4 데이터 품질 검사")
    print(f"학습·대조 데이터: {len(train_rows)}")
    print(f"문맥 의존 데이터: {len(context_rows)}")
    print(f"검수 표본: {len(review_rows)}")
    print(f"Actionability: {dict(Counter(row['actionability'] for row in train_rows))}")
    print(f"Base Label: {dict(Counter(row['base_label'] for row in train_rows))}")
    print(f"v0.3 이관 데이터의 방향 변경: {len(changed_rows)}")
    print("결과: PASS")


if __name__ == "__main__":
    main()
