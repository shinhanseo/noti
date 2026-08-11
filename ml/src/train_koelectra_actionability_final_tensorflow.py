"""Train the final three-tier actionability model and export a TFLite artifact."""

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
    MODEL_CONTRACT_VERSION,
    encode_actionability,
)
from train_koelectra_tensorflow import (
    MODEL_NAME,
    KoElectraModule,
    compile_classifier,
    default_data_path,
    default_project_dir,
    load_data,
    serializable_history,
    tokenize,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=default_data_path())
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_project_dir()
        / "models"
        / "koelectra_actionability_triage_v0.5_final",
    )
    parser.add_argument("--dataset-version", default="0.5")
    parser.add_argument("--decision-threshold", type=float, required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--head-epochs", type=int, default=3)
    parser.add_argument("--finetune-epochs", type=int, default=12)
    parser.add_argument("--head-learning-rate", type=float, default=3e-4)
    parser.add_argument("--finetune-learning-rate", type=float, default=2e-5)
    parser.add_argument("--unfreeze-top-layers", type=int, default=4)
    parser.add_argument("--disable-class-weights", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 0.0 <= args.decision_threshold <= 1.0:
        raise ValueError("--decision-threshold는 0부터 1 사이여야 합니다.")
    np.random.seed(42)
    tf.random.set_seed(42)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data = load_data(args.data)
    labels = encode_actionability(data["actionability"].astype(str).tolist())
    class_counts = np.bincount(labels, minlength=len(ACTIONABILITY_LABELS))
    class_weights = {
        class_id: float(len(labels) / (len(ACTIONABILITY_LABELS) * count))
        for class_id, count in enumerate(class_counts)
    }
    fit_class_weights = None if args.disable_class_weights else class_weights
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    inputs = tokenize(tokenizer, data["text"].tolist())
    classifier = TFAutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        from_pt=True,
        num_labels=len(ACTIONABILITY_LABELS),
        id2label={index: label for index, label in enumerate(ACTIONABILITY_LABELS)},
        label2id=ACTIONABILITY_TO_ID,
    )

    classifier.electra.trainable = False
    compile_classifier(classifier, args.head_learning_rate)
    head_history = classifier.fit(
        inputs,
        labels,
        epochs=args.head_epochs,
        batch_size=args.batch_size,
        class_weight=fit_class_weights,
        verbose=2,
    )

    encoder_layers = classifier.electra.encoder.layer
    if not 0 <= args.unfreeze_top_layers <= len(encoder_layers):
        raise ValueError("--unfreeze-top-layers 범위가 올바르지 않습니다.")
    classifier.electra.trainable = True
    classifier.electra.embeddings.trainable = False
    classifier.electra.embeddings_project.trainable = False
    for layer in encoder_layers:
        layer.trainable = False
    if args.unfreeze_top_layers:
        for layer in encoder_layers[-args.unfreeze_top_layers :]:
            layer.trainable = True

    compile_classifier(classifier, args.finetune_learning_rate)
    finetune_history = classifier.fit(
        inputs,
        labels,
        epochs=args.finetune_epochs,
        batch_size=args.batch_size,
        class_weight=fit_class_weights,
        verbose=2,
    )

    module = KoElectraModule(classifier)
    converter = tf.lite.TFLiteConverter.from_concrete_functions(
        [module.serve.get_concrete_function()], module
    )
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    tflite_model = converter.convert()
    tflite_path = args.output_dir / (
        f"noti_koelectra_actionability_v{args.dataset_version}_final_fp32.tflite"
    )
    tflite_path.write_bytes(tflite_model)

    sample_inputs = {name: values[:1] for name, values in inputs.items()}
    tensorflow_logits = module.serve(
        **{
            name: tf.convert_to_tensor(value)
            for name, value in sample_inputs.items()
        }
    )["logits"].numpy()
    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    tflite_logits = np.asarray(
        interpreter.get_signature_runner("serving_default")(**sample_inputs)[
            "logits"
        ]
    )
    conversion_max_abs_diff = float(
        np.max(np.abs(tensorflow_logits - tflite_logits))
    )

    classifier.save_weights(str(args.output_dir / "classifier.weights.h5"))
    tokenizer.save_pretrained(args.output_dir / "tokenizer")
    model_contract = {
        "model_contract_version": MODEL_CONTRACT_VERSION,
        "label_order": list(ACTIONABILITY_LABELS),
        "important_probability": (
            "P(ATTENTION_WORTHY) + P(ACTION_REQUIRED)"
        ),
        "model_score_policy": [
            {"minimum_probability": 0.80, "score_delta": 15},
            {"minimum_probability": 0.65, "score_delta": 10},
            {"minimum_probability": 0.35, "score_delta": 0},
            {"minimum_probability": 0.20, "score_delta": -10},
            {"minimum_probability": 0.00, "score_delta": -15},
        ],
        "cross_validation_decision_threshold": args.decision_threshold,
        "sequence_length": 64,
        "input_names": ["input_ids", "attention_mask", "token_type_ids"],
        "output_name": "logits",
    }
    (args.output_dir / "model_contract.json").write_text(
        json.dumps(model_contract, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    report = {
        "status": "final_actionability_triage_training_and_conversion_complete",
        "model": MODEL_NAME,
        "model_contract_version": MODEL_CONTRACT_VERSION,
        "dataset_version": args.dataset_version,
        "dataset": str(args.data),
        "label_order": list(ACTIONABILITY_LABELS),
        "training_rows": len(data),
        "training_actionability_counts": {
            str(key): int(value)
            for key, value in data["actionability"].value_counts().items()
        },
        "training_strategy": "all_rows_after_fixed_5_fold_cross_validation",
        "unfrozen_top_encoder_layers": args.unfreeze_top_layers,
        "class_weight_strategy": (
            "none" if args.disable_class_weights else "balanced_inverse_frequency"
        ),
        "class_weights": {
            ACTIONABILITY_LABELS[class_id]: weight
            for class_id, weight in class_weights.items()
        },
        "epochs_completed": {
            "head": len(head_history.history["loss"]),
            "finetune": len(finetune_history.history["loss"]),
        },
        "history": {
            "head": serializable_history(head_history),
            "finetune": serializable_history(finetune_history),
        },
        "binary_decision_threshold": {
            "threshold": args.decision_threshold,
            "source": "pooled_three_tier_out_of_fold_predictions",
        },
        "tflite_size_bytes": len(tflite_model),
        "conversion_max_absolute_logit_difference": conversion_max_abs_diff,
    }
    (args.output_dir / "training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
