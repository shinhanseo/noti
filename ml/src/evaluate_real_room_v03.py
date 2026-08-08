import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score

from compare_lightweight_models import make_candidates
from compare_pretrained_embeddings import (
    CANDIDATES as EMBEDDING_CANDIDATES,
    create_embeddings,
    dataset_fingerprint,
    make_heads,
)
from prepare_room_notifications_v03 import mask_private_text
from train_baseline import load_training_data, make_text


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-06_approved"
    / "noti.db"
)
DEFAULT_PRIVATE_RESULT = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-06_approved"
    / "room_review_shadow_predictions_v0.3.csv"
)
DEFAULT_HUMAN_LABELS = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-06_approved"
    / "room_review_human_labels_v0.3.csv"
)
REPORT_PATH = PROJECT_DIR / "reports" / "v0.3_real_room_shadow_evaluation.md"
RESULT_PATH = PROJECT_DIR / "reports" / "v0.3_real_room_shadow_evaluation.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="실제 Room REVIEW 알림의 비라벨 그림자 평가"
    )
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--private-output", type=Path, default=DEFAULT_PRIVATE_RESULT)
    parser.add_argument(
        "--labels",
        type=Path,
        default=DEFAULT_HUMAN_LABELS,
        help="private_id와 human_label(0 또는 1)이 있는 사용자 검토 CSV",
    )
    parser.add_argument(
        "--include-e5",
        action="store_true",
        help="로컬 multilingual-e5-small과 두 분류 Head를 함께 평가",
    )
    return parser.parse_args()


def load_room_candidates(database: Path) -> pd.DataFrame:
    uri = f"file:{database}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        data = pd.read_sql_query(
            """
            SELECT
                notification_key,
                package_name,
                title,
                body,
                posted_at,
                category,
                is_ongoing,
                importance_score,
                importance_level,
                importance_forced,
                importance_policy_version
            FROM notifications
            WHERE importance_forced = 0
              AND importance_score BETWEEN 25 AND 39
            ORDER BY posted_at
            """,
            connection,
        )

    data["title"] = data["title"].fillna("").map(mask_private_text)
    data["body"] = data["body"].fillna("").map(mask_private_text)
    data["text"] = make_text(data)
    data["private_id"] = data["notification_key"].map(
        lambda value: hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
    )
    data["normalized_text"] = (
        data["text"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
    )
    return data


def add_lightweight_predictions(
    training_data: pd.DataFrame,
    room_data: pd.DataFrame,
) -> list[str]:
    model_names: list[str] = []
    for name, factory in make_candidates().items():
        pipeline = factory()
        pipeline.fit(training_data["text"], training_data["label"])
        probability = pipeline.predict_proba(room_data["text"])[:, 1]
        room_data[f"probability__{name}"] = probability
        room_data[f"prediction__{name}"] = (probability >= 0.5).astype(int)
        model_names.append(name)
    return model_names


def add_e5_predictions(
    training_data: pd.DataFrame,
    room_data: pd.DataFrame,
) -> list[str]:
    from sentence_transformers import SentenceTransformer

    candidate = EMBEDDING_CANDIDATES["multilingual_e5_small"]
    training_texts = training_data["text"].tolist()
    fingerprint = dataset_fingerprint(training_texts)
    training_embeddings, _ = create_embeddings(
        candidate,
        training_texts,
        fingerprint,
        force=False,
        local_files_only=True,
    )

    encoder = SentenceTransformer(
        candidate.model_id,
        device="cpu",
        local_files_only=True,
    )
    encoder.max_seq_length = candidate.max_sequence_length
    room_embeddings = encoder.encode(
        [candidate.text_prefix + text for text in room_data["text"]],
        batch_size=16,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)

    labels = training_data["label"].to_numpy(dtype=int)
    model_names: list[str] = []
    for head_name, head in make_heads(42).items():
        head.fit(training_embeddings, labels)
        probability = head.predict_proba(room_embeddings)[:, 1]
        name = f"e5_small_{head_name}"
        room_data[f"probability__{name}"] = probability
        room_data[f"prediction__{name}"] = (probability >= 0.5).astype(int)
        model_names.append(name)
    return model_names


def summarize_model(room_data: pd.DataFrame, name: str) -> dict[str, object]:
    probabilities = room_data[f"probability__{name}"]
    predictions = room_data[f"prediction__{name}"]
    summary: dict[str, object] = {
        "name": name,
        "important_predictions": int(predictions.sum()),
        "general_predictions": int((predictions == 0).sum()),
        "important_share": float(predictions.mean()),
        "mean_probability": float(probabilities.mean()),
        "minimum_probability": float(probabilities.min()),
        "maximum_probability": float(probabilities.max()),
        "ambiguous_40_60": int(probabilities.between(0.4, 0.6).sum()),
    }
    labeled = room_data[room_data["human_label"].notna()]
    if not labeled.empty:
        labels = labeled["human_label"].astype(int)
        labeled_predictions = labeled[f"prediction__{name}"].astype(int)
        matrix = confusion_matrix(labels, labeled_predictions, labels=[0, 1])
        summary.update(
            {
                "accuracy": float(accuracy_score(labels, labeled_predictions)),
                "precision": float(
                    precision_score(labels, labeled_predictions, zero_division=0)
                ),
                "recall": float(
                    recall_score(labels, labeled_predictions, zero_division=0)
                ),
                "false_positive": int(matrix[0, 1]),
                "false_negative": int(matrix[1, 0]),
            }
        )
    return summary


def create_report(result: dict[str, object]) -> str:
    lines = [
        "# v0.3 실제 Room 알림 그림자 평가",
        "",
        "## 목적",
        "",
        "실제 기기에서 수집한 알림 중 사용자 강제 판정이 없고 규칙 점수가 "
        "25~39인 REVIEW 알림에 여러 모델을 그림자 실행한다.",
        "사용자가 직접 확인한 중요/일반 라벨이 있으면 실제 예측과 비교한다.",
        "",
        "## 데이터",
        "",
        f"- 전체 Room 알림: {result['room_total_rows']}개",
        f"- 실제 AI 실행 후보: {result['review_rows']}개",
        f"- 중복 제거 전 고유 문장: {result['unique_texts']}개",
        f"- 후보 발신 패키지: {result['review_packages']}개",
        f"- 사용자 피드백 라벨: {result['feedback_rows']}개",
        f"- 이번 사용자 검토 라벨: {result['human_labeled_rows']}개 "
        f"(중요 {result['human_important_rows']}, 일반 {result['human_general_rows']})",
        "",
        "## 모델별 그림자 판정",
        "",
        "| 모델 | 중요 예측 | 일반 예측 | 중요 비율 | 평균 확률 | 0.4~0.6 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in result["models"]:
        lines.append(
            f"| `{row['name']}` | {row['important_predictions']} | "
            f"{row['general_predictions']} | {row['important_share']:.1%} | "
            f"{row['mean_probability']:.3f} | {row['ambiguous_40_60']} |"
        )

    if result["human_labeled_rows"]:
        lines.extend(
            [
                "",
                "## 사용자 정답 기준 평가",
                "",
                "| 모델 | 정확도 | Precision | Recall | FP | FN |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for row in result["models"]:
            lines.append(
                f"| `{row['name']}` | {row['accuracy']:.1%} | "
                f"{row['precision']:.3f} | {row['recall']:.3f} | "
                f"{row['false_positive']} | {row['false_negative']} |"
            )

    lines.extend(
        [
            "",
            "## 모델 합의",
            "",
            f"- 전 모델 중요 합의: {result['unanimous_important']}개",
            f"- 전 모델 일반 합의: {result['unanimous_general']}개",
            f"- 모델 판단 불일치: {result['mixed_predictions']}개",
            f"- 평균 모델 간 확률 범위: {result['mean_probability_spread']:.3f}",
            "",
            "## 해석 제한",
            "",
            "- 사용자 정답은 확보했지만 중요 라벨이 1개뿐이므로 수치는 매우 불안정하다.",
            "- 12개 후보는 통계적으로 매우 작은 외부 데이터다.",
            "- 원문과 개별 예측은 Git 제외 private CSV에만 저장했다.",
            "- 다음 단계는 중복을 정리한 고유 문장을 사람이 라벨링하는 것이다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    all_training_data, training_data = load_training_data("0.3")
    room_data = load_room_candidates(args.database)
    if room_data.empty:
        raise RuntimeError("실제 Room DB에 REVIEW 대상이 없습니다.")

    room_data["human_label"] = pd.NA
    if args.labels.exists():
        labels = pd.read_csv(args.labels, dtype={"private_id": str})
        if set(labels.columns) != {"private_id", "human_label"}:
            raise ValueError("라벨 CSV는 private_id,human_label 두 컬럼이어야 합니다.")
        if not labels["human_label"].isin([0, 1]).all():
            raise ValueError("human_label은 0 또는 1이어야 합니다.")
        label_map = labels.set_index("private_id")["human_label"]
        room_data["human_label"] = room_data["private_id"].map(label_map)

    model_names = add_lightweight_predictions(training_data, room_data)
    if args.include_e5:
        model_names.extend(add_e5_predictions(training_data, room_data))

    prediction_columns = [f"prediction__{name}" for name in model_names]
    probability_columns = [f"probability__{name}" for name in model_names]
    room_data["important_votes"] = room_data[prediction_columns].sum(axis=1)
    room_data["model_count"] = len(model_names)
    room_data["mean_probability"] = room_data[probability_columns].mean(axis=1)
    room_data["probability_spread"] = (
        room_data[probability_columns].max(axis=1)
        - room_data[probability_columns].min(axis=1)
    )

    with sqlite3.connect(f"file:{args.database}?mode=ro", uri=True) as connection:
        room_total_rows = connection.execute(
            "SELECT COUNT(*) FROM notifications"
        ).fetchone()[0]
        feedback_rows = connection.execute(
            "SELECT COUNT(*) FROM notification_feedback"
        ).fetchone()[0]

    result: dict[str, object] = {
        "dataset_version": "0.3",
        "training_rows": len(training_data),
        "training_total_rows": len(all_training_data),
        "room_total_rows": room_total_rows,
        "review_rows": len(room_data),
        "unique_texts": int(room_data["normalized_text"].nunique()),
        "review_packages": int(room_data["package_name"].nunique()),
        "feedback_rows": feedback_rows,
        "human_labeled_rows": int(room_data["human_label"].notna().sum()),
        "human_important_rows": int(room_data["human_label"].fillna(0).sum()),
        "human_general_rows": int((room_data["human_label"] == 0).sum()),
        "models": [summarize_model(room_data, name) for name in model_names],
        "unanimous_important": int(
            (room_data["important_votes"] == len(model_names)).sum()
        ),
        "unanimous_general": int((room_data["important_votes"] == 0).sum()),
        "mixed_predictions": int(
            room_data["important_votes"].between(1, len(model_names) - 1).sum()
        ),
        "mean_probability_spread": float(room_data["probability_spread"].mean()),
    }

    private_columns = [
        "private_id",
        "package_name",
        "title",
        "body",
        "posted_at",
        "category",
        "is_ongoing",
        "importance_score",
        "importance_level",
        "human_label",
        *prediction_columns,
        *probability_columns,
        "important_votes",
        "model_count",
        "mean_probability",
        "probability_spread",
    ]
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    room_data[private_columns].to_csv(
        args.private_output,
        index=False,
        encoding="utf-8-sig",
        lineterminator="\n",
    )
    REPORT_PATH.write_text(create_report(result), encoding="utf-8")
    RESULT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("실제 Room REVIEW 그림자 평가 완료")
    print(f"전체 알림: {room_total_rows}")
    print(f"REVIEW 후보: {len(room_data)}")
    print(f"고유 문장: {result['unique_texts']}")
    print(f"모델 불일치: {result['mixed_predictions']}")
    print(f"집계 보고서: {REPORT_PATH}")
    print(f"개별 결과: {args.private_output}")


if __name__ == "__main__":
    main()
