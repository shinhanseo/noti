"""Evaluate frozen EmbeddingGemma embeddings with thin actionability heads."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)
from sklearn.neural_network import MLPClassifier
from sklearn.utils.class_weight import compute_sample_weight

from actionability_contract import (
    ACTIONABILITY_LABELS,
    encode_actionability,
    important_probabilities,
    model_score_delta,
    predicted_actionability,
    probability_columns,
)
from evaluate_real_room_v03 import load_room_candidates
from notification_text_preprocessor import (
    PREPROCESSING_VERSION,
    normalize_notification_text,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_ID = "google/embeddinggemma-300m"
CLASSIFICATION_PREFIX = "task: classification | query: "
MAX_SEQUENCE_LENGTH = 64
DATA_PATH = PROJECT_DIR / "data" / "public" / "train_notifications_v0.5.csv"
PRIVATE_DIR = PROJECT_DIR / "data" / "private" / "room_export_2026-08-12_raw"
DATABASE_PATH = PRIVATE_DIR / "noti.db"
LABELS_PATH = PRIVATE_DIR / "room_review_holdout_labels.csv"
PRIVATE_OUTPUT_PATH = PRIVATE_DIR / "embeddinggemma_actionability_predictions.csv"
POLICY_REPLAY_PATH = PRIVATE_DIR / "android_policy_replay_output.tsv"
REPORT_JSON_PATH = PROJECT_DIR / "reports" / "embeddinggemma_actionability_v0.5.json"
REPORT_MARKDOWN_PATH = (
    PROJECT_DIR / "reports" / "embeddinggemma_actionability_v0.5.md"
)
CACHE_DIR = PROJECT_DIR / ".cache" / "pretrained_embeddings"
MODEL_OUTPUT_DIR = PROJECT_DIR / "models" / "embeddinggemma_actionability_v0.5"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    parser.add_argument("--database", type=Path, default=DATABASE_PATH)
    parser.add_argument("--labels", type=Path, default=LABELS_PATH)
    parser.add_argument("--private-output", type=Path, default=PRIVATE_OUTPUT_PATH)
    parser.add_argument("--report-json", type=Path, default=REPORT_JSON_PATH)
    parser.add_argument("--report-markdown", type=Path, default=REPORT_MARKDOWN_PATH)
    parser.add_argument("--force-embeddings", action="store_true")
    parser.add_argument("--local-files-only", action="store_true")
    return parser.parse_args()


def load_training_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    eligible = data["model_eligible"].astype(str).str.lower().eq("true")
    eligible &= data["training_eligible"].astype(str).str.lower().eq("true")
    data = data[eligible & data["clarity"].eq("CLEAR")].copy()
    data["text"] = [
        normalize_notification_text(package_name, title, body)
        for package_name, title, body in zip(
            data["package_name"].fillna(""), data["title"], data["body"]
        )
    ]
    data["actionability_id"] = encode_actionability(
        data["actionability"].astype(str).tolist()
    )
    if data["cv_fold"].isna().any():
        raise ValueError("고정 cv_fold가 없는 학습 행이 있습니다.")
    data["cv_fold"] = data["cv_fold"].astype(int)
    return data.reset_index(drop=True)


def load_holdout(database: Path, labels_path: Path) -> pd.DataFrame:
    room = load_room_candidates(database)
    labels = pd.read_csv(labels_path, dtype={"private_id": str}).set_index(
        "private_id"
    )
    room["personal_preference"] = room["private_id"].map(
        labels["personal_preference"]
    )
    room["common_actionability"] = room["private_id"].map(
        labels["common_actionability"]
    )
    room = room[room["personal_preference"].notna()].copy()
    room["human_label"] = room["personal_preference"].map(
        {"GENERAL": 0, "IMPORTANT": 1}
    )
    if room["human_label"].isna().any():
        raise ValueError("알 수 없는 개인 선호 라벨이 있습니다.")
    room["text"] = [
        normalize_notification_text(package_name, title, body)
        for package_name, title, body in zip(
            room["package_name"].fillna(""), room["title"], room["body"]
        )
    ]
    return room.reset_index(drop=True)


def embedding_cache_path(texts: list[str]) -> Path:
    digest = hashlib.sha256()
    digest.update(MODEL_ID.encode("utf-8"))
    digest.update(b"\0")
    for text in texts:
        digest.update(text.encode("utf-8"))
        digest.update(b"\0")
    safe_model_id = MODEL_ID.replace("/", "__").lower()
    return CACHE_DIR / f"{safe_model_id}_v05_seq64_{digest.hexdigest()[:12]}.npz"


def create_embeddings(
    texts: list[str], force: bool, local_files_only: bool
) -> tuple[np.ndarray, dict[str, float | int | bool | str], object]:
    from huggingface_hub import snapshot_download
    from sentence_transformers import SentenceTransformer

    prepared = [CLASSIFICATION_PREFIX + text for text in texts]
    target = embedding_cache_path(prepared)
    load_started = time.perf_counter()
    model = SentenceTransformer(
        MODEL_ID, device="cpu", local_files_only=local_files_only
    )
    model.max_seq_length = MAX_SEQUENCE_LENGTH
    model_load_seconds = time.perf_counter() - load_started

    if target.exists() and not force:
        embeddings = np.load(target)["embeddings"]
        cache_hit = True
        embedding_seconds = 0.0
    else:
        started = time.perf_counter()
        embeddings = model.encode(
            prepared,
            batch_size=16,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)
        embedding_seconds = time.perf_counter() - started
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(target, embeddings=embeddings)
        cache_hit = False

    snapshot = Path(snapshot_download(repo_id=MODEL_ID, local_files_only=True))
    snapshot_bytes = sum(
        path.stat().st_size for path in snapshot.rglob("*") if path.is_file()
    )
    timing: dict[str, float | int | bool | str] = {
        "cache_hit": cache_hit,
        "model_load_seconds": model_load_seconds,
        "embedding_seconds": embedding_seconds,
        "sentences_per_second": (
            len(texts) / embedding_seconds if embedding_seconds else 0.0
        ),
        "source_snapshot_bytes": snapshot_bytes,
        "cache_path": str(target.relative_to(PROJECT_DIR)),
    }
    return embeddings, timing, model


def make_head(name: str) -> object:
    if name == "logistic_regression":
        return LogisticRegression(
            max_iter=3000, class_weight="balanced", random_state=42
        )
    if name == "mlp_32":
        return MLPClassifier(
            hidden_layer_sizes=(32,),
            activation="relu",
            alpha=0.001,
            max_iter=2000,
            random_state=42,
        )
    raise ValueError(f"알 수 없는 head: {name}")


def fit_head(head: object, name: str, x: np.ndarray, y: np.ndarray) -> None:
    if name == "mlp_32":
        head.fit(x, y, sample_weight=compute_sample_weight("balanced", y))
    else:
        head.fit(x, y)


def choose_recall_threshold(
    labels: np.ndarray, probabilities: np.ndarray, minimum_recall: float = 0.9
) -> float:
    precisions, recalls, thresholds = precision_recall_curve(labels, probabilities)
    candidates = [
        (float(precision), float(threshold))
        for precision, recall, threshold in zip(
            precisions[:-1], recalls[:-1], thresholds
        )
        if recall >= minimum_recall
    ]
    return max(candidates, key=lambda row: (row[0], row[1]))[1] if candidates else 0.5


def binary_metrics(
    actual: np.ndarray, probabilities: np.ndarray, threshold: float
) -> dict[str, object]:
    predicted = (probabilities >= threshold).astype(np.int32)
    matrix = confusion_matrix(actual, predicted, labels=[0, 1])
    return {
        "threshold": threshold,
        "accuracy": float(accuracy_score(actual, predicted)),
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
        "false_positive": int(matrix[0, 1]),
        "false_negative": int(matrix[1, 0]),
        "confusion_matrix": matrix.tolist(),
    }


def actionability_metrics(
    actual: np.ndarray, probabilities: np.ndarray
) -> dict[str, object]:
    predicted = np.argmax(probabilities, axis=1)
    precision, recall, f1, support = precision_recall_fscore_support(
        actual, predicted, labels=[0, 1, 2], zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_f1": float(
            f1_score(actual, predicted, labels=[0, 1, 2], average="macro")
        ),
        "confusion_matrix": confusion_matrix(
            actual, predicted, labels=[0, 1, 2]
        ).tolist(),
        "per_class": {
            label: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, label in enumerate(ACTIONABILITY_LABELS)
        },
    }


def cross_validate(
    embeddings: np.ndarray, data: pd.DataFrame, head_name: str
) -> tuple[dict[str, object], np.ndarray]:
    labels = data["actionability_id"].to_numpy(dtype=np.int32)
    probabilities = np.zeros((len(data), len(ACTIONABILITY_LABELS)), dtype=np.float64)
    fold_rows = []
    for fold in range(5):
        validation = data["cv_fold"].eq(fold).to_numpy()
        train = ~validation
        train_groups = set(data.loc[train, "template_group"])
        validation_groups = set(data.loc[validation, "template_group"])
        overlap = len(train_groups & validation_groups)
        if overlap:
            raise RuntimeError(f"fold {fold} template_group overlap: {overlap}")
        head = make_head(head_name)
        fit_head(head, head_name, embeddings[train], labels[train])
        fold_probability = head.predict_proba(embeddings[validation])
        probabilities[validation] = fold_probability
        fold_rows.append(
            {
                "fold": fold,
                "rows": int(validation.sum()),
                "actionability": actionability_metrics(
                    labels[validation], fold_probability
                ),
            }
        )
    binary_actual = (labels > 0).astype(np.int32)
    important = important_probabilities(probabilities)
    threshold = choose_recall_threshold(binary_actual, important)
    result = {
        "head": head_name,
        "folds": fold_rows,
        "pooled_actionability": actionability_metrics(labels, probabilities),
        "pooled_binary_at_0_5": binary_metrics(binary_actual, important, 0.5),
        "pooled_binary_at_selected_threshold": binary_metrics(
            binary_actual, important, threshold
        ),
    }
    return result, probabilities


def measure_single_latency(model: object, text: str) -> dict[str, float]:
    prepared = CLASSIFICATION_PREFIX + text
    model.encode([prepared], show_progress_bar=False, normalize_embeddings=True)
    samples = []
    for _ in range(10):
        started = time.perf_counter()
        model.encode([prepared], show_progress_bar=False, normalize_embeddings=True)
        samples.append((time.perf_counter() - started) * 1000)
    return {
        "median": float(np.median(samples)),
        "p95": float(np.percentile(samples, 95)),
        "minimum": float(np.min(samples)),
        "maximum": float(np.max(samples)),
    }


def evaluate_holdout(
    holdout: pd.DataFrame,
    probabilities: np.ndarray,
    cv_threshold: float,
) -> dict[str, object]:
    important = important_probabilities(probabilities)
    personal_actual = holdout["human_label"].to_numpy(dtype=np.int32)
    predicted_labels = predicted_actionability(probabilities)
    common_actual = holdout["common_actionability"].astype(str).to_numpy()
    return {
        "personal_at_0_5": binary_metrics(personal_actual, important, 0.5),
        "personal_at_cv_threshold": binary_metrics(
            personal_actual, important, cv_threshold
        ),
        "common_actionability": {
            "accuracy": float(accuracy_score(common_actual, predicted_labels)),
            "macro_f1": float(
                f1_score(
                    common_actual,
                    predicted_labels,
                    labels=list(ACTIONABILITY_LABELS),
                    average="macro",
                    zero_division=0,
                )
            ),
            "confusion_matrix": confusion_matrix(
                common_actual,
                predicted_labels,
                labels=list(ACTIONABILITY_LABELS),
            ).tolist(),
        },
        "predicted_actionability_counts": {
            label: predicted_labels.count(label) for label in ACTIONABILITY_LABELS
        },
    }


def simulate_android_product(
    holdout: pd.DataFrame,
    important_probability: np.ndarray,
) -> dict[str, object]:
    replay = pd.read_csv(POLICY_REPLAY_PATH, sep="\t", dtype={"private_id": str})
    replay = replay.set_index("private_id")
    actual = holdout["human_label"].to_numpy(dtype=np.int32)
    predictions = []
    rows = []
    for index, row in holdout.iterrows():
        policy = replay.loc[row["private_id"]]
        rule_score = int(policy["new_score"])
        rule_level = str(policy["new_level"])
        score_delta = model_score_delta(important_probability[index])
        final_score = rule_score + score_delta if rule_level == "REVIEW" else rule_score
        final_level = (
            "IMPORTANT" if final_score >= 40 else
            "REVIEW" if final_score >= 25 else
            "GENERAL"
        )
        prediction = int(final_level == "IMPORTANT")
        predictions.append(prediction)
        rows.append(
            {
                "private_id": row["private_id"],
                "rule_score": rule_score,
                "rule_level": rule_level,
                "ai_executed": rule_level == "REVIEW",
                "model_score_delta": score_delta if rule_level == "REVIEW" else 0,
                "final_score": final_score,
                "final_level": final_level,
                "human_label": int(row["human_label"]),
            }
        )
    predicted = np.asarray(predictions, dtype=np.int32)
    matrix = confusion_matrix(actual, predicted, labels=[0, 1])
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "correct_rows": int(np.sum(actual == predicted)),
        "false_positive": int(matrix[0, 1]),
        "false_negative": int(matrix[1, 0]),
        "confusion_matrix": matrix.tolist(),
        "rows": rows,
    }


def make_markdown(result: dict[str, object]) -> str:
    lines = [
        f"# {result['model']} + Thin Head v0.5 실험",
        "",
        "## 조건",
        "",
        f"- 학습 데이터: {result['training_rows']}개",
        "- 분할: 고정 5-Fold, template_group 중복 0",
        f"- 입력 전처리: `{result['text_preprocessing']}`",
        f"- 프롬프트: `{result['classification_prefix']}`",
        f"- `{result['model']}`은 고정하고 얇은 분류 Head만 학습",
        "",
        "## 교차검증",
        "",
        "| Head | 3단계 Accuracy | Macro F1 | 이진 Accuracy | Precision | Recall | FP | FN | 임계값 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["cross_validation"]:
        action = row["pooled_actionability"]
        binary = row["pooled_binary_at_selected_threshold"]
        lines.append(
            f"| `{row['head']}` | {action['accuracy']:.3f} | "
            f"{action['macro_f1']:.3f} | {binary['accuracy']:.3f} | "
            f"{binary['precision']:.3f} | {binary['recall']:.3f} | "
            f"{binary['false_positive']} | {binary['false_negative']} | "
            f"{binary['threshold']:.3f} |"
        )
    holdout = result["independent_holdout"]
    lines.extend(
        [
            "",
            f"선택 Head: `{result['selected_head']}` (홀드아웃을 보기 전에 Macro F1로 선택)",
            "",
            "## 실제 Room 독립 홀드아웃 6개",
            "",
            "| Head | 개인 Accuracy(0.5) | Precision | Recall | CV 임계값 Accuracy | 공통 Actionability Accuracy |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for head_name, head_result in result["holdout_by_head"].items():
        at_half = head_result["personal_at_0_5"]
        at_cv = head_result["personal_at_cv_threshold"]
        common = head_result["common_actionability"]
        lines.append(
            f"| `{head_name}` | {at_half['accuracy']:.3f} | "
            f"{at_half['precision']:.3f} | {at_half['recall']:.3f} | "
            f"{at_cv['accuracy']:.3f} | {common['accuracy']:.3f} |"
        )
    lines.extend(
        [
            "",
            f"선택 Head의 앱 전체 파이프라인 Accuracy: "
            f"{result['android_product_simulation']['accuracy']:.3f} "
            f"({result['android_product_simulation']['correct_rows']}/6)",
            f"- 공통 Actionability Accuracy: {holdout['common_actionability']['accuracy']:.3f}",
            f"- 공통 Actionability Macro F1: {holdout['common_actionability']['macro_f1']:.3f}",
            "",
            "## 개발 Mac CPU 참고값",
            "",
            f"- 원본 Hugging Face 스냅샷: {result['source_snapshot_bytes'] / 1024 / 1024:.1f} MiB",
            f"- 분류 Head: {result['head_size_bytes'] / 1024:.1f} KiB",
            f"- 모델 로딩: {result['timing']['model_load_seconds']:.2f}초",
            f"- 단일 알림 Embedding median/P95: {result['single_notification_latency_ms']['median']:.2f}/"
            f"{result['single_notification_latency_ms']['p95']:.2f} ms",
            "",
            "## 제한",
            "",
            "- 학습 데이터 600개는 합성 중심이며 실제 홀드아웃은 6개뿐이다.",
            "- 이 수치는 Python FP32 모델의 Mac CPU 결과이며 Android LiteRT 성능이 아니다.",
            "- 모델 전체를 미세조정한 것이 아니라 고정 Embedding 위의 분류 Head만 학습했다.",
            "- Android 채택 전 양자화·변환·실제 기기 RAM/배터리 측정이 필요하다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    np.random.seed(42)
    training = load_training_data(args.data)
    holdout = load_holdout(args.database, args.labels)
    all_texts = training["text"].tolist() + holdout["text"].tolist()
    embeddings, timing, embedding_model = create_embeddings(
        all_texts, args.force_embeddings, args.local_files_only
    )
    training_embeddings = embeddings[: len(training)]
    holdout_embeddings = embeddings[len(training) :]

    cv_results = []
    for head_name in ("logistic_regression", "mlp_32"):
        print(f"고정 5-Fold: {head_name}")
        cv_result, _ = cross_validate(training_embeddings, training, head_name)
        cv_results.append(cv_result)
    selected = max(
        cv_results,
        key=lambda row: (
            row["pooled_actionability"]["macro_f1"],
            row["pooled_binary_at_selected_threshold"]["recall"],
        ),
    )
    selected_name = str(selected["head"])
    threshold = float(
        selected["pooled_binary_at_selected_threshold"]["threshold"]
    )
    labels = training["actionability_id"].to_numpy(dtype=np.int32)
    holdout_by_head: dict[str, object] = {}
    selected_head = None
    holdout_probability = None
    for cv_result in cv_results:
        head_name = str(cv_result["head"])
        candidate_head = make_head(head_name)
        fit_head(candidate_head, head_name, training_embeddings, labels)
        candidate_probability = candidate_head.predict_proba(holdout_embeddings)
        cv_threshold = float(
            cv_result["pooled_binary_at_selected_threshold"]["threshold"]
        )
        holdout_by_head[head_name] = evaluate_holdout(
            holdout, candidate_probability, cv_threshold
        )
        if head_name == selected_name:
            selected_head = candidate_head
            holdout_probability = candidate_probability
    if selected_head is None or holdout_probability is None:
        raise RuntimeError("선택한 분류 Head의 홀드아웃 예측이 없습니다.")
    holdout_important = important_probabilities(holdout_probability)
    holdout_binary = (holdout_important >= threshold).astype(np.int32)
    personal_actual = holdout["human_label"].to_numpy(dtype=np.int32)
    personal = binary_metrics(personal_actual, holdout_important, threshold)
    predicted_labels = predicted_actionability(holdout_probability)
    common_actual = holdout["common_actionability"].astype(str).to_numpy()
    common = {
        "accuracy": float(accuracy_score(common_actual, predicted_labels)),
        "macro_f1": float(
            f1_score(
                common_actual,
                predicted_labels,
                labels=list(ACTIONABILITY_LABELS),
                average="macro",
                zero_division=0,
            )
        ),
        "confusion_matrix": confusion_matrix(
            common_actual, predicted_labels, labels=list(ACTIONABILITY_LABELS)
        ).tolist(),
    }
    holdout["predicted_actionability"] = predicted_labels
    for column, values in probability_columns(holdout_probability).items():
        holdout[column] = values
    holdout["important_probability"] = holdout_important
    holdout["model_score_delta"] = [
        model_score_delta(value) for value in holdout_important
    ]
    holdout["binary_prediction"] = holdout_binary

    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    head_path = MODEL_OUTPUT_DIR / f"{selected_name}.joblib"
    joblib.dump(selected_head, head_path, compress=3)
    result: dict[str, object] = {
        "status": "experiment_complete",
        "model": MODEL_ID,
        "dataset_version": "0.5",
        "training_rows": len(training),
        "text_preprocessing": PREPROCESSING_VERSION,
        "classification_prefix": CLASSIFICATION_PREFIX,
        "embedding_dimensions": int(embeddings.shape[1]),
        "cross_validation": cv_results,
        "selected_head": selected_name,
        "selection_rule": "highest pooled actionability macro_f1 before holdout",
        "independent_holdout": {
            "rows": len(holdout),
            "personal_metrics": personal,
            "common_actionability": common,
            "predicted_actionability_counts": {
                label: predicted_labels.count(label)
                for label in ACTIONABILITY_LABELS
            },
        },
        "holdout_by_head": holdout_by_head,
        "android_product_simulation": simulate_android_product(
            holdout, holdout_important
        ),
        "source_snapshot_bytes": int(timing["source_snapshot_bytes"]),
        "head_size_bytes": head_path.stat().st_size,
        "timing": timing,
        "single_notification_latency_ms": measure_single_latency(
            embedding_model, holdout.iloc[0]["text"]
        ),
    }
    output_columns = [
        "private_id", "package_name", "title", "body", "human_label",
        "common_actionability", "predicted_actionability",
        *probability_columns(holdout_probability).keys(),
        "important_probability", "model_score_delta", "binary_prediction",
    ]
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    holdout[output_columns].to_csv(
        args.private_output, index=False, encoding="utf-8-sig"
    )
    args.report_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.report_markdown.write_text(make_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
