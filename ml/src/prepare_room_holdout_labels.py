"""Create a private, anonymized labeling sheet for newly collected Room REVIEW rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path

from prepare_room_notifications_v03 import mask_private_text


PROJECT_DIR = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--previous-database", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def max_posted_at(database: Path) -> int:
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        value = connection.execute(
            "SELECT MAX(posted_at) FROM notifications"
        ).fetchone()[0]
    if value is None:
        raise RuntimeError("이전 DB에 알림이 없습니다.")
    return int(value)


def load_review_rows(database: Path, cutoff: int) -> list[sqlite3.Row]:
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        return connection.execute(
            """
            SELECT
                notification_key,
                package_name,
                title,
                body,
                posted_at,
                category,
                importance_score,
                importance_level
            FROM notifications
            WHERE posted_at > ?
              AND importance_forced = 0
              AND importance_score BETWEEN 25 AND 39
            ORDER BY posted_at
            """,
            (cutoff,),
        ).fetchall()


def main() -> None:
    args = parse_args()
    cutoff = max_posted_at(args.previous_database)
    rows = load_review_rows(args.database, cutoff)
    fields = [
        "private_id",
        "package_name",
        "title",
        "body",
        "posted_at",
        "android_category",
        "rule_score",
        "rule_level",
        "common_actionability",
        "personal_preference",
        "review_note",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "private_id": hashlib.sha256(
                        row["notification_key"].encode("utf-8")
                    ).hexdigest()[:12],
                    "package_name": row["package_name"],
                    "title": mask_private_text(row["title"] or ""),
                    "body": mask_private_text(row["body"] or ""),
                    "posted_at": datetime.fromtimestamp(
                        row["posted_at"] / 1000
                    ).astimezone().isoformat(timespec="seconds"),
                    "android_category": row["category"] or "",
                    "rule_score": row["importance_score"],
                    "rule_level": row["importance_level"],
                    "common_actionability": "",
                    "personal_preference": "",
                    "review_note": "",
                }
            )

    print(f"이전 DB cutoff: {cutoff}")
    print(f"새 REVIEW 라벨링 행: {len(rows)}")
    print(f"저장 위치: {args.output}")
    print("원본 notification_key는 SHA-256 기반 private_id로 대체했습니다.")


if __name__ == "__main__":
    main()
