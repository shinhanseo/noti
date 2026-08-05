import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_DIR / "data" / "public"
TRAIN_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.3.csv"
CONTEXT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.3.csv"
EVALUATION_PATH = PUBLIC_DATA_DIR / "public_evaluation_v0.3.csv"

REQUIRED_COLUMNS = {
    "id", "app_name", "package_name", "title", "body", "label",
    "notification_type", "template_group", "clarity", "reason_code",
    "android_category", "is_ongoing", "rule_score", "rule_level",
    "forced", "model_eligible", "source", "dataset_version",
    "source_detail", "source_url", "license", "is_real", "is_public",
    "label_status", "original_source_id",
}

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
    for path in (TRAIN_PATH, CONTEXT_PATH, EVALUATION_PATH):
        if not path.exists():
            errors.append(f"파일이 없습니다: {path.name}")
    if errors:
        return errors

    train_columns, train_rows = read_csv(TRAIN_PATH)
    context_columns, context_rows = read_csv(CONTEXT_PATH)
    evaluation_columns, evaluation_rows = read_csv(EVALUATION_PATH)

    for path, columns in (
        (TRAIN_PATH, train_columns),
        (CONTEXT_PATH, context_columns),
        (EVALUATION_PATH, evaluation_columns),
    ):
        missing = REQUIRED_COLUMNS - set(columns)
        if missing:
            errors.append(f"{path.name}: 필수 컬럼 누락 {sorted(missing)}")

    all_rows = train_rows + context_rows + evaluation_rows
    ids = [row["id"] for row in all_rows]
    duplicates = [value for value, count in Counter(ids).items() if count > 1]
    if duplicates:
        errors.append(f"중복 ID: {duplicates[:5]}")

    exact_texts: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in all_rows:
        row_id = row["id"]
        text = f'{row["title"]} {row["body"]}'.strip()
        if not text:
            errors.append(f"{row_id}: 제목과 본문이 모두 비어 있습니다")
            continue
        exact_texts[normalize_text(text)].append(row)

        if row["dataset_version"] != "0.3":
            errors.append(f"{row_id}: dataset_version이 0.3이 아닙니다")
        if row["is_real"] not in {"true", "false"}:
            errors.append(f"{row_id}: is_real boolean 오류")
        if row["is_public"] not in {"true", "false"}:
            errors.append(f"{row_id}: is_public boolean 오류")

        for name, pattern in PII_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{row_id}: 마스킹되지 않은 {name} 의심 값")

    unsafe_duplicates = []
    for rows in exact_texts.values():
        if len(rows) < 2:
            continue
        labels = {row["label"] for row in rows}
        groups = {row["template_group"] for row in rows}
        if len(labels) > 1 or len(groups) > 1 or "" in groups:
            unsafe_duplicates.append([row["id"] for row in rows])
    if unsafe_duplicates:
        errors.append(
            "라벨 또는 template_group이 다른 정규화 문장 중복: "
            f"{unsafe_duplicates[:3]}"
        )

    for row in train_rows:
        if row["label"] not in {"0", "1"}:
            errors.append(f"{row['id']}: 학습 label은 0 또는 1이어야 합니다")
        if row["label_status"] not in {"POLICY_REVIEWED", "HUMAN_REVIEWED"}:
            errors.append(f"{row['id']}: 검토되지 않은 라벨이 학습 파일에 있습니다")
        if row["clarity"] != "CLEAR":
            errors.append(f"{row['id']}: 학습 clarity는 CLEAR여야 합니다")

    for row in context_rows:
        if row["label"]:
            errors.append(f"{row['id']}: 문맥 데이터 label은 비워야 합니다")
        if row["label_status"] != "UNLABELED_CONTEXT":
            errors.append(f"{row['id']}: 문맥 데이터 label_status 오류")

    for row in evaluation_rows:
        if row["label"] or row["model_eligible"] == "true":
            errors.append(f"{row['id']}: 공개 원문은 검토 전 학습에 사용할 수 없습니다")
        if row["label_status"] != "UNLABELED":
            errors.append(f"{row['id']}: 공개 원문 label_status는 UNLABELED여야 합니다")

    label_counts = Counter(row["label"] for row in train_rows)
    if label_counts["0"] != label_counts["1"]:
        errors.append(f"학습 라벨 불균형: {dict(label_counts)}")

    realistic = [row for row in train_rows if row["source"] == "SYNTHETIC_REALISTIC_REVIEWED"]
    if len(realistic) != 160:
        errors.append(f"현실형 신규 데이터는 160개여야 합니다: {len(realistic)}")
    realistic_labels = Counter(row["label"] for row in realistic)
    if realistic_labels != Counter({"0": 80, "1": 80}):
        errors.append(f"현실형 신규 라벨 불균형: {dict(realistic_labels)}")

    per_app: dict[str, Counter[str]] = defaultdict(Counter)
    for row in realistic:
        per_app[row["app_name"]][row["label"]] += 1
    for app_name, counts in per_app.items():
        if counts != Counter({"0": 4, "1": 4}):
            errors.append(f"{app_name}: 현실형 라벨 구성이 4:4가 아닙니다 ({dict(counts)})")

    return errors


def main() -> None:
    errors = validate()
    if errors:
        print("v0.3 데이터 품질 검사 실패")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    _, train_rows = read_csv(TRAIN_PATH)
    _, context_rows = read_csv(CONTEXT_PATH)
    realistic = [row for row in train_rows if row["source"] == "SYNTHETIC_REALISTIC_REVIEWED"]
    print("v0.3 데이터 품질 검사")
    print(f"학습·대조 데이터: {len(train_rows)}")
    print(f"현실형 신규 데이터: {len(realistic)}")
    print(f"문맥 의존 데이터: {len(context_rows)}")
    print(f"전체 Label: {dict(Counter(row['label'] for row in train_rows))}")
    print(f"현실형 앱: {len(set(row['app_name'] for row in realistic))}")
    print("결과: PASS")


if __name__ == "__main__":
    main()
