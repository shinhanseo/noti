"""Evaluate the trained KoELECTRA TFLite model on local Room REVIEW data."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from ai_edge_litert.interpreter import Interpreter
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score
from transformers import AutoTokenizer

from evaluate_real_room_v03 import (
    DEFAULT_DATABASE,
    DEFAULT_HUMAN_LABELS,
    load_room_candidates,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_VERSION = "0.5"
DEFAULT_MODEL = (
    PROJECT_DIR
    / "models"
    / "koelectra_tensorflow_v0.5_final"
    / "noti_koelectra_v0.5_final_fp32.tflite"
)
DEFAULT_TRAINING_REPORT = (
    PROJECT_DIR
    / "models"
    / "koelectra_tensorflow_v0.5_final"
    / "training_report.json"
)
DEFAULT_PRIVATE_OUTPUT = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-06_approved"
    / "room_review_koelectra_predictions_v0.5.csv"
)
DEFAULT_REPORT_JSON = (
    PROJECT_DIR / "reports" / "v0.5_koelectra_real_room_evaluation.json"
)
DEFAULT_REPORT_MARKDOWN = (
    PROJECT_DIR / "reports" / "v0.5_koelectra_real_room_evaluation.md"
)
MODEL_NAME = "monologg/koelectra-small-v3-discriminator"
SEQ_LEN = 64


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--labels", type=Path, default=DEFAULT_HUMAN_LABELS)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument(
        "--training-report",
        type=Path,
        default=DEFAULT_TRAINING_REPORT,
    )
    parser.add_argument(
        "--private-output",
        type=Path,
        default=DEFAULT_PRIVATE_OUTPUT,
    )
    parser.add_argument("--dataset-version", default=DEFAULT_VERSION)
    parser.add_argument(
        "--report-json",
        type=Path,
        default=DEFAULT_REPORT_JSON,
    )
    parser.add_argument(
        "--report-markdown",
        type=Path,
        default=DEFAULT_REPORT_MARKDOWN,
    )
    return parser.parse_args()


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / np.sum(exponentials, axis=-1, keepdims=True)


def create_markdown(result: dict[str, object]) -> str:
    metrics = result["metrics"]
    return "\n".join(
        [
            f"# KoELECTRA v{result['dataset_version']} 실제 Room 개발 세트 점검",
            "",
            "## 조건",
            "",
            f"- 실제 REVIEW 알림: {result['review_rows']}개",
            f"- 사용자 중요 라벨: {result['important_rows']}개",
            f"- 사용자 일반 라벨: {result['general_rows']}개",
            f"- 임계값: {result['threshold']:.6f}",
            "- 실제 알림 원문과 개별 예측은 Git 제외 private CSV에만 저장",
            "",
            "## 결과",
            "",
            f"- Accuracy: {metrics['accuracy']:.1%}",
            f"- Precision: {metrics['precision']:.3f}",
            f"- Recall: {metrics['recall']:.3f}",
            f"- False Positive: {metrics['false_positive']}",
            f"- False Negative: {metrics['false_negative']}",
            f"- 중요 예측: {result['important_predictions']}개",
            f"- 일반 예측: {result['general_predictions']}개",
            "",
            "## 로컬 Mac CPU 참고값",
            "",
            f"- Median latency: {result['latency_ms']['median']:.2f} ms",
            f"- P95 latency: {result['latency_ms']['p95']:.2f} ms",
            "- Android 실기기 성능이 아니므로 배포 성능으로 해석하지 않는다.",
            "",
            "## 제한",
            "",
            "- 실제 중요 라벨이 1개뿐이므로 Recall은 통계적으로 신뢰할 수 없다.",
            "- 이 라벨은 한 사용자의 개인 선호이며 공통 모델의 행동 필요성 정답과 동일하지 않다.",
            "- 이 Room 알림에서 발견한 실패 유형을 v0.5 데이터 설계에 반영했으므로 독립 평가 세트가 아니다.",
            "- 모델 선택과 Android 적용 판단은 새 사용자·새 시점의 미사용 알림으로 다시 해야 한다.",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    training_report = json.loads(args.training_report.read_text(encoding="utf-8"))
    threshold = float(
        training_report["validation_at_recall_threshold"]["threshold"]
    )
    room_data = load_room_candidates(args.database)
    labels = pd.read_csv(args.labels, dtype={"private_id": str})
    label_map = labels.set_index("private_id")["human_label"]
    room_data["human_label"] = room_data["private_id"].map(label_map)
    labeled = room_data[room_data["human_label"].notna()].copy()
    if labeled.empty:
        raise RuntimeError("사용자 라벨이 있는 실제 REVIEW 알림이 없습니다.")

    tokenizer = AutoTokenizer.from_pretrained(
        args.model.parent / "tokenizer",
        use_fast=True,
        local_files_only=True,
    )
    interpreter = Interpreter(model_path=str(args.model), num_threads=2)
    signature = interpreter.get_signature_runner("serving_default")

    probabilities: list[float] = []
    latencies_ms: list[float] = []
    for text in labeled["text"]:
        encoded = tokenizer(
            text,
            max_length=SEQ_LEN,
            padding="max_length",
            truncation=True,
            return_tensors="np",
        )
        input_ids = encoded["input_ids"].astype(np.int32)
        inputs = {
            "input_ids": input_ids,
            "attention_mask": encoded["attention_mask"].astype(np.int32),
            "token_type_ids": encoded.get(
                "token_type_ids",
                np.zeros_like(input_ids),
            ).astype(np.int32),
        }
        started = time.perf_counter()
        logits = np.asarray(signature(**inputs)["logits"])
        latencies_ms.append((time.perf_counter() - started) * 1000)
        probabilities.append(float(softmax(logits)[0, 1]))

    labeled["important_probability"] = probabilities
    labeled["prediction"] = (
        labeled["important_probability"] >= threshold
    ).astype(int)
    actual = labeled["human_label"].astype(int)
    predicted = labeled["prediction"].astype(int)
    matrix = confusion_matrix(actual, predicted, labels=[0, 1])
    result: dict[str, object] = {
        "dataset_version": args.dataset_version,
        "model": str(args.model.relative_to(PROJECT_DIR)),
        "review_rows": len(labeled),
        "important_rows": int(actual.sum()),
        "general_rows": int((actual == 0).sum()),
        "threshold": threshold,
        "important_predictions": int(predicted.sum()),
        "general_predictions": int((predicted == 0).sum()),
        "positive_label_probabilities": [
            float(value)
            for value in labeled.loc[actual == 1, "important_probability"]
        ],
        "metrics": {
            "accuracy": float(accuracy_score(actual, predicted)),
            "precision": float(precision_score(actual, predicted, zero_division=0)),
            "recall": float(recall_score(actual, predicted, zero_division=0)),
            "false_positive": int(matrix[0, 1]),
            "false_negative": int(matrix[1, 0]),
            "confusion_matrix": matrix.tolist(),
        },
        "latency_ms": {
            "median": float(np.median(latencies_ms)),
            "p95": float(np.percentile(latencies_ms, 95)),
            "minimum": float(np.min(latencies_ms)),
            "maximum": float(np.max(latencies_ms)),
        },
    }

    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    labeled[
        [
            "private_id",
            "package_name",
            "title",
            "body",
            "human_label",
            "important_probability",
            "prediction",
        ]
    ].to_csv(args.private_output, index=False, encoding="utf-8-sig")
    args.report_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    args.report_markdown.write_text(create_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
