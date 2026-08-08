"""Try an independent KoELECTRA TensorFlow -> TFLite conversion path."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")

import numpy as np
import tensorflow as tf
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification


MODEL_NAME = "monologg/koelectra-small-v3-discriminator"
SEQ_LEN = 64
TEXT = "쿠팡 주문하신 상품이 배송을 시작했습니다."


def output_dir() -> Path:
    script_path = globals().get("__file__")
    if script_path:
        return (
            Path(script_path).resolve().parents[1]
            / "models"
            / "koelectra_tensorflow_litert_probe"
        )
    return Path.cwd() / "koelectra_tensorflow_litert_probe"


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


def main() -> None:
    tf.random.set_seed(42)
    destination = output_dir()
    destination.mkdir(parents=True, exist_ok=True)
    report_path = destination / "probe_report.json"
    report: dict[str, object] = {
        "model": MODEL_NAME,
        "sequence_length": SEQ_LEN,
        "conversion_path": "pytorch_checkpoint_to_tensorflow_to_tflite",
        "tensorflow": tf.__version__,
    }

    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)
        classifier = TFAutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            from_pt=True,
            num_labels=2,
        )
        encoded = tokenizer(
            TEXT,
            max_length=SEQ_LEN,
            padding="max_length",
            truncation=True,
            return_tensors="np",
        )
        inputs = {
            "input_ids": tf.convert_to_tensor(encoded["input_ids"], tf.int32),
            "attention_mask": tf.convert_to_tensor(
                encoded["attention_mask"], tf.int32
            ),
            "token_type_ids": tf.convert_to_tensor(
                encoded.get(
                    "token_type_ids",
                    np.zeros_like(encoded["input_ids"]),
                ),
                tf.int32,
            ),
        }
        module = KoElectraModule(classifier)
        tensorflow_logits = module.serve(**inputs)["logits"].numpy()
        concrete_function = module.serve.get_concrete_function()

        converter = tf.lite.TFLiteConverter.from_concrete_functions(
            [concrete_function],
            module,
        )
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS]
        tflite_model = converter.convert()
        tflite_path = destination / "koelectra_small_tensorflow_fp32.tflite"
        tflite_path.write_bytes(tflite_model)

        interpreter = tf.lite.Interpreter(model_content=tflite_model)
        signature = interpreter.get_signature_runner("serving_default")
        tflite_outputs = signature(
            input_ids=inputs["input_ids"].numpy(),
            attention_mask=inputs["attention_mask"].numpy(),
            token_type_ids=inputs["token_type_ids"].numpy(),
        )
        tflite_logits = np.asarray(tflite_outputs["logits"])
        max_logit_diff = float(
            np.max(np.abs(tensorflow_logits - tflite_logits))
        )
        tensorflow_probabilities = tf.nn.softmax(
            tensorflow_logits, axis=-1
        ).numpy()
        tflite_probabilities = tf.nn.softmax(tflite_logits, axis=-1).numpy()
        max_probability_diff = float(
            np.max(
                np.abs(
                    tensorflow_probabilities - tflite_probabilities
                )
            )
        )
        report.update(
            {
                "status": (
                    "conversion_complete"
                    if max_logit_diff <= 1e-3
                    else "conversion_complete_numerical_mismatch"
                ),
                "tensorflow_logits": tensorflow_logits.tolist(),
                "tflite_logits": tflite_logits.tolist(),
                "max_absolute_logit_difference": max_logit_diff,
                "max_absolute_probability_difference": max_probability_diff,
                "tflite_size_bytes": len(tflite_model),
                "tflite_path": str(tflite_path),
            }
        )
        tokenizer.save_pretrained(destination / "tokenizer")
    except Exception as error:
        report.update(
            {
                "status": "failed",
                "error_type": type(error).__name__,
                "message": str(error),
            }
        )
        raise
    finally:
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
