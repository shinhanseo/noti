import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_DIR / "data" / "public"
TRAIN_PATH = PUBLIC_DATA_DIR / "train_notifications_v0.5.csv"
CONTEXT_PATH = PUBLIC_DATA_DIR / "context_notifications_v0.5.csv"
EVALUATION_PATH = PUBLIC_DATA_DIR / "public_evaluation_v0.5.csv"
MANIFEST_PATH = PUBLIC_DATA_DIR / "source_manifest_v0.5.csv"

EXPECTED_TOTAL_ACTIONABILITY = Counter(
    {
        "ACTION_REQUIRED": 218,
        "ATTENTION_WORTHY": 142,
        "INFORMATIONAL": 102,
        "PROMOTIONAL": 218,
    }
)
EXPECTED_ELIGIBLE_ACTIONABILITY = Counter(
    {
        "ACTION_REQUIRED": 178,
        "ATTENTION_WORTHY": 142,
        "INFORMATIONAL": 82,
        "PROMOTIONAL": 198,
    }
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return reader.fieldnames or [], list(reader)


def validate() -> list[str]:
    errors: list[str] = []
    for path in (TRAIN_PATH, CONTEXT_PATH, EVALUATION_PATH, MANIFEST_PATH):
        if not path.exists():
            errors.append(f"파일이 없습니다: {path.name}")
    if errors:
        return errors

    fields, train_rows = read_csv(TRAIN_PATH)
    _, context_rows = read_csv(CONTEXT_PATH)
    _, evaluation_rows = read_csv(EVALUATION_PATH)
    _, manifest_rows = read_csv(MANIFEST_PATH)
    if "cv_fold" not in fields:
        errors.append("train 데이터에 cv_fold가 없습니다")
    if len(train_rows) != 680:
        errors.append(f"학습·대조 데이터는 680개여야 합니다: {len(train_rows)}")
    if len(context_rows) != 80:
        errors.append(f"문맥 데이터는 80개여야 합니다: {len(context_rows)}")
    if len(manifest_rows) != 10:
        errors.append(f"source manifest는 10개여야 합니다: {len(manifest_rows)}")

    ids = [row["id"] for row in train_rows + context_rows + evaluation_rows]
    duplicate_ids = [value for value, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"중복 ID: {duplicate_ids[:5]}")

    for row in train_rows + context_rows + evaluation_rows:
        if row["dataset_version"] != "0.5":
            errors.append(f"{row['id']}: dataset_version 오류")

    actionability_counts = Counter(row["actionability"] for row in train_rows)
    if actionability_counts != EXPECTED_TOTAL_ACTIONABILITY:
        errors.append(f"전체 actionability 분포 오류: {dict(actionability_counts)}")

    diversity_rows = [
        row for row in train_rows if row["source"] == "SYNTHETIC_DIVERSITY_REVIEWED"
    ]
    if len(diversity_rows) != 160:
        errors.append(f"v0.5 신규 데이터는 160개여야 합니다: {len(diversity_rows)}")
    diversity_counts = Counter(row["actionability"] for row in diversity_rows)
    expected_diversity = Counter(
        {
            "ACTION_REQUIRED": 32,
            "ATTENTION_WORTHY": 48,
            "INFORMATIONAL": 32,
            "PROMOTIONAL": 48,
        }
    )
    if diversity_counts != expected_diversity:
        errors.append(f"v0.5 신규 actionability 분포 오류: {dict(diversity_counts)}")

    eligible = [
        row
        for row in train_rows
        if row["model_eligible"].lower() == "true"
        and row["training_eligible"].lower() == "true"
        and row["clarity"] == "CLEAR"
    ]
    if len(eligible) != 600:
        errors.append(f"모델 학습 대상은 600개여야 합니다: {len(eligible)}")
    eligible_counts = Counter(row["actionability"] for row in eligible)
    if eligible_counts != EXPECTED_ELIGIBLE_ACTIONABILITY:
        errors.append(f"학습 대상 actionability 분포 오류: {dict(eligible_counts)}")

    groups_to_folds: dict[str, set[str]] = defaultdict(set)
    for row in eligible:
        if row["cv_fold"] not in {"0", "1", "2", "3", "4"}:
            errors.append(f"{row['id']}: cv_fold 오류")
        groups_to_folds[row["template_group"]].add(row["cv_fold"])
    leaking_groups = [group for group, folds in groups_to_folds.items() if len(folds) > 1]
    if leaking_groups:
        errors.append(f"여러 fold에 걸친 template_group: {leaking_groups[:5]}")

    target_counts = {
        key: value / 5
        for key, value in EXPECTED_ELIGIBLE_ACTIONABILITY.items()
    }
    for fold in range(5):
        fold_rows = [row for row in eligible if row["cv_fold"] == str(fold)]
        if not 105 <= len(fold_rows) <= 135:
            errors.append(f"Fold {fold} 크기 불균형: {len(fold_rows)}")
        counts = Counter(row["actionability"] for row in fold_rows)
        for actionability, target in target_counts.items():
            tolerance = max(6, target * 0.35)
            if abs(counts[actionability] - target) > tolerance:
                errors.append(
                    f"Fold {fold} {actionability} 불균형: "
                    f"{counts[actionability]} (목표 {target:.1f})"
                )

    for row in context_rows:
        if row["training_eligible"].lower() != "false" or row["cv_fold"]:
            errors.append(f"{row['id']}: 문맥 데이터 학습 차단 오류")

    return errors


def main() -> None:
    errors = validate()
    if errors:
        print("v0.5 데이터 품질 검사 실패")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)

    _, train_rows = read_csv(TRAIN_PATH)
    eligible = [row for row in train_rows if row["cv_fold"]]
    print("v0.5 데이터 품질 검사")
    print(f"학습·대조 데이터: {len(train_rows)}")
    print(f"모델 학습 대상: {len(eligible)}")
    print(f"Actionability: {dict(Counter(row['actionability'] for row in eligible))}")
    for fold in range(5):
        fold_rows = [row for row in eligible if row["cv_fold"] == str(fold)]
        print(
            f"Fold {fold}: {len(fold_rows)} "
            f"{dict(Counter(row['actionability'] for row in fold_rows))}"
        )
    print("결과: PASS")


if __name__ == "__main__":
    main()
