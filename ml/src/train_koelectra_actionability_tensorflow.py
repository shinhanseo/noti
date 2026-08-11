"""Train a three-tier KoELECTRA actionability fold and optionally export TFLite."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")

import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

from actionability_contract import (
    ACTIONABILITY_LABELS,
    ACTIONABILITY_TO_ID,
    MODEL_CONTRACT_VERSION,
    encode_actionability,
    important_probabilities,
    model_score_delta,
    predicted_actionability,
    probability_columns,
)
from train_koelectra_tensorflow import (
    MODEL_NAME,
    KoElectraModule,
    choose_recall_threshold,
    compile_classifier,
    default_data_path,
    default_project_dir,
    evaluate,
    load_data,
    serializable_history,
    tokenize,
)


NUM_LABELS = len(ACTIONABILITY_LABELS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=default_data_path())
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_project_dir()
        / "models"
        / "koelectra_actionability_triage_v0.5_fold0",
    )
    parser.add_argument("--dataset-version", default="0.5")
    parser.add_argument("--fold-index", type=int, default=0)
    parser.add_argument("--skip-artifacts", action="store_true")
    parser.add_argument("--print-validation-rows", action="store_true")
    parser.add_argument("--disable-class-weights", action="store_true")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--head-epochs", type=int, default=3)
    parser.add_argument("--finetune-epochs", type=int, default=12)
    parser.add_argument("--head-learning-rate", type=float, default=3e-4)
    parser.add_argument("--finetune-learning-rate", type=float, default=2e-5)
    parser.add_argument("--unfreeze-top-layers", type=int, default=4)
    args, _ = parser.parse_known_args()
    return args


def multiclass_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, object]:
    class_ids = list(range(NUM_LABELS))
    precision, recall, f1, support = precision_recall_fscore_support(
        actual,
        predicted,
        labels=class_ids,
        zero_division=0,
    )
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        actual,
        predicted,
        labels=class_ids,
        average="macro",
        zero_division=0,
    )
    weighted_f1 = precision_recall_fscore_support(
        actual,
        predicted,
        labels=class_ids,
        average="weighted",
        zero_division=0,
    )[2]
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_precision": float(macro_precision),
        "macro_recall": float(macro_recall),
        "macro_f1": float(macro_f1),
        "weighted_f1": float(weighted_f1),
        "confusion_matrix": confusion_matrix(
            actual, predicted, labels=class_ids
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


def main() -> None:
    args = parse_args()
    if args.fold_index not in range(5):
        raise ValueError("--fold-index는 0부터 4 사이여야 합니다.")
    np.random.seed(42)
    tf.random.set_seed(42)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data = load_data(args.data)
    if "actionability" not in data.columns:
        raise ValueError("데이터에 actionability 열이 없습니다.")
    if "cv_fold" not in data.columns or data["cv_fold"].isna().any():
        raise ValueError("v0.5 고정 cv_fold가 필요합니다.")
    data["actionability_id"] = encode_actionability(
        data["actionability"].astype(str).tolist()
    )
    validation_mask = data["cv_fold"].astype(int).eq(args.fold_index)
    train_data = data[~validation_mask].copy()
    validation_data = data[validation_mask].copy()
    group_overlap = len(
        set(train_data["template_group"])
        & set(validation_data["template_group"])
    )
    if group_overlap:
        raise RuntimeError("학습·검증 template_group이 겹칩니다.")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    train_inputs = tokenize(tokenizer, train_data["text"].tolist())
    validation_inputs = tokenize(tokenizer, validation_data["text"].tolist())
    train_labels = train_data["actionability_id"].to_numpy(dtype=np.int32)
    validation_labels = validation_data["actionability_id"].to_numpy(
        dtype=np.int32
    )
    class_counts = np.bincount(train_labels, minlength=NUM_LABELS)
    class_weights = {
        class_id: float(len(train_labels) / (NUM_LABELS * count))
        for class_id, count in enumerate(class_counts)
    }
    fit_class_weights = None if args.disable_class_weights else class_weights

    classifier = TFAutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        from_pt=True,
        num_labels=NUM_LABELS,
        id2label={index: label for index, label in enumerate(ACTIONABILITY_LABELS)},
        label2id=ACTIONABILITY_TO_ID,
    )
    classifier.electra.trainable = False
    compile_classifier(classifier, args.head_learning_rate)
    head_history = classifier.fit(
        train_inputs,
        train_labels,
        validation_data=(validation_inputs, validation_labels),
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
        train_inputs,
        train_labels,
        validation_data=(validation_inputs, validation_labels),
        epochs=args.finetune_epochs,
        batch_size=args.batch_size,
        class_weight=fit_class_weights,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=2,
                restore_best_weights=True,
            )
        ],
        verbose=2,
    )

    validation_logits = classifier.predict(
        validation_inputs,
        batch_size=args.batch_size,
        verbose=0,
    ).logits
    probabilities = tf.nn.softmax(validation_logits, axis=-1).numpy()
    actionability_predictions = np.argmax(probabilities, axis=-1).astype(np.int32)
    important_probability = important_probabilities(probabilities)
    binary_actual = validation_data["label"].to_numpy(dtype=np.int32)
    threshold = choose_recall_threshold(binary_actual, important_probability)
    binary_predictions = (important_probability >= threshold).astype(np.int32)

    tflite_size_bytes: int | None = None
    conversion_max_abs_diff: float | None = None
    if not args.skip_artifacts:
        module = KoElectraModule(classifier)
        converter = tf.lite.TFLiteConverter.from_concrete_functions(
            [module.serve.get_concrete_function()], module
        )
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
        tflite_model = converter.convert()
        tflite_path = args.output_dir / (
            f"noti_koelectra_actionability_v{args.dataset_version}_fp32.tflite"
        )
        tflite_path.write_bytes(tflite_model)
        sample_inputs = {name: values[:1] for name, values in validation_inputs.items()}
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
        tflite_size_bytes = len(tflite_model)
        classifier.save_weights(str(args.output_dir / "classifier.weights.h5"))
        tokenizer.save_pretrained(args.output_dir / "tokenizer")

    output_columns = [
        "id",
        "app_name",
        "title",
        "body",
        "label",
        "template_group",
        "actionability",
        "event_type",
        "preference_sensitive",
    ]
    validation_rows = validation_data[output_columns].copy()
    validation_rows["actual_actionability_id"] = validation_labels
    validation_rows["predicted_actionability"] = predicted_actionability(
        probabilities
    )
    validation_rows["predicted_actionability_id"] = actionability_predictions
    for column, values in probability_columns(probabilities).items():
        validation_rows[column] = values
    validation_rows["important_probability"] = important_probability
    validation_rows["model_score_delta"] = [
        model_score_delta(value) for value in important_probability
    ]
    validation_rows["binary_prediction"] = binary_predictions
    actionability_errors = validation_rows[
        validation_rows["actual_actionability_id"]
        != validation_rows["predicted_actionability_id"]
    ]

    report = {
        "status": "actionability_triage_training_complete",
        "model": MODEL_NAME,
        "model_contract_version": MODEL_CONTRACT_VERSION,
        "dataset_version": args.dataset_version,
        "dataset": str(args.data),
        "label_order": list(ACTIONABILITY_LABELS),
        "fold_index": args.fold_index,
        "split_strategy": "preassigned_actionability_balanced_group_fold",
        "unfrozen_top_encoder_layers": args.unfreeze_top_layers,
        "class_weight_strategy": (
            "none" if args.disable_class_weights else "balanced_inverse_frequency"
        ),
        "class_weights": {
            ACTIONABILITY_LABELS[class_id]: weight
            for class_id, weight in class_weights.items()
        },
        "train_size": len(train_data),
        "validation_size": len(validation_data),
        "train_actionability_counts": {
            str(key): int(value)
            for key, value in train_data["actionability"].value_counts().items()
        },
        "validation_actionability_counts": {
            str(key): int(value)
            for key, value in validation_data["actionability"].value_counts().items()
        },
        "template_group_overlap": group_overlap,
        "epochs_completed": {
            "head": len(head_history.history["loss"]),
            "finetune": len(finetune_history.history["loss"]),
        },
        "history": {
            "head": serializable_history(head_history),
            "finetune": serializable_history(finetune_history),
        },
        "actionability_metrics": multiclass_metrics(
            validation_labels, actionability_predictions
        ),
        "binary_metrics_at_0.5": evaluate(
            binary_actual, important_probability, 0.5
        ),
        "binary_metrics_at_recall_threshold": evaluate(
            binary_actual, important_probability, threshold
        ),
        "tflite_size_bytes": tflite_size_bytes,
        "conversion_max_absolute_logit_difference": conversion_max_abs_diff,
        "validation_rows": validation_rows.to_dict(orient="records"),
        "actionability_errors": actionability_errors.to_dict(orient="records"),
    }
    (args.output_dir / "training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    console_report = dict(report)
    if not args.print_validation_rows:
        console_report.pop("validation_rows")
        console_report.pop("actionability_errors")
    print(json.dumps(console_report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
