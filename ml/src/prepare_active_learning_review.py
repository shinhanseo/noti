"""Select diverse, uncertain Room notifications for efficient human review."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from ai_edge_litert.interpreter import Interpreter
from sklearn.cluster import KMeans
from transformers import AutoTokenizer

import experiment_embeddinggemma_actionability_v05 as embedding_experiment
from actionability_contract import (
    important_probabilities,
    predicted_actionability,
    softmax,
)
from notification_text_preprocessor import normalize_notification_text
from prepare_room_notifications_v03 import mask_private_text


PROJECT_DIR = Path(__file__).resolve().parents[1]
PRIVATE_DIR = PROJECT_DIR / "data" / "private" / "room_export_2026-08-12_raw"
DEFAULT_DATABASE = PRIVATE_DIR / "noti.db"
DEFAULT_REPLAY = PRIVATE_DIR / "android_policy_replay_output.tsv"
DEFAULT_ALL_OUTPUT = PRIVATE_DIR / "active_learning_all_predictions.csv"
DEFAULT_REVIEW_OUTPUT = PRIVATE_DIR / "active_learning_review_40.csv"
DEFAULT_REPORT = PROJECT_DIR / "reports" / "active_learning_selection_2026-08-12.md"
KOELECTRA_DIR = PROJECT_DIR / "models" / "koelectra_actionability_triage_v0.5_final"
KOELECTRA_MODEL = (
    KOELECTRA_DIR
    / "noti_koelectra_actionability_v0.5_final_dynamic_range.tflite"
)
EMBEDDINGGEMMA_ID = "google/embeddinggemma-300m"
EMBEDDINGGEMMA_PREFIX = "task: classification | query: "
GRANITE_ID = "ibm-granite/granite-embedding-97m-multilingual-r2"
GRANITE_PREFIX = ""
LABEL_COLUMNS = [
    "user_common_actionability",
    "user_personal_preference",
    "review_note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--replay", type=Path, default=DEFAULT_REPLAY)
    parser.add_argument("--all-output", type=Path, default=DEFAULT_ALL_OUTPUT)
    parser.add_argument("--review-output", type=Path, default=DEFAULT_REVIEW_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--review-count", type=int, default=40)
    parser.add_argument("--local-files-only", action="store_true")
    return parser.parse_args()


def private_id(notification_key: str) -> str:
    return hashlib.sha256(notification_key.encode("utf-8")).hexdigest()[:12]


def load_room(database: Path, replay_path: Path) -> pd.DataFrame:
    uri = f"file:{database}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        data = pd.read_sql_query(
            """
            SELECT notification_key, package_name, title, body, posted_at,
                   category, is_ongoing, importance_score, importance_level,
                   importance_forced
            FROM notifications
            WHERE importance_forced = 0
            ORDER BY posted_at DESC
            """,
            connection,
        )
    data["private_id"] = data["notification_key"].map(private_id)
    data["title"] = data["title"].fillna("").map(mask_private_text)
    data["body"] = data["body"].fillna("").map(mask_private_text)
    data["text"] = [
        normalize_notification_text(package_name, title, body)
        for package_name, title, body in zip(
            data["package_name"], data["title"], data["body"]
        )
    ]
    replay = pd.read_csv(replay_path, sep="\t", dtype={"private_id": str})
    replay = replay[["private_id", "new_score", "new_level"]].rename(
        columns={"new_score": "rule_score_v2", "new_level": "rule_level_v2"}
    )
    data = data.merge(replay, on="private_id", how="left", validate="one_to_one")
    if data[["rule_score_v2", "rule_level_v2"]].isna().any().any():
        raise RuntimeError("Kotlin v2 replay 결과가 없는 알림이 있습니다.")
    return data


def deduplicate(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data["dedupe_key"] = data["package_name"].astype(str) + "\0" + data["text"]
    counts = data["dedupe_key"].value_counts()
    unique = data.drop_duplicates("dedupe_key", keep="first").copy()
    unique["duplicate_count"] = unique["dedupe_key"].map(counts).astype(int)
    return unique.reset_index(drop=True)


def add_koelectra_predictions(data: pd.DataFrame) -> None:
    tokenizer = AutoTokenizer.from_pretrained(
        KOELECTRA_DIR / "tokenizer", use_fast=True, local_files_only=True
    )
    interpreter = Interpreter(model_path=str(KOELECTRA_MODEL), num_threads=2)
    runner = interpreter.get_signature_runner("serving_default")
    probabilities = []
    for text in data["text"]:
        encoded = tokenizer(
            text,
            max_length=64,
            padding="max_length",
            truncation=True,
            return_tensors="np",
        )
        input_ids = encoded["input_ids"].astype(np.int32)
        inputs = {
            "input_ids": input_ids,
            "attention_mask": encoded["attention_mask"].astype(np.int32),
            "token_type_ids": encoded.get(
                "token_type_ids", np.zeros_like(input_ids)
            ).astype(np.int32),
        }
        probabilities.append(softmax(np.asarray(runner(**inputs)["logits"]))[0])
    values = np.asarray(probabilities)
    data["koelectra_actionability"] = predicted_actionability(values)
    data["koelectra_important_probability"] = important_probabilities(values)


def run_embedding_model(
    training: pd.DataFrame,
    room: pd.DataFrame,
    model_id: str,
    prefix: str,
    local_files_only: bool,
) -> tuple[np.ndarray, np.ndarray]:
    embedding_experiment.MODEL_ID = model_id
    embedding_experiment.CLASSIFICATION_PREFIX = prefix
    all_texts = training["text"].tolist() + room["text"].tolist()
    embeddings, _, model = embedding_experiment.create_embeddings(
        all_texts, force=False, local_files_only=local_files_only
    )
    training_embeddings = embeddings[: len(training)]
    room_embeddings = embeddings[len(training) :].copy()
    labels = training["actionability_id"].to_numpy(dtype=np.int32)
    head = embedding_experiment.make_head("mlp_32")
    embedding_experiment.fit_head(
        head, "mlp_32", training_embeddings, labels
    )
    probabilities = head.predict_proba(room_embeddings)
    del model, embeddings, training_embeddings, head
    gc.collect()
    return probabilities, room_embeddings


def add_prediction_columns(
    data: pd.DataFrame, prefix: str, probabilities: np.ndarray
) -> None:
    data[f"{prefix}_actionability"] = predicted_actionability(probabilities)
    data[f"{prefix}_important_probability"] = important_probabilities(
        probabilities
    )


def add_selection_features(data: pd.DataFrame) -> None:
    data["obvious_promotion"] = data["text"].str.contains(
        r"\(광고\)|\[광고\]|수신거부", regex=True
    )
    model_columns = [
        "koelectra_actionability",
        "embeddinggemma_actionability",
        "granite_actionability",
    ]
    model_votes = np.column_stack(
        [data[column].ne("GENERAL").to_numpy(dtype=int) for column in model_columns]
    )
    rule_vote = data["rule_level_v2"].ne("GENERAL").to_numpy(dtype=int)
    all_votes = np.column_stack([model_votes, rule_vote])
    vote_sums = all_votes.sum(axis=1)
    data["important_votes"] = vote_sums
    data["binary_disagreement"] = np.minimum(vote_sums, 4 - vote_sums)
    data["actionability_disagreement"] = [
        len(set(values)) - 1
        for values in zip(*(data[column] for column in model_columns))
    ]
    probability_columns = [
        "koelectra_important_probability",
        "embeddinggemma_important_probability",
        "granite_important_probability",
    ]
    uncertainty = np.column_stack(
        [
            1.0 - 2.0 * np.abs(data[column].to_numpy(dtype=float) - 0.5)
            for column in probability_columns
        ]
    ).max(axis=1)
    data["maximum_model_uncertainty"] = np.clip(uncertainty, 0.0, 1.0)
    package_counts = data["package_name"].value_counts()
    data["package_rarity"] = data["package_name"].map(
        lambda value: 1.0 / np.sqrt(package_counts[value])
    )
    data["selection_priority"] = (
        4.0 * data["binary_disagreement"]
        + 2.0 * data["actionability_disagreement"]
        + 2.0 * data["maximum_model_uncertainty"]
        + 1.5 * data["rule_level_v2"].eq("REVIEW").astype(float)
        + data["package_rarity"]
    )
    data["selection_reason"] = [
        ", ".join(
            reason
            for condition, reason in (
                (binary > 0, "모델·규칙 중요 여부 불일치"),
                (action > 0, "3단계 Actionability 불일치"),
                (uncertain >= 0.7, "모델 확률 애매"),
                (level == "REVIEW", "Kotlin REVIEW 경계"),
            )
            if condition
        ) or "의미 군집 대표"
        for binary, action, uncertain, level in zip(
            data["binary_disagreement"],
            data["actionability_disagreement"],
            data["maximum_model_uncertainty"],
            data["rule_level_v2"],
        )
    ]


def select_diverse(
    data: pd.DataFrame, embeddings: np.ndarray, review_count: int
) -> pd.DataFrame:
    cluster_count = min(review_count * 2, len(data))
    clusters = KMeans(
        n_clusters=cluster_count, random_state=42, n_init=20
    ).fit_predict(embeddings)
    data = data.copy()
    data["cluster_id"] = clusters
    ranked = data.sort_values(
        ["selection_priority", "posted_at"], ascending=[False, False]
    )
    representatives = (
        ranked.groupby("cluster_id", as_index=False, group_keys=False)
        .head(1)
        .sort_values("selection_priority", ascending=False)
    )
    selected_indices: list[int] = []
    selected_clusters: set[int] = set()
    package_counts: dict[str, int] = {}
    promotion_count = 0

    def try_select(index: int, row: pd.Series) -> bool:
        nonlocal promotion_count
        package_name = str(row["package_name"])
        if package_counts.get(package_name, 0) >= 3:
            return False
        if bool(row["obvious_promotion"]) and promotion_count >= 5:
            return False
        selected_indices.append(index)
        selected_clusters.add(int(row["cluster_id"]))
        package_counts[package_name] = package_counts.get(package_name, 0) + 1
        promotion_count += int(bool(row["obvious_promotion"]))
        return True

    for index, row in representatives.iterrows():
        try_select(index, row)
        if len(selected_indices) == review_count:
            break

    # A cluster's highest-priority row may be blocked by an app/promotion cap.
    # In that case, try another row from an as-yet unrepresented cluster.
    if len(selected_indices) < review_count:
        for index, row in ranked.iterrows():
            if int(row["cluster_id"]) in selected_clusters:
                continue
            try_select(index, row)
            if len(selected_indices) == review_count:
                break

    # Keep package and promotion limits hard even if cluster uniqueness has to
    # be relaxed to reach the requested review size.
    if len(selected_indices) < review_count:
        for index, row in ranked.iterrows():
            if index in selected_indices:
                continue
            try_select(index, row)
            if len(selected_indices) == review_count:
                break

    if len(selected_indices) != review_count:
        raise ValueError(
            f"Could select only {len(selected_indices)} of {review_count} rows "
            "without exceeding diversity caps"
        )

    selected = data.loc[selected_indices].reset_index(drop=True)
    selected.insert(0, "review_id", [f"AL_{index:03d}" for index in range(1, len(selected) + 1)])
    selected["user_common_actionability"] = ""
    selected["user_personal_preference"] = ""
    selected["review_note"] = ""
    return selected


def make_report(
    room_rows: int, unique: pd.DataFrame, selected: pd.DataFrame
) -> str:
    return "\n".join(
        [
            "# Room Active Learning 검수 후보 선정",
            "",
            "## 결과",
            "",
            f"- 비강제 자동 판정 알림: {room_rows}개",
            f"- 패키지+전처리 문장 중복 제거 후: {len(unique)}개",
            f"- 의미 군집 대표 검수 후보: {len(selected)}개",
            f"- 후보 패키지 수: {selected['package_name'].nunique()}개",
            f"- 모델·규칙 중요 여부 불일치 후보: {(selected['binary_disagreement'] > 0).sum()}개",
            f"- 3단계 모델 불일치 후보: {(selected['actionability_disagreement'] > 0).sum()}개",
            f"- Kotlin REVIEW 후보: {selected['rule_level_v2'].eq('REVIEW').sum()}개",
            f"- 명시적 광고 문구 후보: {selected['obvious_promotion'].sum()}개",
            f"- 동일 패키지 최대 후보: {selected['package_name'].value_counts().max()}개",
            "",
            "## 선정 방식",
            "",
            "1. 사용자 피드백이 아닌 비강제 알림만 사용했다.",
            "2. Android v2 전처리 후 패키지와 문장이 같은 중복을 합쳤다.",
            "3. KoELECTRA, EmbeddingGemma, Granite와 Kotlin 규칙의 불일치를 계산했다.",
            "4. Granite 의미 Embedding을 검수 후보 수의 두 배인 군집으로 묶었다.",
            "5. 군집 대표를 우선하되, 명시적 광고는 최대 5개·동일 패키지는 최대 3개로 제한했다.",
            "",
            "## 검수 방법",
            "",
            "Git 제외 private CSV의 마지막 세 열만 작성한다.",
            "",
            "- `user_common_actionability`: GENERAL / ATTENTION_WORTHY / ACTION_REQUIRED",
            "- `user_personal_preference`: GENERAL / IMPORTANT",
            "- `review_note`: 선택 사항",
            "",
            "알림 원문과 개별 예측은 private CSV에만 저장했다.",
            "",
        ]
    )


def preserve_existing_labels(
    selected: pd.DataFrame, review_output: Path
) -> pd.DataFrame:
    if not review_output.exists():
        return selected

    existing = pd.read_csv(review_output, dtype=str).fillna("")
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
    unique = deduplicate(room)
    training = embedding_experiment.load_training_data(
        embedding_experiment.DATA_PATH
    )

    print("KoELECTRA 전체 그림자 예측")
    add_koelectra_predictions(unique)

    print("EmbeddingGemma 전체 그림자 예측")
    embeddinggemma_probability, _ = run_embedding_model(
        training,
        unique,
        EMBEDDINGGEMMA_ID,
        EMBEDDINGGEMMA_PREFIX,
        args.local_files_only,
    )
    add_prediction_columns(
        unique, "embeddinggemma", embeddinggemma_probability
    )

    print("Granite 전체 그림자 예측 및 군집 Embedding 생성")
    granite_probability, granite_embeddings = run_embedding_model(
        training,
        unique,
        GRANITE_ID,
        GRANITE_PREFIX,
        args.local_files_only,
    )
    add_prediction_columns(unique, "granite", granite_probability)
    add_selection_features(unique)
    selected = select_diverse(unique, granite_embeddings, args.review_count)
    selected = preserve_existing_labels(selected, args.review_output)

    all_columns = [
        "private_id", "package_name", "title", "body", "posted_at",
        "category", "rule_score_v2", "rule_level_v2", "duplicate_count",
        "koelectra_actionability", "koelectra_important_probability",
        "embeddinggemma_actionability", "embeddinggemma_important_probability",
        "granite_actionability", "granite_important_probability",
        "important_votes", "binary_disagreement", "actionability_disagreement",
        "maximum_model_uncertainty", "selection_priority", "selection_reason",
        "obvious_promotion",
    ]
    review_columns = [
        "review_id", "cluster_id", *all_columns,
        "user_common_actionability", "user_personal_preference", "review_note",
    ]
    args.all_output.parent.mkdir(parents=True, exist_ok=True)
    unique[all_columns].to_csv(
        args.all_output, index=False, encoding="utf-8-sig"
    )
    selected[review_columns].to_csv(
        args.review_output, index=False, encoding="utf-8-sig"
    )
    args.report.write_text(
        make_report(len(room), unique, selected), encoding="utf-8"
    )
    summary = {
        "room_rows": len(room),
        "unique_rows": len(unique),
        "selected_rows": len(selected),
        "selected_packages": int(selected["package_name"].nunique()),
        "binary_disagreements": int((selected["binary_disagreement"] > 0).sum()),
        "actionability_disagreements": int(
            (selected["actionability_disagreement"] > 0).sum()
        ),
        "review_output": str(args.review_output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
