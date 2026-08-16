"""Export and verify quantized TFLite variants from the final model weights."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")

import numpy as np
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

from actionability_contract import (
    ACTIONABILITY_LABELS,
    ACTIONABILITY_TO_ID,
    important_probabilities,
    model_score_delta,
    softmax,
)
from train_koelectra_tensorflow import (
    LEGACY_TEXT_PREPROCESSING,
    MODEL_NAME,
    TEXT_PREPROCESSING_CHOICES,
    KoElectraModule,
    default_data_path,
    load_data,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = (
    PROJECT_DIR / "models" / "koelectra_actionability_triage_v0.5_final"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument(
        "--data", type=Path, default=default_data_path()
    )
    parser.add_argument(
        "--text-preprocessing",
        choices=TEXT_PREPROCESSING_CHOICES,
        default=LEGACY_TEXT_PREPROCESSING,
        help=(
            "기존 v0.5 가중치는 legacy로 학습됨. android_v2로 새로 학습한 "
            "가중치만 android_v2를 선택합니다."
        ),
    )
    return parser.parse_args()


def convert(module: KoElectraModule, mode: str) -> bytes:
    converter = tf.lite.TFLiteConverter.from_concrete_functions(
        [module.serve.get_concrete_function()], module
    )
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    if mode == "float16":
        converter.target_spec.supported_types = [tf.float16]
    elif mode != "dynamic":
        raise ValueError(f"지원하지 않는 변환 모드: {mode}")
    return converter.convert()


def make_inputs(tokenizer, texts: list[str]) -> list[dict[str, np.ndarray]]:
    result = []
    for text in texts:
        encoded = tokenizer(
            text,
            max_length=64,
            padding="max_length",
            truncation=True,
            return_tensors="np",
        )
        input_ids = encoded["input_ids"].astype(np.int32)
        result.append(
            {
                "input_ids": input_ids,
                "attention_mask": encoded["attention_mask"].astype(np.int32),
                "token_type_ids": encoded.get(
                    "token_type_ids", np.zeros_like(input_ids)
                ).astype(np.int32),
            }
        )
    return result


def run_tflite(
    model: bytes, inputs: list[dict[str, np.ndarray]]
) -> np.ndarray:
    interpreter = tf.lite.Interpreter(model_content=model, num_threads=2)
    runner = interpreter.get_signature_runner("serving_default")
    return np.concatenate(
        [np.asarray(runner(**item)["logits"]) for item in inputs], axis=0
    )


def fidelity(reference_logits: np.ndarray, candidate_logits: np.ndarray) -> dict:
    reference_probability = softmax(reference_logits)
    candidate_probability = softmax(candidate_logits)
    reference_important = important_probabilities(reference_probability)
    candidate_important = important_probabilities(candidate_probability)
    reference_scores = np.asarray(
        [model_score_delta(value) for value in reference_important]
    )
    candidate_scores = np.asarray(
        [model_score_delta(value) for value in candidate_important]
    )
    logit_difference = np.abs(reference_logits - candidate_logits)
    probability_difference = np.abs(reference_important - candidate_important)
    return {
        "max_absolute_logit_difference": float(logit_difference.max()),
        "mean_absolute_logit_difference": float(logit_difference.mean()),
        "max_important_probability_difference": float(
            probability_difference.max()
        ),
        "mean_important_probability_difference": float(
            probability_difference.mean()
        ),
        "class_prediction_agreement": float(
            np.mean(
                np.argmax(reference_probability, axis=1)
                == np.argmax(candidate_probability, axis=1)
            )
        ),
        "model_score_delta_agreement": float(
            np.mean(reference_scores == candidate_scores)
        ),
        "model_score_delta_changed_rows": int(
            np.sum(reference_scores != candidate_scores)
        ),
    }


def main() -> None:
    args = parse_args()
    weights_path = args.model_dir / "classifier.weights.h5"
    tokenizer = AutoTokenizer.from_pretrained(
        args.model_dir / "tokenizer", use_fast=True, local_files_only=True
    )
    classifier = TFAutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        from_pt=True,
        num_labels=len(ACTIONABILITY_LABELS),
        id2label={index: label for index, label in enumerate(ACTIONABILITY_LABELS)},
        label2id=ACTIONABILITY_TO_ID,
        local_files_only=True,
    )
    classifier.load_weights(str(weights_path))
    module = KoElectraModule(classifier)
    data = load_data(args.data, args.text_preprocessing)
    inputs = make_inputs(tokenizer, data["text"].astype(str).tolist())
    fp32_path = args.model_dir / "noti_koelectra_actionability_v0.5_final_fp32.tflite"
    reference = run_tflite(fp32_path.read_bytes(), inputs)

    results: dict[str, object] = {}
    for mode, suffix in (
        ("float16", "fp16"),
        ("dynamic", "dynamic_range"),
    ):
        model = convert(module, mode)
        path = args.model_dir / (
            f"noti_koelectra_actionability_v0.5_final_{suffix}.tflite"
        )
        path.write_bytes(model)
        logits = run_tflite(model, inputs)
        results[mode] = {
            "path": str(path),
            "size_bytes": len(model),
            "validation_rows": len(inputs),
            **fidelity(reference, logits),
        }

    results["text_preprocessing"] = args.text_preprocessing
    report_path = args.model_dir / "quantization_report.json"
    report_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
