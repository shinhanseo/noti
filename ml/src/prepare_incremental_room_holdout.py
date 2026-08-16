"""Prepare a private, temporally new Room holdout for human review.

The script compares two Room snapshots by notification key, masks private text,
deduplicates normalized notification content, and writes an unlabeled review
sheet. It never updates either Room database.
"""

from __future__ import annotations

import argparse
import hashlib
import sqlite3
from pathlib import Path

import pandas as pd

from notification_text_preprocessor import normalize_notification_text
from prepare_room_notifications_v03 import mask_private_text


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE_DB = (
    PROJECT_DIR / "data" / "private" / "room_export_2026-08-12_raw" / "noti.db"
)
DEFAULT_CURRENT_DB = (
    PROJECT_DIR / "data" / "private" / "room_export_2026-08-16_raw" / "noti.db"
)
DEFAULT_OUTPUT = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-16_raw"
    / "incremental_holdout_review.csv"
)
DEFAULT_REPORT = PROJECT_DIR / "reports" / "incremental_room_holdout_2026-08-16.md"
LABEL_COLUMNS = [
    "user_common_actionability",
    "user_personal_preference",
    "review_note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-db", type=Path, default=DEFAULT_BASELINE_DB)
    parser.add_argument("--current-db", type=Path, default=DEFAULT_CURRENT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def load_notifications(database: Path) -> pd.DataFrame:
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        return pd.read_sql_query(
            """
            SELECT notification_key, package_name, title, body, posted_at,
                   category, is_ongoing, importance_score, importance_level,
                   importance_forced
            FROM notifications
            ORDER BY posted_at ASC
            """,
            connection,
        ).fillna("")


def private_id(notification_key: str) -> str:
    return hashlib.sha256(notification_key.encode("utf-8")).hexdigest()[:12]


def preserve_labels(selected: pd.DataFrame, output: Path) -> pd.DataFrame:
    if not output.exists():
        return selected
    existing = pd.read_csv(output, dtype=str).fillna("")
    required = {"private_id", *LABEL_COLUMNS}
    if not required.issubset(existing.columns):
        return selected
    labels = existing[["private_id", *LABEL_COLUMNS]].drop_duplicates(
        "private_id", keep="last"
    )
    selected = selected.drop(columns=LABEL_COLUMNS).merge(
        labels, on="private_id", how="left", validate="one_to_one"
    )
    selected[LABEL_COLUMNS] = selected[LABEL_COLUMNS].fillna("")
    return selected


def main() -> None:
    args = parse_args()
    baseline = load_notifications(args.baseline_db)
    current = load_notifications(args.current_db)
    baseline_keys = set(baseline["notification_key"].astype(str))
    added = current[~current["notification_key"].astype(str).isin(baseline_keys)].copy()

    added["private_id"] = added["notification_key"].astype(str).map(private_id)
    added["title"] = added["title"].astype(str).map(mask_private_text)
    added["body"] = added["body"].astype(str).map(mask_private_text)
    added["normalized_text"] = [
        normalize_notification_text(package, title, body)
        for package, title, body in zip(
            added["package_name"], added["title"], added["body"]
        )
    ]
    added["dedupe_key"] = (
        added["package_name"].astype(str) + "\0" + added["normalized_text"]
    )
    duplicate_counts = added["dedupe_key"].value_counts()
    selected = added.drop_duplicates("dedupe_key", keep="first").copy()
    selected["duplicate_count"] = selected["dedupe_key"].map(duplicate_counts).astype(int)
    selected = selected.sort_values(["posted_at", "private_id"]).reset_index(drop=True)
    selected.insert(
        0, "review_id", [f"IH_{index:03d}" for index in range(1, len(selected) + 1)]
    )
    for column in LABEL_COLUMNS:
        selected[column] = ""
    selected = preserve_labels(selected, args.output)

    columns = [
        "review_id",
        "private_id",
        "package_name",
        "title",
        "body",
        "posted_at",
        "category",
        "duplicate_count",
        *LABEL_COLUMNS,
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    selected[columns].to_csv(args.output, index=False, encoding="utf-8-sig")

    fingerprint = hashlib.sha256(
        "\n".join(selected["private_id"]).encode("utf-8")
    ).hexdigest()
    package_counts = selected["package_name"].value_counts()
    report = "\n".join(
        [
            "# 증분 Room 독립 홀드아웃 봉인",
            "",
            f"- 기준 스냅샷 알림: {len(baseline)}개",
            f"- 현재 스냅샷 알림: {len(current)}개",
            f"- 새 notification key: {len(added)}개",
            f"- 전처리 문장 중복 제거 후: {len(selected)}개",
            f"- 포함 패키지: {selected['package_name'].nunique()}개",
            f"- 동일 패키지 최대 빈도: {int(package_counts.max()) if len(package_counts) else 0}개",
            f"- 표본 fingerprint: `{fingerprint}`",
            "",
            "이 세트는 이전 Room 스냅샷 이후에 도착한 알림만 포함한다.",
            "제목과 본문은 private 검수 파일을 만들기 전에 마스킹했다.",
            "모델 예측과 Kotlin 점수는 선정에 사용하지 않았다.",
            "라벨 입력 전 모델 예측을 별도 파일에 봉인한다.",
            "평가가 끝나기 전에는 학습 데이터에 포함하지 않는다.",
            "",
        ]
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
