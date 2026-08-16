"""Run the three-tier actionability TFLite model on local Room REVIEW data."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from ai_edge_litert.interpreter import Interpreter
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from transformers import AutoTokenizer

from actionability_contract import (
    ACTIONABILITY_LABELS,
    important_probabilities,
    model_score_delta,
    predicted_actionability,
    probability_columns,
    softmax,
)
from evaluate_real_room_v03 import (
    DEFAULT_DATABASE,
    DEFAULT_HUMAN_LABELS,
    load_room_candidates,
)
from notification_text_preprocessor import (
    PREPROCESSING_VERSION,
    normalize_notification_text,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_DIR / "models" / "koelectra_actionability_triage_v0.5_final"
DEFAULT_MODEL = MODEL_DIR / "noti_koelectra_actionability_v0.5_final_fp32.tflite"
DEFAULT_TRAINING_REPORT = MODEL_DIR / "training_report.json"
DEFAULT_PRIVATE_OUTPUT = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-06_approved"
    / "room_review_koelectra_actionability_v0.5.csv"
)
DEFAULT_REPORT_JSON = (
    PROJECT_DIR / "reports" / "v0.5_koelectra_actionability_room.json"
)
DEFAULT_REPORT_MARKDOWN = (
    PROJECT_DIR / "reports" / "v0.5_koelectra_actionability_room.md"
)
SEQ_LEN = 64


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--labels", type=Path, default=DEFAULT_HUMAN_LABELS)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument(
        "--training-report", type=Path, default=DEFAULT_TRAINING_REPORT
    )
    parser.add_argument("--private-output", type=Path, default=DEFAULT_PRIVATE_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument(
        "--report-markdown", type=Path, default=DEFAULT_REPORT_MARKDOWN
    )
    parser.add_argument(
        "--evaluation-kind",
        choices=("development", "independent_holdout"),
        default="development",
    )
    parser.add_argument(
        "--text-preprocessing",
        choices=("legacy", "android_v2"),
        default="android_v2",
    )
    return parser.parse_args()


def make_markdown(result: dict[str, object]) -> str:
    metric = result["personal_label_metrics"]
    independent = result["evaluation_kind"] == "independent_holdout"
    lines = [
        (
            "# KoELECTRA v0.5 3-Tier 실제 Room 독립 홀드아웃"
            if independent
            else "# KoELECTRA v0.5 3-Tier 실제 Room 개발 세트 점검"
        ),
        "",
        "## 조건",
        "",
        f"- 실제 REVIEW 알림: {result['review_rows']}개",
        f"- 사용자 중요/일반: {result['important_rows']}/{result['general_rows']}",
        f"- OOF 이진 임계값: {result['binary_threshold']:.6f}",
        f"- 텍스트 전처리: `{result['text_preprocessing']}`",
        (
            "- 모델 학습 당시 전처리: "
            f"`{result['model_training_text_preprocessing']}`"
        ),
        "- 실제 원문과 개별 예측은 Git 제외 private CSV에만 저장",
        "",
        "## 개인 라벨과 비교한 참고 결과",
        "",
        f"- Accuracy: {metric['accuracy']:.3f}",
        f"- Precision: {metric['precision']:.3f}",
        f"- Recall: {metric['recall']:.3f}",
        f"- FP/FN: {metric['false_positive']}/{metric['false_negative']}",
        "",
    ]
    if "common_actionability_metrics" in result:
        actionability = result["common_actionability_metrics"]
        lines.extend(
            [
                "## 공통 Actionability 정답과 비교",
                "",
                f"- Accuracy: {actionability['accuracy']:.3f}",
                f"- Macro F1: {actionability['macro_f1']:.3f}",
                "- Confusion matrix 순서: GENERAL, ATTENTION_WORTHY, ACTION_REQUIRED",
                "",
            ]
        )
    lines.extend(
        [
        "## 예측 Actionability 분포",
        "",
        ]
    )
    for label in ACTIONABILITY_LABELS:
        lines.append(f"- `{label}`: {result['predicted_actionability_counts'].get(label, 0)}개")
    lines.extend(
        [
            "",
            "## 로컬 Mac CPU 참고값",
            "",
            f"- Median latency: {result['latency_ms']['median']:.2f} ms",
            f"- P95 latency: {result['latency_ms']['p95']:.2f} ms",
            "",
            "## 제한",
            "",
            "- 사용자 중요/일반 라벨은 공통 actionability 정답과 다르다.",
            (
                "- 모델과 임계값을 고정한 뒤 수집한 독립 홀드아웃이다."
                if independent
                else "- 이 데이터는 모델 설계에 참고했으므로 독립 테스트가 아니다."
            ),
            (
                "- 6개뿐인 작은 표본이므로 Android 적용 판단에는 부족하다."
                if independent
                else "- Android 적용 전 새 실제 홀드아웃이 필요하다."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    training_report = json.loads(args.training_report.read_text(encoding="utf-8"))
    threshold = float(training_report["binary_decision_threshold"]["threshold"])
    room_data = load_room_candidates(args.database)
    labels = pd.read_csv(args.labels, dtype={"private_id": str})
    indexed_labels = labels.set_index("private_id")
    if "human_label" in labels:
        personal_labels = indexed_labels["human_label"]
    elif "personal_preference" in labels:
        unknown_preferences = set(labels["personal_preference"].dropna()) - {
            "GENERAL",
            "IMPORTANT",
        }
        if unknown_preferences:
            raise ValueError(
                f"알 수 없는 personal_preference: {sorted(unknown_preferences)}"
            )
        personal_labels = indexed_labels["personal_preference"].map(
            {"GENERAL": 0, "IMPORTANT": 1}
        )
    else:
        raise ValueError(
            "라벨 CSV에는 human_label 또는 personal_preference가 필요합니다."
        )
    room_data["human_label"] = room_data["private_id"].map(personal_labels)
    if "common_actionability" in labels:
        room_data["common_actionability"] = room_data["private_id"].map(
            indexed_labels["common_actionability"]
        )
    labeled = room_data[room_data["human_label"].notna()].copy()
    if labeled.empty:
        raise RuntimeError("사용자 라벨이 있는 실제 REVIEW 알림이 없습니다.")
    if args.text_preprocessing == "android_v2":
        labeled["text"] = [
            normalize_notification_text(package_name, title, body)
            for package_name, title, body in zip(
                labeled["package_name"],
                labeled["title"],
                labeled["body"],
            )
        ]

    tokenizer = AutoTokenizer.from_pretrained(
        args.model.parent / "tokenizer", use_fast=True, local_files_only=True
    )
    interpreter = Interpreter(model_path=str(args.model), num_threads=2)
    signature = interpreter.get_signature_runner("serving_default")
    outputs = []
    latencies_ms = []
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
                "token_type_ids", np.zeros_like(input_ids)
            ).astype(np.int32),
        }
        started = time.perf_counter()
        logits = np.asarray(signature(**inputs)["logits"])
        latencies_ms.append((time.perf_counter() - started) * 1000)
        outputs.append(softmax(logits)[0])

    probabilities = np.asarray(outputs, dtype=np.float64)
    actionability_predictions = predicted_actionability(probabilities)
    important_probability = important_probabilities(probabilities)
    binary_prediction = (important_probability >= threshold).astype(np.int32)
    actual = labeled["human_label"].astype(int).to_numpy()
    matrix = confusion_matrix(actual, binary_prediction, labels=[0, 1])
    labeled["predicted_actionability"] = actionability_predictions
    for column, values in probability_columns(probabilities).items():
        labeled[column] = values
    labeled["important_probability"] = important_probability
    labeled["model_score_delta"] = [
        model_score_delta(value) for value in important_probability
    ]
    labeled["binary_prediction"] = binary_prediction

    result: dict[str, object] = {
        "dataset_version": "0.5",
        "evaluation_kind": args.evaluation_kind,
        "text_preprocessing": (
            PREPROCESSING_VERSION
            if args.text_preprocessing == "android_v2"
            else "legacy-title-body-v1"
        ),
        "model_training_text_preprocessing": training_report.get(
            "text_preprocessing", "legacy-title-body-v1"
        ),
        "review_rows": len(labeled),
        "important_rows": int(actual.sum()),
        "general_rows": int((actual == 0).sum()),
        "binary_threshold": threshold,
        "predicted_actionability_counts": {
            str(key): int(value)
            for key, value in labeled["predicted_actionability"].value_counts().items()
        },
        "model_score_delta_counts": {
            str(key): int(value)
            for key, value in labeled["model_score_delta"].value_counts().items()
        },
        "personal_label_metrics": {
            "accuracy": float(accuracy_score(actual, binary_prediction)),
            "precision": float(
                precision_score(actual, binary_prediction, zero_division=0)
            ),
            "recall": float(recall_score(actual, binary_prediction, zero_division=0)),
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
    if "common_actionability" in labeled:
        actionability_labeled = labeled[
            labeled["common_actionability"].notna()
            & labeled["common_actionability"].ne("")
        ]
        if not actionability_labeled.empty:
            actionability_actual = actionability_labeled[
                "common_actionability"
            ].astype(str)
            actionability_predicted = actionability_labeled[
                "predicted_actionability"
            ].astype(str)
            result["common_actionability_metrics"] = {
                "rows": len(actionability_labeled),
                "accuracy": float(
                    accuracy_score(actionability_actual, actionability_predicted)
                ),
                "macro_f1": float(
                    f1_score(
                        actionability_actual,
                        actionability_predicted,
                        labels=list(ACTIONABILITY_LABELS),
                        average="macro",
                        zero_division=0,
                    )
                ),
                "confusion_matrix": confusion_matrix(
                    actionability_actual,
                    actionability_predicted,
                    labels=list(ACTIONABILITY_LABELS),
                ).tolist(),
            }
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    output_columns = [
        "private_id",
        "package_name",
        "title",
        "body",
        "human_label",
        *(["common_actionability"] if "common_actionability" in labeled else []),
        "predicted_actionability",
        *probability_columns(probabilities).keys(),
        "important_probability",
        "model_score_delta",
        "binary_prediction",
    ]
    labeled[output_columns].to_csv(
        args.private_output, index=False, encoding="utf-8-sig"
    )
    args.report_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.report_markdown.write_text(make_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
