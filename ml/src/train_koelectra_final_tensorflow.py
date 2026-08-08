"""Train KoELECTRA on all eligible rows after cross-validation and export TFLite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

from train_koelectra_tensorflow import (
    MODEL_NAME,
    KoElectraModule,
    compile_classifier,
    default_project_dir,
    load_data,
    serializable_history,
    tokenize,
)


def parse_args() -> argparse.Namespace:
    project_dir = default_project_dir()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=Path,
        default=project_dir / "data" / "public" / "train_notifications_v0.5.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_dir / "models" / "koelectra_tensorflow_v0.5_final",
    )
    parser.add_argument("--dataset-version", default="0.5")
    parser.add_argument("--decision-threshold", type=float, required=True)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--head-epochs", type=int, default=3)
    parser.add_argument("--finetune-epochs", type=int, default=6)
    parser.add_argument("--head-learning-rate", type=float, default=3e-4)
    parser.add_argument("--finetune-learning-rate", type=float, default=2e-5)
    parser.add_argument("--unfreeze-top-layers", type=int, default=2)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    np.random.seed(42)
    tf.random.set_seed(42)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    data = load_data(args.data)
    labels = data["label"].to_numpy(dtype=np.int32)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
    inputs = tokenize(tokenizer, data["text"].tolist())
    classifier = TFAutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        from_pt=True,
        num_labels=2,
    )

    classifier.electra.trainable = False
    compile_classifier(classifier, args.head_learning_rate)
    head_history = classifier.fit(
        inputs,
        labels,
        epochs=args.head_epochs,
        batch_size=args.batch_size,
        verbose=2,
    )

    encoder_layers = classifier.electra.encoder.layer
    classifier.electra.trainable = True
    classifier.electra.embeddings.trainable = False
    classifier.electra.embeddings_project.trainable = False
    for layer in encoder_layers:
        layer.trainable = False
    for layer in encoder_layers[-args.unfreeze_top_layers :]:
        layer.trainable = True

    compile_classifier(classifier, args.finetune_learning_rate)
    finetune_history = classifier.fit(
        inputs,
        labels,
        epochs=args.finetune_epochs,
        batch_size=args.batch_size,
        verbose=2,
    )

    module = KoElectraModule(classifier)
    concrete_function = module.serve.get_concrete_function()
    converter = tf.lite.TFLiteConverter.from_concrete_functions(
        [concrete_function],
        module,
    )
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
    tflite_model = converter.convert()
    tflite_path = args.output_dir / (
        f"noti_koelectra_v{args.dataset_version}_final_fp32.tflite"
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
    signature = interpreter.get_signature_runner("serving_default")
    tflite_logits = np.asarray(signature(**sample_inputs)["logits"])
    conversion_max_abs_diff = float(
        np.max(np.abs(tensorflow_logits - tflite_logits))
    )

    classifier.save_weights(str(args.output_dir / "classifier.weights.h5"))
    tokenizer.save_pretrained(args.output_dir / "tokenizer")
    report = {
        "status": "final_training_and_conversion_complete",
        "model": MODEL_NAME,
        "dataset_version": args.dataset_version,
        "dataset": str(args.data),
        "training_rows": len(data),
        "training_label_counts": {
            str(key): int(value)
            for key, value in data["label"].value_counts().sort_index().items()
        },
        "training_strategy": "all_rows_after_fixed_5_fold_cross_validation",
        "unfrozen_top_encoder_layers": args.unfreeze_top_layers,
        "epochs_completed": {
            "head": len(head_history.history["loss"]),
            "finetune": len(finetune_history.history["loss"]),
        },
        "history": {
            "head": serializable_history(head_history),
            "finetune": serializable_history(finetune_history),
        },
        "validation_at_recall_threshold": {
            "threshold": args.decision_threshold,
            "source": "pooled_out_of_fold_predictions",
        },
        "tflite_size_bytes": len(tflite_model),
        "conversion_max_absolute_logit_difference": conversion_max_abs_diff,
    }
    (args.output_dir / "training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
