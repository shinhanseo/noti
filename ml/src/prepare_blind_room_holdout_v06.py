"""Seal a model-independent blind Room holdout before human labeling."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

from prepare_active_learning_review import DEFAULT_DATABASE, DEFAULT_REPLAY, load_room


PROJECT_DIR = Path(__file__).resolve().parents[1]
PRIVATE_DIR = PROJECT_DIR / "data" / "private" / "room_export_2026-08-12_raw"
ACTIVE_PATH = PRIVATE_DIR / "active_learning_review_40.csv"
OUTPUT_PATH = PRIVATE_DIR / "blind_holdout_review_100.csv"
REPORT_PATH = PROJECT_DIR / "reports" / "blind_holdout_v06_seal.md"
SELECTION_SALT = "noti-blind-room-holdout-v1"
LABEL_COLUMNS = [
    "user_common_actionability",
    "user_personal_preference",
    "review_note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--replay", type=Path, default=DEFAULT_REPLAY)
    parser.add_argument("--active", type=Path, default=ACTIVE_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--count", type=int, default=100)
    return parser.parse_args()


def selection_hash(private_id: str) -> str:
    return hashlib.sha256(
        f"{SELECTION_SALT}\0{private_id}".encode("utf-8")
    ).hexdigest()


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
    room = load_room(args.database, args.replay)
    active = pd.read_csv(args.active).fillna("")
    active_ids = set(active["private_id"].astype(str))
    room["dedupe_key"] = room["package_name"].astype(str) + "\0" + room["text"]
    room_ids = set(room["private_id"].astype(str))
    missing_active_ids = active_ids - room_ids
    if missing_active_ids:
        raise ValueError(
            f"Room DB에서 기존 검수 ID {len(missing_active_ids)}개를 찾지 못했습니다."
        )
    active_keys = set(
        room.loc[room["private_id"].isin(active_ids), "dedupe_key"]
    )
    excluded = room["private_id"].isin(active_ids) | room["dedupe_key"].isin(active_keys)
    candidates = room[~excluded].copy()
    candidates["selection_hash"] = candidates["private_id"].map(selection_hash)
    selected = candidates.sort_values("selection_hash").head(args.count).copy()
    if len(selected) != args.count:
        raise ValueError(f"검수 후보가 {args.count}개보다 적습니다: {len(selected)}")

    selected = selected.sort_values("selection_hash").reset_index(drop=True)
    selected.insert(
        0, "review_id", [f"BH_{index:03d}" for index in range(1, len(selected) + 1)]
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
        *LABEL_COLUMNS,
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    selected[columns].to_csv(args.output, index=False, encoding="utf-8-sig")

    fingerprint = hashlib.sha256(
        "\n".join(selected["private_id"]).encode("utf-8")
    ).hexdigest()
    excluded_rows = int(excluded.sum())
    if excluded_rows < len(active_ids):
        raise RuntimeError("기존 Active Learning 행이 모두 제외되지 않았습니다.")
    report = "\n".join(
        [
            "# v0.6 블라인드 Room 홀드아웃 봉인",
            "",
            f"- 전체 비강제 Room 알림: {len(room)}개",
            f"- 기존 Active Learning 문장군 제외: {excluded_rows}개",
            f"- 모델 독립 후보 풀: {len(candidates)}개",
            f"- 블라인드 평가 표본: {len(selected)}개",
            f"- 포함 패키지: {selected['package_name'].nunique()}개",
            f"- 동일 패키지 최대 빈도: {selected['package_name'].value_counts().max()}개",
            f"- 동일 패키지+제목+본문 반복 행: {selected.duplicated(['package_name', 'title', 'body']).sum()}개",
            f"- 선택 방식: `{SELECTION_SALT}` + private ID SHA-256 정렬",
            f"- 표본 fingerprint: `{fingerprint}`",
            "",
            "선정 과정에는 Kotlin 점수와 어떤 모델 예측값도 사용하지 않았다.",
            "기존 40개와 전처리 문장이 같은 알림은 모두 제외했다.",
            "실사용 빈도를 반영하는 원본 100개를 주 평가로 삼고, 반복 제거 결과도 보조로 계산한다.",
            "모델 예측은 별도 private 파일에 라벨 입력 전에 봉인한다.",
            "",
        ]
    )
    args.report.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
