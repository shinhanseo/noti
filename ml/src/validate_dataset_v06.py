"""Validate the generated public v0.6 dataset and fixed group folds."""

from __future__ import annotations

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DIR = PROJECT_DIR / "data" / "public"
TRAIN = PUBLIC_DIR / "train_notifications_v0.6.csv"
CONTEXT = PUBLIC_DIR / "context_notifications_v0.6.csv"
EVALUATION = PUBLIC_DIR / "public_evaluation_v0.6.csv"
MANIFEST = PUBLIC_DIR / "source_manifest_v0.6.csv"
EXPECTED_TOTAL = Counter(
    ACTION_REQUIRED=250,
    ATTENTION_WORTHY=138,
    INFORMATIONAL=202,
    PROMOTIONAL=250,
)
EXPECTED_ELIGIBLE = Counter(
    ACTION_REQUIRED=210,
    ATTENTION_WORTHY=138,
    INFORMATIONAL=182,
    PROMOTIONAL=230,
)
EXPECTED_NEW = Counter(
    ACTION_REQUIRED=32,
    ATTENTION_WORTHY=48,
    INFORMATIONAL=48,
    PROMOTIONAL=32,
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def validate() -> list[str]:
    errors: list[str] = []
    for path in (TRAIN, CONTEXT, EVALUATION, MANIFEST):
        if not path.exists():
            errors.append(f"파일 없음: {path.name}")
    if errors:
        return errors

    train = rows(TRAIN)
    context = rows(CONTEXT)
    evaluation = rows(EVALUATION)
    manifest = rows(MANIFEST)
    if (len(train), len(context), len(manifest)) != (840, 80, 11):
        errors.append(
            f"행 수 오류: train={len(train)}, context={len(context)}, manifest={len(manifest)}"
        )
    all_rows = train + context + evaluation
    if any(row["dataset_version"] != "0.6" for row in all_rows):
        errors.append("dataset_version은 모두 0.6이어야 함")
    ids = [row["id"] for row in all_rows]
    if len(ids) != len(set(ids)):
        errors.append("중복 ID 존재")
    if Counter(row["actionability"] for row in train) != EXPECTED_TOTAL:
        errors.append("전체 Actionability 분포 오류")

    eligible = [
        row for row in train
        if row["model_eligible"] == "true"
        and row["training_eligible"] == "true"
        and row["clarity"] == "CLEAR"
    ]
    if Counter(row["actionability"] for row in eligible) != EXPECTED_ELIGIBLE:
        errors.append("학습 Actionability 분포 오류")
    new = [
        row for row in train
        if row["source"] == "SYNTHETIC_REAL_PATTERN_REVIEWED"
    ]
    if len(new) != 160 or Counter(row["actionability"] for row in new) != EXPECTED_NEW:
        errors.append("v0.6 신규 문장 분포 오류")
    revised = [
        row for row in train
        if row["reason_code"] == "v06_passive_delivery_progress"
    ]
    if len(revised) != 52 or any(row["actionability"] != "INFORMATIONAL" for row in revised):
        errors.append("배송 진행 라벨 교정 오류")

    groups: dict[str, set[str]] = defaultdict(set)
    for row in eligible:
        if row["cv_fold"] not in {"0", "1", "2", "3", "4"}:
            errors.append(f"{row['id']}: cv_fold 오류")
        groups[row["template_group"]].add(row["cv_fold"])
    if any(len(folds) != 1 for folds in groups.values()):
        errors.append("template_group fold 누수")
    fold_sizes = Counter(row["cv_fold"] for row in eligible)
    if any(not 145 <= fold_sizes[str(fold)] <= 160 for fold in range(5)):
        errors.append(f"fold 크기 불균형: {dict(fold_sizes)}")
    if any(row["training_eligible"] != "false" or row["cv_fold"] for row in context):
        errors.append("개인화 context 학습 차단 오류")
    return errors


def main() -> None:
    errors = validate()
    if errors:
        print("v0.6 데이터 품질 검사 실패")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    train = rows(TRAIN)
    eligible = [row for row in train if row["cv_fold"]]
    print("v0.6 데이터 품질 검사: PASS")
    print(f"전체 {len(train)}개, 학습 대상 {len(eligible)}개")
    print(dict(Counter(row["actionability"] for row in eligible)))


if __name__ == "__main__":
    main()
