"""Train the first KoELECTRA notification classifier and export TFLite."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

from notification_text_preprocessor import (
    PREPROCESSING_VERSION,
    normalize_notification_text,
)


MODEL_NAME = "monologg/koelectra-small-v3-discriminator"
SEQ_LEN = 64
LEGACY_TEXT_PREPROCESSING = "legacy"
ANDROID_V2_TEXT_PREPROCESSING = "android_v2"
TEXT_PREPROCESSING_CHOICES = (
    LEGACY_TEXT_PREPROCESSING,
    ANDROID_V2_TEXT_PREPROCESSING,
)


def default_project_dir() -> Path:
    script_path = globals().get("__file__")
    if script_path:
        return Path(script_path).resolve().parents[1]
    return Path.cwd()


def default_data_path() -> Path:
    script_path = globals().get("__file__")
    if script_path:
        return (
            default_project_dir()
            / "data"
            / "public"
            / "train_notifications_v0.5.csv"
        )
    return Path.cwd() / "train_notifications_v0.5.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=default_data_path(),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_project_dir()
        / "models"
        / "koelectra_tensorflow_v0.5_top2",
    )
    parser.add_argument("--dataset-version", default="0.5")
    parser.add_argument("--fold-index", type=int, default=0)
    parser.add_argument("--skip-artifacts", action="store_true")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--head-epochs", type=int, default=3)
    parser.add_argument("--finetune-epochs", type=int, default=6)
    parser.add_argument("--head-learning-rate", type=float, default=3e-4)
    parser.add_argument("--finetune-learning-rate", type=float, default=2e-5)
    parser.add_argument("--unfreeze-top-layers", type=int, default=2)
    args, _ = parser.parse_known_args()
    return args


def text_preprocessing_version(mode: str) -> str:
    if mode == LEGACY_TEXT_PREPROCESSING:
        return "legacy-title-body-v1"
    if mode == ANDROID_V2_TEXT_PREPROCESSING:
        return PREPROCESSING_VERSION
    raise ValueError(f"지원하지 않는 텍스트 전처리입니다: {mode}")


def load_data(
    path: Path,
    text_preprocessing: str = LEGACY_TEXT_PREPROCESSING,
) -> pd.DataFrame:
    data = pd.read_csv(path)
    eligible = data["model_eligible"].astype(str).str.lower().eq("true")
    if "training_eligible" in data.columns:
        eligible &= data["training_eligible"].astype(str).str.lower().eq("true")
    filtered = data[eligible & data["clarity"].eq("CLEAR")].copy()
    if text_preprocessing == LEGACY_TEXT_PREPROCESSING:
        filtered["text"] = (
            filtered["title"].fillna("").str.strip()
            + " "
            + filtered["body"].fillna("").str.strip()
        ).str.strip()
    elif text_preprocessing == ANDROID_V2_TEXT_PREPROCESSING:
        filtered["text"] = [
            normalize_notification_text(package_name, title, body)
            for package_name, title, body in zip(
                filtered["package_name"].fillna(""),
                filtered["title"],
                filtered["body"],
            )
        ]
    else:
        text_preprocessing_version(text_preprocessing)
    return filtered.reset_index(drop=True)


def tokenize(
    tokenizer: object,
    texts: list[str],
) -> dict[str, np.ndarray]:
    encoded = tokenizer(
        texts,
        max_length=SEQ_LEN,
        padding="max_length",
        truncation=True,
        return_tensors="np",
    )
    input_ids = encoded["input_ids"].astype(np.int32)
    return {
        "input_ids": input_ids,
        "attention_mask": encoded["attention_mask"].astype(np.int32),
        "token_type_ids": encoded.get(
            "token_type_ids",
            np.zeros_like(input_ids),
        ).astype(np.int32),
    }


class KoElectraModule(tf.Module):
    def __init__(self, classifier: tf.keras.Model) -> None:
        super().__init__()
        self.classifier = classifier

    @tf.function(
        input_signature=[
            tf.TensorSpec([1, SEQ_LEN], tf.int32, name="input_ids"),
            tf.TensorSpec([1, SEQ_LEN], tf.int32, name="attention_mask"),
            tf.TensorSpec([1, SEQ_LEN], tf.int32, name="token_type_ids"),
        ]
    )
    def serve(
        self,
        input_ids: tf.Tensor,
        attention_mask: tf.Tensor,
        token_type_ids: tf.Tensor,
    ) -> dict[str, tf.Tensor]:
        logits = self.classifier(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            training=False,
        ).logits
        return {"logits": logits}


def choose_recall_threshold(
    labels: np.ndarray,
    probabilities: np.ndarray,
    minimum_recall: float = 0.9,
) -> float:
    precisions, recalls, thresholds = precision_recall_curve(
        labels,
        probabilities,
    )
    candidates: list[tuple[float, float, float]] = []
    for precision, recall, threshold in zip(
        precisions[:-1],
        recalls[:-1],
        thresholds,
    ):
        if recall >= minimum_recall:
            candidates.append((float(precision), float(recall), float(threshold)))
    if not candidates:
        return 0.5
    return max(candidates, key=lambda row: (row[0], row[2]))[2]


def evaluate(
    labels: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> dict[str, object]:
    predictions = (probabilities >= threshold).astype(np.int32)
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    return {
        "threshold": threshold,
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
        "false_positive": int(matrix[0, 1]),
        "false_negative": int(matrix[1, 0]),
    }


def compile_classifier(
    classifier: tf.keras.Model,
    learning_rate: float,
) -> None:
    classifier.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")],
    )


def serializable_history(history: tf.keras.callbacks.History) -> dict[str, list[float]]:
    return {
        key: [float(value) for value in values]
        for key, values in history.history.items()
    }


def probability_summary_by_column(
    data: pd.DataFrame,
    probabilities: np.ndarray,
    predictions: np.ndarray,
    column: str,
) -> dict[str, dict[str, float | int]]:
    if column not in data.columns:
        return {}
    summary_data = data[[column, "label"]].copy()
    summary_data["probability"] = probabilities
    summary_data["prediction"] = predictions
    result: dict[str, dict[str, float | int]] = {}
    for value, group in summary_data.groupby(column, dropna=False):
        result[str(value)] = {
            "rows": int(len(group)),
            "positive_labels": int(group["label"].sum()),
            "predicted_positive": int(group["prediction"].sum()),
            "mean_probability": float(group["probability"].mean()),
            "accuracy": float((group["label"] == group["prediction"]).mean()),
        }
    return result


def main() -> None:
    args = parse_args()
    np.random.seed(42)
    tf.random.set_seed(42)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data = load_data(args.data)
    labels = data["label"].to_numpy(dtype=np.int32)
    groups = data["template_group"].astype(str).to_numpy()
    if "cv_fold" in data.columns and data["cv_fold"].notna().all():
        if args.fold_index not in {0, 1, 2, 3, 4}:
            raise ValueError("--fold-index는 0부터 4 사이여야 합니다.")
        validation_mask = data["cv_fold"].astype(int).eq(args.fold_index)
        train_data = data[~validation_mask]
        validation_data = data[validation_mask]
        split_strategy = "preassigned_actionability_balanced_group_fold"
    else:
        splitter = StratifiedGroupKFold(
            n_splits=5,
            shuffle=True,
            random_state=42,
        )
        splits = list(splitter.split(data, y=labels, groups=groups))
        train_index, validation_index = splits[args.fold_index]
        train_data = data.iloc[train_index]
        validation_data = data.iloc[validation_index]
        split_strategy = "sklearn_stratified_group_kfold"
    group_overlap = len(
        set(train_data["template_group"])
        & set(validation_data["template_group"])
    )
    if group_overlap:
        raise RuntimeError("학습·검증 template_group이 겹칩니다.")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    train_inputs = tokenize(tokenizer, train_data["text"].tolist())
    validation_inputs = tokenize(
        tokenizer,
        validation_data["text"].tolist(),
    )
    train_labels = train_data["label"].to_numpy(dtype=np.int32)
    validation_labels = validation_data["label"].to_numpy(dtype=np.int32)

    classifier = TFAutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        from_pt=True,
        num_labels=2,
    )
    classifier.electra.trainable = False
    compile_classifier(classifier, args.head_learning_rate)
    head_history = classifier.fit(
        train_inputs,
        train_labels,
        validation_data=(validation_inputs, validation_labels),
        epochs=args.head_epochs,
        batch_size=args.batch_size,
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
    validation_probabilities = tf.nn.softmax(
        validation_logits,
        axis=-1,
    ).numpy()[:, 1]
    recall_threshold = choose_recall_threshold(
        validation_labels,
        validation_probabilities,
    )
    validation_predictions = (
        validation_probabilities >= recall_threshold
    ).astype(np.int32)

    tflite_size_bytes: int | None = None
    conversion_max_abs_diff: float | None = None
    if not args.skip_artifacts:
        module = KoElectraModule(classifier)
        concrete_function = module.serve.get_concrete_function()
        converter = tf.lite.TFLiteConverter.from_concrete_functions(
            [concrete_function],
            module,
        )
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
        tflite_model = converter.convert()
        tflite_path = args.output_dir / (
            f"noti_koelectra_v{args.dataset_version}_top"
            f"{args.unfreeze_top_layers}_fp32.tflite"
        )
        tflite_path.write_bytes(tflite_model)

        sample_inputs = {
            name: values[:1]
            for name, values in validation_inputs.items()
        }
        tensorflow_logits = module.serve(
            **{
                name: tf.convert_to_tensor(value)
                for name, value in sample_inputs.items()
            }
        )["logits"].numpy()
        interpreter = tf.lite.Interpreter(model_content=tflite_model)
        signature = interpreter.get_signature_runner("serving_default")
        tflite_logits = np.asarray(signature(**sample_inputs)["logits"])
        conversion_max_abs_diff = float(
            np.max(np.abs(tensorflow_logits - tflite_logits))
        )
        tflite_size_bytes = len(tflite_model)
        classifier.save_weights(str(args.output_dir / "classifier.weights.h5"))
        tokenizer.save_pretrained(args.output_dir / "tokenizer")
    error_columns = [
        "id",
        "app_name",
        "title",
        "body",
        "label",
        "template_group",
    ]
    error_columns.extend(
        column
        for column in ("actionability", "event_type", "preference_sensitive")
        if column in validation_data.columns
    )
    errors = validation_data[error_columns].copy()
    errors["important_probability"] = validation_probabilities
    errors["prediction"] = validation_predictions
    errors = errors[errors["label"] != errors["prediction"]]
    validation_rows = validation_data[error_columns].copy()
    validation_rows["important_probability"] = validation_probabilities
    validation_rows["prediction"] = validation_predictions

    report = {
        "status": "training_and_conversion_complete",
        "model": MODEL_NAME,
        "dataset_version": args.dataset_version,
        "dataset": str(args.data),
        "sequence_length": SEQ_LEN,
        "training_strategy": "head_warmup_then_partial_unfreeze",
        "split_strategy": split_strategy,
        "fold_index": args.fold_index,
        "unfrozen_top_encoder_layers": args.unfreeze_top_layers,
        "train_size": len(train_data),
        "validation_size": len(validation_data),
        "train_label_counts": {
            str(key): int(value)
            for key, value in train_data["label"]
            .value_counts()
            .sort_index()
            .items()
        },
        "validation_label_counts": {
            str(key): int(value)
            for key, value in validation_data["label"]
            .value_counts()
            .sort_index()
            .items()
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
        "validation_at_0.5": evaluate(
            validation_labels,
            validation_probabilities,
            0.5,
        ),
        "validation_at_recall_threshold": evaluate(
            validation_labels,
            validation_probabilities,
            recall_threshold,
        ),
        "validation_summary_by_actionability": probability_summary_by_column(
            validation_data,
            validation_probabilities,
            validation_predictions,
            "actionability",
        ),
        "validation_summary_by_event_type": probability_summary_by_column(
            validation_data,
            validation_probabilities,
            validation_predictions,
            "event_type",
        ),
        "tflite_size_bytes": tflite_size_bytes,
        "conversion_max_absolute_logit_difference": conversion_max_abs_diff,
        "validation_rows": validation_rows.to_dict(orient="records"),
        "validation_errors": errors.to_dict(orient="records"),
    }
    report_path = args.output_dir / "training_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
