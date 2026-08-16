"""Compare three frozen Korean-capable encoders under one fixed protocol."""

from __future__ import annotations

import gc
import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from huggingface_hub import snapshot_download
from sentence_transformers import SentenceTransformer
from transformers import AutoModel, AutoTokenizer

import experiment_embeddinggemma_actionability_v05 as experiment
from actionability_contract import ACTIONABILITY_LABELS, predicted_actionability
from evaluate_granite_v05_v06_blind_holdout import (
    mcnemar_exact,
    model_metrics,
    paired_accuracy_interval,
    paired_important_f1_interval,
)
from notification_text_preprocessor import PREPROCESSING_VERSION, normalize_notification_text


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = PROJECT_DIR / "data" / "public" / "train_notifications_v0.5.csv"
PRIVATE_DIR = PROJECT_DIR / "data" / "private" / "room_export_2026-08-12_raw"
HOLDOUT_PATH = PRIVATE_DIR / "blind_holdout_review_100.csv"
PRIVATE_PREDICTIONS = PRIVATE_DIR / "frozen_backbone_benchmark_v1_predictions.csv"
CACHE_DIR = PROJECT_DIR / ".cache" / "frozen_backbone_benchmark_v1"
MODEL_DIR = PROJECT_DIR / "models" / "frozen_backbone_benchmark_v1"
JSON_OUTPUT = PROJECT_DIR / "reports" / "frozen_backbone_benchmark_v1.json"
MARKDOWN_OUTPUT = PROJECT_DIR / "reports" / "frozen_backbone_benchmark_v1.md"
MAX_LENGTH = 64
BENCHMARK_ROWS = 30

MODELS = (
    {
        "key": "granite_97m_r2",
        "model_id": "ibm-granite/granite-embedding-97m-multilingual-r2",
        "adapter": "sentence_transformer",
        "prefix": "",
    },
    {
        "key": "embeddinggemma_300m",
        "model_id": "google/embeddinggemma-300m",
        "adapter": "sentence_transformer",
        "prefix": "task: classification | query: ",
    },
    {
        "key": "koelectra_small_v3",
        "model_id": "monologg/koelectra-small-v3-discriminator",
        "adapter": "transformers_mean_pool",
        "prefix": "",
    },
)


def load_holdout() -> pd.DataFrame:
    data = pd.read_csv(HOLDOUT_PATH).fillna("")
    if not data["user_common_actionability"].isin(ACTIONABILITY_LABELS).all():
        raise ValueError("Room 100개 공통 라벨이 완성되지 않았습니다.")
    data["text"] = [
        normalize_notification_text(package, title, body)
        for package, title, body in zip(
            data["package_name"], data["title"], data["body"]
        )
    ]
    return data


def cache_path(model_id: str, adapter: str, prefix: str, texts: list[str]) -> Path:
    digest = hashlib.sha256()
    for value in (model_id, adapter, prefix, PREPROCESSING_VERSION, str(MAX_LENGTH), *texts):
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return CACHE_DIR / f"{model_id.replace('/', '__').lower()}_{digest.hexdigest()[:16]}.npz"


def snapshot_bytes(model_id: str) -> int:
    snapshot = Path(snapshot_download(repo_id=model_id, local_files_only=True))
    return sum(path.stat().st_size for path in snapshot.rglob("*") if path.is_file())


def benchmark_calls(callable_encode: object, texts: list[str]) -> dict[str, float]:
    samples = texts[:BENCHMARK_ROWS]
    for text in samples[:5]:
        callable_encode([text])
    durations = []
    for text in samples:
        started = time.perf_counter()
        callable_encode([text])
        durations.append((time.perf_counter() - started) * 1000)
    return {
        "single_median_ms": float(np.median(durations)),
        "single_p95_ms": float(np.percentile(durations, 95)),
        "single_samples": len(durations),
    }


def sentence_transformer_embeddings(
    config: dict[str, str], texts: list[str]
) -> tuple[np.ndarray, dict[str, object]]:
    load_started = time.perf_counter()
    model = SentenceTransformer(config["model_id"], device="cpu", local_files_only=True)
    model.max_seq_length = MAX_LENGTH
    load_seconds = time.perf_counter() - load_started
    prepared = [config["prefix"] + text for text in texts]
    target = cache_path(config["model_id"], config["adapter"], config["prefix"], texts)
    if target.exists():
        vectors = np.load(target)["embeddings"]
        batch_seconds = 0.0
        cache_hit = True
    else:
        started = time.perf_counter()
        vectors = model.encode(
            prepared,
            batch_size=16,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype(np.float32)
        batch_seconds = time.perf_counter() - started
        target.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(target, embeddings=vectors)
        cache_hit = False

    def encode(values: list[str]) -> np.ndarray:
        return model.encode(
            [config["prefix"] + value for value in values],
            batch_size=1,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    timing = benchmark_calls(encode, texts[-BENCHMARK_ROWS:])
    metadata: dict[str, object] = {
        "embedding_dimension": int(vectors.shape[1]),
        "parameter_count": int(sum(parameter.numel() for parameter in model.parameters())),
        "source_snapshot_bytes": snapshot_bytes(config["model_id"]),
        "load_seconds": load_seconds,
        "batch_encode_seconds": batch_seconds,
        "batch_cache_hit": cache_hit,
        **timing,
    }
    del model
    gc.collect()
    return vectors, metadata


def koelectra_embeddings(
    config: dict[str, str], texts: list[str]
) -> tuple[np.ndarray, dict[str, object]]:
    load_started = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(config["model_id"], local_files_only=True)
    model = AutoModel.from_pretrained(config["model_id"], local_files_only=True)
    model.eval()
    load_seconds = time.perf_counter() - load_started
    target = cache_path(config["model_id"], config["adapter"], config["prefix"], texts)

    def encode(values: list[str]) -> np.ndarray:
        encoded = tokenizer(
            values,
            padding=True,
            truncation=True,
            max_length=MAX_LENGTH,
            return_tensors="pt",
        )
        with torch.inference_mode():
            hidden = model(**encoded).last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).to(hidden.dtype)
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
        return pooled.cpu().numpy().astype(np.float32)

    if target.exists():
        vectors = np.load(target)["embeddings"]
        batch_seconds = 0.0
        cache_hit = True
    else:
        chunks = []
        started = time.perf_counter()
        for offset in range(0, len(texts), 16):
            chunks.append(encode(texts[offset : offset + 16]))
        vectors = np.concatenate(chunks, axis=0)
        batch_seconds = time.perf_counter() - started
        target.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(target, embeddings=vectors)
        cache_hit = False

    timing = benchmark_calls(encode, texts[-BENCHMARK_ROWS:])
    metadata: dict[str, object] = {
        "embedding_dimension": int(vectors.shape[1]),
        "parameter_count": int(sum(parameter.numel() for parameter in model.parameters())),
        "source_snapshot_bytes": snapshot_bytes(config["model_id"]),
        "load_seconds": load_seconds,
        "batch_encode_seconds": batch_seconds,
        "batch_cache_hit": cache_hit,
        **timing,
    }
    del model, tokenizer
    gc.collect()
    return vectors, metadata


def get_embeddings(
    config: dict[str, str], texts: list[str]
) -> tuple[np.ndarray, dict[str, object]]:
    if config["adapter"] == "sentence_transformer":
        return sentence_transformer_embeddings(config, texts)
    return koelectra_embeddings(config, texts)


def evaluate(
    training: pd.DataFrame,
    holdout: pd.DataFrame,
    training_vectors: np.ndarray,
    holdout_vectors: np.ndarray,
    model_key: str,
) -> tuple[dict[str, object], list[str]]:
    labels = training["actionability_id"].to_numpy(dtype=np.int32)
    folds = training["cv_fold"].to_numpy(dtype=np.int32)
    oof = np.zeros((len(training), 3), dtype=np.float64)
    for fold in range(5):
        train_mask = folds != fold
        validation_mask = folds == fold
        head = experiment.make_head("mlp_32")
        experiment.fit_head(
            head, "mlp_32", training_vectors[train_mask], labels[train_mask]
        )
        oof[validation_mask] = head.predict_proba(training_vectors[validation_mask])

    final_head = experiment.make_head("mlp_32")
    experiment.fit_head(final_head, "mlp_32", training_vectors, labels)
    holdout_probability = final_head.predict_proba(holdout_vectors)
    predictions = predicted_actionability(holdout_probability)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    head_path = MODEL_DIR / f"{model_key}_mlp_32.joblib"
    joblib.dump(final_head, head_path)
    cv_actual = pd.Series([ACTIONABILITY_LABELS[value] for value in labels])
    cv_predicted = pd.Series(predicted_actionability(oof))
    return (
        {
            "cross_validation": model_metrics(cv_actual, cv_predicted),
            "room_holdout": model_metrics(
                holdout["user_common_actionability"], pd.Series(predictions)
            ),
            "head_bytes": head_path.stat().st_size,
        },
        predictions,
    )


def markdown(results: dict[str, object]) -> str:
    lines = [
        "# Frozen Backbone 동일조건 모델 비교 v1",
        "",
        "세 encoder를 고정하고 동일한 v0.5 600개, Android v2 전처리, 고정 5-Fold, MLP 32-unit으로 비교했다.",
        "",
        "## 성능",
        "",
        "| 모델 | 합성 CV Accuracy | 합성 CV Macro F1 | Room Accuracy | Room 등장 클래스 Macro F1 | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for config in MODELS:
        value = results["models"][config["key"]]
        cv = value["evaluation"]["cross_validation"]
        room = value["evaluation"]["room_holdout"]
        binary = room["important_binary"]
        lines.append(
            f"| {config['key']} | {cv['three_class_accuracy']:.3f} | "
            f"{cv['three_class_macro_f1']:.3f} | {room['three_class_accuracy']:.3f} | "
            f"{room['observed_class_macro_f1']:.3f} | {binary['precision']:.3f} | "
            f"{binary['recall']:.3f} | {binary['f1']:.3f} | "
            f"{binary['false_positive']} | {binary['false_negative']} |"
        )
    lines.extend(
        [
            "",
            "## 동일 Room 행 대응 비교",
            "",
            "| 비교 | Accuracy 차이 | Paired bootstrap 95% CI | 중요 F1 차이 | 중요 F1 95% CI | McNemar p |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for comparison, value in results["paired_comparisons"].items():
        accuracy = value["accuracy"]
        important = value["important_f1"]
        lines.append(
            f"| {comparison} | {accuracy['right_minus_left']:+.3f} | "
            f"{accuracy['bootstrap_95_low']:+.3f}~{accuracy['bootstrap_95_high']:+.3f} | "
            f"{important['right_minus_left']:+.3f} | "
            f"{important['bootstrap_95_low']:+.3f}~{important['bootstrap_95_high']:+.3f} | "
            f"{value['mcnemar']['two_sided_exact_p']:.6f} |"
        )
    lines.extend(
        [
            "",
            "## 로컬 CPU 참고 측정",
            "",
            "| 모델 | 파라미터 | 원본 스냅샷 MiB | Embedding 차원 | 단일 median ms | 단일 p95 ms | Head KiB |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for config in MODELS:
        value = results["models"][config["key"]]
        runtime = value["runtime"]
        lines.append(
            f"| {config['key']} | {runtime['parameter_count']:,} | "
            f"{runtime['source_snapshot_bytes'] / 1024**2:.1f} | "
            f"{runtime['embedding_dimension']} | {runtime['single_median_ms']:.2f} | "
            f"{runtime['single_p95_ms']:.2f} | "
            f"{value['evaluation']['head_bytes'] / 1024:.1f} |"
        )
    lines.extend(
        [
            "",
            "Mac CPU + PyTorch/SentenceTransformers 측정이므로 Android TFLite 성능이 아니다.",
            "Room 100개 라벨을 확인한 뒤 프로토콜을 고정했으므로 최종 블라인드 확정 결과가 아니라 통제된 탐색 비교다.",
            "품질 점 추정치는 EmbeddingGemma가 1위지만 Granite와의 차이는 통계적으로 확정되지 않았다.",
            "Granite는 EmbeddingGemma보다 다운로드 스냅샷이 작고 로컬 추론이 빨라 현재 모바일 균형 후보로 유지한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    training = experiment.load_training_data(DATA_PATH)
    holdout = load_holdout()
    all_texts = list(dict.fromkeys([*training["text"], *holdout["text"]]))
    positions = {text: index for index, text in enumerate(all_texts)}
    training_indices = [positions[text] for text in training["text"]]
    holdout_indices = [positions[text] for text in holdout["text"]]
    results: dict[str, object] = {
        "protocol": {
            "training_rows": len(training),
            "holdout_rows": len(holdout),
            "max_length": MAX_LENGTH,
            "head": "mlp_32",
            "random_seed": 42,
            "preprocessing": PREPROCESSING_VERSION,
            "blind_status": "RETROSPECTIVE_CONTROLLED_NOT_PRISTINE_BLIND",
        },
        "models": {},
    }
    private = holdout[["review_id", "private_id", "user_common_actionability"]].copy()
    predictions_by_model: dict[str, np.ndarray] = {}
    for config in MODELS:
        print(f"\n{config['key']} embedding")
        vectors, runtime = get_embeddings(config, all_texts)
        evaluation, predictions = evaluate(
            training,
            holdout,
            vectors[training_indices],
            vectors[holdout_indices],
            config["key"],
        )
        results["models"][config["key"]] = {
            "model_id": config["model_id"],
            "adapter": config["adapter"],
            "prefix": config["prefix"],
            "runtime": runtime,
            "evaluation": evaluation,
        }
        predictions_by_model[config["key"]] = np.asarray(predictions)
        private[f"{config['key']}_actionability"] = predictions
        del vectors
        gc.collect()

    actual = holdout["user_common_actionability"].to_numpy()
    results["paired_comparisons"] = {}
    keys = [config["key"] for config in MODELS]
    for left_index, left in enumerate(keys):
        for right in keys[left_index + 1 :]:
            accuracy = paired_accuracy_interval(
                actual, predictions_by_model[left], predictions_by_model[right]
            )
            important_f1 = paired_important_f1_interval(
                actual, predictions_by_model[left], predictions_by_model[right]
            )
            results["paired_comparisons"][f"{right}_minus_{left}"] = {
                "accuracy": {
                    "right_minus_left": accuracy["v06_minus_v05"],
                    "bootstrap_95_low": accuracy["bootstrap_95_low"],
                    "bootstrap_95_high": accuracy["bootstrap_95_high"],
                },
                "important_f1": {
                    "right_minus_left": important_f1["v06_minus_v05"],
                    "bootstrap_95_low": important_f1["bootstrap_95_low"],
                    "bootstrap_95_high": important_f1["bootstrap_95_high"],
                },
                "mcnemar": mcnemar_exact(
                    actual, predictions_by_model[left], predictions_by_model[right]
                ),
            }

    PRIVATE_PREDICTIONS.parent.mkdir(parents=True, exist_ok=True)
    private.to_csv(PRIVATE_PREDICTIONS, index=False, encoding="utf-8-sig")
    JSON_OUTPUT.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(markdown(results), encoding="utf-8")
    print("\n" + markdown(results))


if __name__ == "__main__":
    main()
