"""Check that quantized LiteRT embeddings preserve the v0.5 Room evaluation."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from ai_edge_litert.interpreter import Interpreter
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer

import compare_frozen_backbones_v05 as benchmark
import experiment_embeddinggemma_actionability_v05 as experiment
from actionability_contract import predicted_actionability
from evaluate_granite_v05_v06_blind_holdout import model_metrics


PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT = PROJECT_DIR / "reports" / "litert_quantized_quality_v1.json"

MODELS = (
    {
        "key": "granite_97m_r2",
        "model_id": "ibm-granite/granite-embedding-97m-multilingual-r2",
        "adapter": "sentence_transformer",
        "prefix": "",
        "tflite": PROJECT_DIR
        / "models/litert_mobile_benchmark/granite_97m_seq64_q8_weight_only.tflite",
    },
    {
        "key": "embeddinggemma_300m",
        "head_key": "embeddinggemma_300m",
        "model_id": "google/embeddinggemma-300m",
        "adapter": "sentence_transformer",
        "prefix": "task: classification | query: ",
        "tflite": PROJECT_DIR
        / "models/litert_mobile_benchmark/embeddinggemma_300m_seq64_q8.tflite",
    },
    {
        "key": "embeddinggemma_300m_int4",
        "head_key": "embeddinggemma_300m",
        "model_id": "google/embeddinggemma-300m",
        "adapter": "sentence_transformer",
        "prefix": "task: classification | query: ",
        "tflite": PROJECT_DIR
        / "models/litert_mobile_benchmark/embeddinggemma_300m_seq64_q4_block32.tflite",
    },
)


def tflite_embeddings(config: dict[str, object], texts: list[str]) -> np.ndarray:
    snapshot = snapshot_download(repo_id=str(config["model_id"]), local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    interpreter = Interpreter(model_path=str(config["tflite"]), num_threads=4)
    interpreter.allocate_tensors()
    inputs = interpreter.get_input_details()
    output = interpreter.get_output_details()[0]
    vectors = []
    for text in texts:
        encoded = tokenizer(
            str(config["prefix"]) + text,
            return_tensors="np",
            padding="max_length",
            truncation=True,
            max_length=benchmark.MAX_LENGTH,
        )
        interpreter.set_tensor(
            inputs[0]["index"], encoded["input_ids"].astype(np.int64)
        )
        interpreter.set_tensor(
            inputs[1]["index"], encoded["attention_mask"].astype(np.int64)
        )
        interpreter.invoke()
        vectors.append(interpreter.get_tensor(output["index"])[0].copy())
    return np.asarray(vectors, dtype=np.float32)


def cosine_rows(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    numerator = np.sum(left * right, axis=1)
    denominator = np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1)
    return numerator / np.maximum(denominator, 1e-12)


def main() -> None:
    training = experiment.load_training_data(benchmark.DATA_PATH)
    holdout = benchmark.load_holdout()
    all_texts = list(dict.fromkeys([*training["text"], *holdout["text"]]))
    positions = {text: index for index, text in enumerate(all_texts)}
    holdout_indices = [positions[text] for text in holdout["text"]]
    full_predictions = pd.read_csv(benchmark.PRIVATE_PREDICTIONS).fillna("")

    report: dict[str, object] = {
        "protocol": {
            "holdout_rows": len(holdout),
            "max_length": benchmark.MAX_LENGTH,
            "head": "same saved MLP 32-unit head as the full-precision benchmark",
            "preprocessing": benchmark.PREPROCESSING_VERSION,
        },
        "models": {},
    }
    for config in MODELS:
        key = str(config["key"])
        head_key = str(config.get("head_key", key))
        print(f"{key}: LiteRT embedding 100 rows")
        quantized = tflite_embeddings(config, holdout["text"].tolist())
        cache = benchmark.cache_path(
            str(config["model_id"]),
            str(config["adapter"]),
            str(config["prefix"]),
            all_texts,
        )
        full_precision = np.load(cache)["embeddings"][holdout_indices]
        cosine = cosine_rows(full_precision, quantized)
        head = joblib.load(
            benchmark.MODEL_DIR / f"{head_key}_mlp_32.joblib"
        )
        predictions = np.asarray(
            predicted_actionability(head.predict_proba(quantized))
        )
        expected = full_predictions[f"{head_key}_actionability"].to_numpy()
        report["models"][key] = {
            "tflite_bytes": Path(config["tflite"]).stat().st_size,
            "embedding_cosine_mean": float(cosine.mean()),
            "embedding_cosine_min": float(cosine.min()),
            "embedding_max_absolute_error": float(
                np.max(np.abs(full_precision - quantized))
            ),
            "prediction_disagreements_vs_full_precision": int(
                np.sum(predictions != expected)
            ),
            "room_holdout": model_metrics(
                holdout["user_common_actionability"], pd.Series(predictions)
            ),
        }

    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
