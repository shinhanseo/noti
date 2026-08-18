"""Compare three new Korean-capable embedding backbones under one fixed protocol."""

from __future__ import annotations

import gc
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

# Transformers reads this value during import, so set it before importing the
# SentenceTransformers stack. The directory is already ignored by ml/.gitignore.
PROJECT_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_MODULES_CACHE", str(PROJECT_DIR / ".cache" / "huggingface_modules"))

import joblib
import numpy as np
import pandas as pd
from huggingface_hub import snapshot_download
from huggingface_hub.constants import HF_HUB_CACHE
from sentence_transformers import SentenceTransformer

import experiment_embeddinggemma_actionability_v05 as experiment
from actionability_contract import ACTIONABILITY_LABELS, predicted_actionability
from evaluate_granite_v05_v06_blind_holdout import (
    mcnemar_exact,
    model_metrics,
    paired_accuracy_interval,
    paired_important_f1_interval,
)
from notification_text_preprocessor import PREPROCESSING_VERSION, normalize_notification_text


DATA_PATH = PROJECT_DIR / "data" / "public" / "train_notifications_v0.5.csv"
ROOM_100_PATH = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-12_raw"
    / "blind_holdout_review_100.csv"
)
ROOM_45_PATH = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-16_raw"
    / "incremental_holdout_review.csv"
)
PRIVATE_PREDICTIONS = (
    PROJECT_DIR
    / "data"
    / "private"
    / "new_ondevice_backbone_benchmark_v1_predictions.csv"
)
CACHE_DIR = PROJECT_DIR / ".cache" / "new_ondevice_backbone_benchmark_v1"
MODEL_DIR = PROJECT_DIR / "models" / "new_ondevice_backbone_benchmark_v1"
JSON_OUTPUT = PROJECT_DIR / "reports" / "new_ondevice_backbone_benchmark_v1.json"
MARKDOWN_OUTPUT = PROJECT_DIR / "reports" / "new_ondevice_backbone_benchmark_v1.md"
MAX_LENGTH = 64
BENCHMARK_ROWS = 30

MODELS: tuple[dict[str, Any], ...] = (
    {
        "key": "kor_static_embedding_128",
        "model_id": "kekeappa/kor-static-embedding-128",
        "prompt_name": None,
        "trust_remote_code": False,
        "batch_size": 64,
    },
    {
        "key": "lfm2_5_embedding_350m",
        "model_id": "LiquidAI/LFM2.5-Embedding-350M",
        "prompt_name": "document",
        "trust_remote_code": True,
        "batch_size": 16,
    },
    {
        "key": "nomic_embed_text_v2_moe",
        "model_id": "nomic-ai/nomic-embed-text-v2-moe",
        "prompt_name": "passage",
        "trust_remote_code": True,
        "batch_size": 16,
    },
)

REJECTED_PREFLIGHT = {
    "model_id": "HancomInSpaceAI/HiEmbed_base_onnx_v1",
    "status": "REJECTED_BEFORE_QUALITY_BENCHMARK",
    "reason": (
        "The official model.onnx_data is internally inconsistent with external "
        "tensor offsets referenced by model.onnx, so ONNX Runtime cannot create a session."
    ),
}


def load_room(path: Path, source: str) -> pd.DataFrame:
    data = pd.read_csv(path, dtype={"private_id": str}).fillna("")
    if not data["user_common_actionability"].isin(ACTIONABILITY_LABELS).all():
        raise ValueError(f"{source} 공통 라벨이 완성되지 않았습니다.")
    data["source_holdout"] = source
    data["text"] = [
        normalize_notification_text(package, title, body)
        for package, title, body in zip(
            data["package_name"], data["title"], data["body"]
        )
    ]
    return data


def load_holdouts() -> pd.DataFrame:
    return pd.concat(
        [load_room(ROOM_100_PATH, "room_100"), load_room(ROOM_45_PATH, "room_45")],
        ignore_index=True,
    )


def cache_path(config: dict[str, Any], texts: list[str]) -> Path:
    digest = hashlib.sha256()
    values = (
        config["model_id"],
        str(config["prompt_name"]),
        PREPROCESSING_VERSION,
        str(MAX_LENGTH),
        *texts,
    )
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    if config.get("prefix"):
        digest.update(str(config["prefix"]).encode("utf-8"))
        digest.update(b"\0")
    safe_id = config["model_id"].replace("/", "__").lower()
    return CACHE_DIR / f"{safe_id}_{digest.hexdigest()[:16]}.npz"


def snapshot_bytes(model_id: str) -> int:
    try:
        snapshot = Path(snapshot_download(repo_id=model_id, local_files_only=True))
    except Exception:
        snapshot_root = (
            Path(HF_HUB_CACHE)
            / f"models--{model_id.replace('/', '--')}"
            / "snapshots"
        )
        snapshots = [path for path in snapshot_root.iterdir() if path.is_dir()]
        if not snapshots:
            raise
        snapshot = max(snapshots, key=lambda path: path.stat().st_mtime)
    return sum(path.stat().st_size for path in snapshot.rglob("*") if path.is_file())


def apply_lfm_transformers_compatibility(model: SentenceTransformer) -> int:
    """Ignore the new Transformers seq_idx kwarg in LiquidAI's current patch.

    LiquidAI's bidirectional ShortConv patch predates the optional seq_idx argument
    now forwarded by Transformers. Removing only that unused optional argument makes
    the official model implementation runnable without changing its math.
    """
    patched = 0
    for module in model.modules():
        if type(module).__name__ != "Lfm2ShortConv":
            continue
        original = module.slow_forward

        def compatible(*args: Any, _original: Any = original, **kwargs: Any) -> Any:
            kwargs.pop("seq_idx", None)
            return _original(*args, **kwargs)

        module.slow_forward = compatible
        patched += 1
    return patched


def encode(
    model: SentenceTransformer,
    values: list[str],
    config: dict[str, Any],
    batch_size: int,
    progress: bool,
) -> np.ndarray:
    prepared = [str(config.get("prefix", "")) + value for value in values]
    kwargs: dict[str, Any] = {}
    if config["prompt_name"]:
        kwargs["prompt_name"] = config["prompt_name"]
    return model.encode(
        prepared,
        batch_size=batch_size,
        show_progress_bar=progress,
        convert_to_numpy=True,
        normalize_embeddings=True,
        **kwargs,
    ).astype(np.float32)


def benchmark_calls(
    model: SentenceTransformer, config: dict[str, Any], texts: list[str]
) -> dict[str, float | int]:
    samples = texts[:BENCHMARK_ROWS]
    for text in samples[:5]:
        encode(model, [text], config, batch_size=1, progress=False)
    durations = []
    for text in samples:
        started = time.perf_counter()
        encode(model, [text], config, batch_size=1, progress=False)
        durations.append((time.perf_counter() - started) * 1000)
    return {
        "single_median_ms": float(np.median(durations)),
        "single_p95_ms": float(np.percentile(durations, 95)),
        "single_samples": len(durations),
    }


def get_embeddings(
    config: dict[str, Any], texts: list[str]
) -> tuple[np.ndarray, dict[str, object]]:
    load_started = time.perf_counter()
    model = SentenceTransformer(
        config["model_id"],
        device="cpu",
        local_files_only=True,
        trust_remote_code=config["trust_remote_code"],
    )
    # StaticEmbedding owns a fixed tokenizer and exposes no writable max length.
    if config["key"] != "kor_static_embedding_128":
        model.max_seq_length = MAX_LENGTH
    lfm_compatibility_modules = 0
    if config["key"] == "lfm2_5_embedding_350m":
        lfm_compatibility_modules = apply_lfm_transformers_compatibility(model)
    load_seconds = time.perf_counter() - load_started

    target = cache_path(config, texts)
    if target.exists():
        vectors = np.load(target)["embeddings"]
        batch_seconds = 0.0
        cache_hit = True
    else:
        started = time.perf_counter()
        vectors = encode(
            model,
            texts,
            config,
            batch_size=config["batch_size"],
            progress=True,
        )
        batch_seconds = time.perf_counter() - started
        target.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(target, embeddings=vectors)
        cache_hit = False

    timing = benchmark_calls(model, config, texts[-BENCHMARK_ROWS:])
    metadata: dict[str, object] = {
        "embedding_dimension": int(vectors.shape[1]),
        "parameter_count": int(sum(parameter.numel() for parameter in model.parameters())),
        "source_snapshot_bytes": snapshot_bytes(config["model_id"]),
        "load_seconds": load_seconds,
        "batch_encode_seconds": batch_seconds,
        "batch_cache_hit": cache_hit,
        "lfm_compatibility_modules": lfm_compatibility_modules,
        **timing,
    }
    del model
    gc.collect()
    return vectors, metadata


def evaluate(
    training: pd.DataFrame,
    holdout: pd.DataFrame,
    training_vectors: np.ndarray,
    holdout_vectors: np.ndarray,
    model_key: str,
) -> tuple[dict[str, object], np.ndarray]:
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
    predictions = np.asarray(predicted_actionability(holdout_probability))
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    head_path = MODEL_DIR / f"{model_key}_mlp_32.joblib"
    joblib.dump(final_head, head_path)

    result: dict[str, object] = {
        "cross_validation": model_metrics(
            pd.Series([ACTIONABILITY_LABELS[value] for value in labels]),
            pd.Series(predicted_actionability(oof)),
        ),
        "head_bytes": head_path.stat().st_size,
    }
    for source in ("room_100", "room_45"):
        mask = holdout["source_holdout"].eq(source).to_numpy()
        result[source] = model_metrics(
            holdout.loc[mask, "user_common_actionability"].reset_index(drop=True),
            pd.Series(predictions[mask]),
        )
    result["room_145"] = model_metrics(
        holdout["user_common_actionability"], pd.Series(predictions)
    )
    return result, predictions


def paired_comparisons(
    holdout: pd.DataFrame, predictions: dict[str, np.ndarray], source: str
) -> dict[str, object]:
    mask = (
        np.ones(len(holdout), dtype=bool)
        if source == "room_145"
        else holdout["source_holdout"].eq(source).to_numpy()
    )
    actual = holdout.loc[mask, "user_common_actionability"].to_numpy()
    output: dict[str, object] = {}
    keys = [config["key"] for config in MODELS]
    for left_index, left in enumerate(keys):
        for right in keys[left_index + 1 :]:
            left_values = predictions[left][mask]
            right_values = predictions[right][mask]
            accuracy = paired_accuracy_interval(actual, left_values, right_values)
            important = paired_important_f1_interval(actual, left_values, right_values)
            output[f"{right}_minus_{left}"] = {
                "accuracy": {
                    "right_minus_left": accuracy["v06_minus_v05"],
                    "bootstrap_95_low": accuracy["bootstrap_95_low"],
                    "bootstrap_95_high": accuracy["bootstrap_95_high"],
                },
                "important_f1": {
                    "right_minus_left": important["v06_minus_v05"],
                    "bootstrap_95_low": important["bootstrap_95_low"],
                    "bootstrap_95_high": important["bootstrap_95_high"],
                },
                "mcnemar": mcnemar_exact(actual, left_values, right_values),
            }
    return output


def markdown(results: dict[str, object]) -> str:
    lines = [
        "# 신규 온디바이스 후보 동일조건 비교 v1",
        "",
        "기존 비교에 사용한 모델은 제외하고, 세 신규 encoder를 고정한 뒤 동일한 v0.5 600개, Android v2 전처리, 고정 5-Fold, MLP 32-unit으로 비교했다.",
        "",
        "## 성능",
        "",
        "| 모델 | 합성 CV Acc | 합성 CV Macro F1 | Room 100 Acc | Room 45 Acc | Room 145 Acc | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for config in MODELS:
        value = results["models"][config["key"]]
        cv = value["evaluation"]["cross_validation"]
        room_100 = value["evaluation"]["room_100"]
        room_45 = value["evaluation"]["room_45"]
        room_145 = value["evaluation"]["room_145"]
        binary = room_145["important_binary"]
        lines.append(
            f"| {config['key']} | {cv['three_class_accuracy']:.3f} | "
            f"{cv['three_class_macro_f1']:.3f} | {room_100['three_class_accuracy']:.3f} | "
            f"{room_45['three_class_accuracy']:.3f} | {room_145['three_class_accuracy']:.3f} | "
            f"{binary['precision']:.3f} | {binary['recall']:.3f} | "
            f"{binary['f1']:.3f} | {binary['false_positive']} | "
            f"{binary['false_negative']} |"
        )
    lines.extend(
        [
            "",
            "## 로컬 CPU 참고 측정",
            "",
            "| 모델 | 파라미터 | 원본 스냅샷 MiB | 차원 | 단일 median ms | 단일 p95 ms | Head KiB |",
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
            "## 해석 주의",
            "",
            "- Room 145개 라벨은 모델 예측 전에 이미 확인했으므로, 신규 모델에 대한 최종 블라인드 성능이 아니라 회고적 개발 비교다.",
            "- 로컬 CPU + PyTorch/SentenceTransformers 수치는 Android ONNX Runtime 수치가 아니다.",
            "- Android 채택 전에는 승자 1개를 ONNX로 변환한 뒤 새 Room 알림을 예측 봉인하고 라벨링해야 한다.",
            "- HiEmbed_base_onnx_v1은 공식 external weight 파일과 ONNX tensor offset이 맞지 않아 품질 비교 전에 제외했다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    training = experiment.load_training_data(DATA_PATH)
    holdout = load_holdouts()
    all_texts = list(dict.fromkeys([*training["text"], *holdout["text"]]))
    positions = {text: index for index, text in enumerate(all_texts)}
    training_indices = [positions[text] for text in training["text"]]
    holdout_indices = [positions[text] for text in holdout["text"]]
    results: dict[str, Any] = {
        "protocol": {
            "training_rows": len(training),
            "holdout_rows": len(holdout),
            "holdout_sources": holdout["source_holdout"].value_counts().to_dict(),
            "max_length": MAX_LENGTH,
            "head": "mlp_32",
            "folds": 5,
            "random_seed": 42,
            "preprocessing": PREPROCESSING_VERSION,
            "blind_status": "RETROSPECTIVE_DEVELOPMENT_NOT_PRISTINE_BLIND",
        },
        "rejected_preflight": [REJECTED_PREFLIGHT],
        "models": {},
    }
    private = holdout[
        ["source_holdout", "review_id", "private_id", "user_common_actionability"]
    ].copy()
    predictions_by_model: dict[str, np.ndarray] = {}
    for config in MODELS:
        print(f"\n{config['key']} embedding", flush=True)
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
            "prompt_name": config["prompt_name"],
            "runtime": runtime,
            "evaluation": evaluation,
        }
        predictions_by_model[config["key"]] = predictions
        private[f"{config['key']}_actionability"] = predictions
        del vectors
        gc.collect()

    results["paired_comparisons"] = {
        source: paired_comparisons(holdout, predictions_by_model, source)
        for source in ("room_100", "room_45", "room_145")
    }
    PRIVATE_PREDICTIONS.parent.mkdir(parents=True, exist_ok=True)
    private.to_csv(PRIVATE_PREDICTIONS, index=False, encoding="utf-8-sig")
    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(markdown(results), encoding="utf-8")
    print("\n" + markdown(results))


if __name__ == "__main__":
    main()
