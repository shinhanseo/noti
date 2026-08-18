"""Validate the shortlisted ARM64 INT8 ONNX encoders with the fixed noti protocol."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
import pandas as pd
from transformers import AutoTokenizer

import compare_compact_mobile_backbones_v2 as shortlist
import compare_new_ondevice_backbones_v1 as benchmark


PROJECT_DIR = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    PROJECT_DIR / "models" / "compact_mobile_backbone_benchmark_v2" / "onnx_artifacts"
)
JSON_OUTPUT = PROJECT_DIR / "reports" / "compact_mobile_onnx_validation_v2.json"
MARKDOWN_OUTPUT = PROJECT_DIR / "reports" / "compact_mobile_onnx_validation_v2.md"
PRIVATE_OUTPUT = (
    PROJECT_DIR / "data" / "private" / "compact_mobile_onnx_validation_v2_predictions.csv"
)

MODELS: tuple[dict[str, Any], ...] = (
    {
        **shortlist.MODELS[1],
        "key": "bekko_embedding_v1_a25m_arm64_int8",
        "onnx_path": ARTIFACT_DIR / "bekko_a25m" / "model_qint8_arm64.onnx",
    },
    {
        **shortlist.MODELS[2],
        "key": "koen_e5_tiny_arm64_int8",
        "onnx_path": ARTIFACT_DIR / "koen_e5_tiny" / "model_qint8_arm64.onnx",
    },
)


def encode_onnx(
    session: ort.InferenceSession,
    tokenizer: Any,
    values: list[str],
    prefix: str,
    batch_size: int,
) -> np.ndarray:
    input_names = {value.name for value in session.get_inputs()}
    batches: list[np.ndarray] = []
    for offset in range(0, len(values), batch_size):
        texts = [prefix + value for value in values[offset : offset + batch_size]]
        tokens = tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=benchmark.MAX_LENGTH,
            return_tensors="np",
        )
        feeds = {
            name: np.asarray(tokens[name], dtype=np.int64)
            for name in input_names
            if name in tokens
        }
        if "token_type_ids" in input_names and "token_type_ids" not in feeds:
            feeds["token_type_ids"] = np.zeros_like(feeds["input_ids"])
        hidden = session.run(None, feeds)[0]
        mask = np.asarray(tokens["attention_mask"], dtype=np.float32)[..., None]
        pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1e-9)
        pooled /= np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
        batches.append(pooled.astype(np.float32))
    return np.concatenate(batches)


def single_latency(
    session: ort.InferenceSession, tokenizer: Any, texts: list[str], prefix: str
) -> dict[str, float]:
    for text in texts[:5]:
        encode_onnx(session, tokenizer, [text], prefix, 1)
    values = []
    for text in texts[:30]:
        started = time.perf_counter()
        encode_onnx(session, tokenizer, [text], prefix, 1)
        values.append((time.perf_counter() - started) * 1000)
    return {
        "single_median_ms": float(np.median(values)),
        "single_p95_ms": float(np.percentile(values, 95)),
    }


def markdown(results: dict[str, Any]) -> str:
    lines = [
        "# Compact mobile ARM64 INT8 ONNX 검증 v2",
        "",
        "원본 PyTorch 후보 평가와 동일한 데이터·전처리·5-Fold·MLP head를 실제 양자화 ONNX 출력으로 다시 평가했다.",
        "",
        "| 모델 | Room 145 Acc | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN | 원본과 평균 cosine | ONNX MiB | 단일 median ms* |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for config in MODELS:
        value = results["models"][config["key"]]
        room = value["evaluation"]["room_145"]
        binary = room["important_binary"]
        lines.append(
            f"| {config['key']} | {room['three_class_accuracy']:.3f} | "
            f"{binary['precision']:.3f} | {binary['recall']:.3f} | "
            f"{binary['f1']:.3f} | {binary['false_positive']} | "
            f"{binary['false_negative']} | {value['source_cosine_mean']:.6f} | "
            f"{value['onnx_bytes'] / 1024**2:.1f} | "
            f"{value['runtime']['single_median_ms']:.2f} |"
        )
    lines.extend(
        [
            "",
            "\\* Apple Silicon Mac의 Python ONNX Runtime 참고값이며 Android 실기기 수치가 아니다.",
            "토크나이저와 Android 런타임 라이브러리 용량은 ONNX MiB 열에 포함하지 않았다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    benchmark.CACHE_DIR = shortlist.CACHE_DIR
    benchmark.MODEL_DIR = PROJECT_DIR / "models" / "compact_mobile_onnx_validation_v2"
    training = benchmark.experiment.load_training_data(benchmark.DATA_PATH)
    holdout = benchmark.load_holdouts()
    all_texts = list(dict.fromkeys([*training["text"], *holdout["text"]]))
    positions = {text: index for index, text in enumerate(all_texts)}
    training_indices = [positions[text] for text in training["text"]]
    holdout_indices = [positions[text] for text in holdout["text"]]
    results: dict[str, Any] = {"models": {}}
    private = holdout[
        ["source_holdout", "review_id", "private_id", "user_common_actionability"]
    ].copy()

    for config in MODELS:
        print(f"\n{config['key']}", flush=True)
        session = ort.InferenceSession(
            str(config["onnx_path"]), providers=["CPUExecutionProvider"]
        )
        tokenizer = AutoTokenizer.from_pretrained(
            config["model_id"], local_files_only=True
        )
        started = time.perf_counter()
        vectors = encode_onnx(
            session,
            tokenizer,
            all_texts,
            str(config.get("prefix", "")),
            int(config["batch_size"]),
        )
        batch_seconds = time.perf_counter() - started
        source_config = next(
            value for value in shortlist.MODELS if value["model_id"] == config["model_id"]
        )
        source_vectors = np.load(benchmark.cache_path(source_config, all_texts))[
            "embeddings"
        ]
        cosine = np.sum(source_vectors * vectors, axis=1)
        evaluation, predictions = benchmark.evaluate(
            training,
            holdout,
            vectors[training_indices],
            vectors[holdout_indices],
            config["key"],
        )
        results["models"][config["key"]] = {
            "model_id": config["model_id"],
            "onnx_path": str(config["onnx_path"].relative_to(PROJECT_DIR)),
            "onnx_bytes": config["onnx_path"].stat().st_size,
            "source_cosine_mean": float(cosine.mean()),
            "source_cosine_min": float(cosine.min()),
            "runtime": {
                "batch_encode_seconds": batch_seconds,
                **single_latency(
                    session,
                    tokenizer,
                    all_texts[-30:],
                    str(config.get("prefix", "")),
                ),
            },
            "evaluation": evaluation,
        }
        private[f"{config['key']}_actionability"] = predictions

    PRIVATE_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    private.to_csv(PRIVATE_OUTPUT, index=False, encoding="utf-8-sig")
    JSON_OUTPUT.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(markdown(results), encoding="utf-8")
    print("\n" + markdown(results))


if __name__ == "__main__":
    main()
