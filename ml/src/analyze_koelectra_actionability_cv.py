"""Aggregate fixed five-fold reports for the three-tier actionability model."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)

from actionability_contract import ACTIONABILITY_LABELS


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_DIR / "models" / "koelectra_actionability_triage_v0.5_cv"
DEFAULT_JSON = (
    PROJECT_DIR
    / "reports"
    / "koelectra_actionability_triage_v0.5_cross_validation.json"
)
DEFAULT_MARKDOWN = (
    PROJECT_DIR
    / "reports"
    / "koelectra_actionability_triage_v0.5_cross_validation.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report-markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--minimum-important-recall", type=float, default=0.9)
    return parser.parse_args()


def choose_threshold(
    actual: np.ndarray,
    probabilities: np.ndarray,
    minimum_recall: float,
) -> float:
    precisions, recalls, thresholds = precision_recall_curve(actual, probabilities)
    candidates = [
        (float(precision), float(recall), float(threshold))
        for precision, recall, threshold in zip(
            precisions[:-1], recalls[:-1], thresholds
        )
        if recall >= minimum_recall
    ]
    if not candidates:
        return 0.5
    return max(candidates, key=lambda item: (item[0], item[2]))[2]


def multiclass_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
) -> dict[str, object]:
    labels = list(range(len(ACTIONABILITY_LABELS)))
    precision, recall, f1, support = precision_recall_fscore_support(
        actual, predicted, labels=labels, zero_division=0
    )
    macro = precision_recall_fscore_support(
        actual, predicted, labels=labels, average="macro", zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_precision": float(macro[0]),
        "macro_recall": float(macro[1]),
        "macro_f1": float(macro[2]),
        "confusion_matrix": confusion_matrix(
            actual, predicted, labels=labels
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


def binary_metrics(
    actual: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
) -> dict[str, object]:
    predicted = (probabilities >= threshold).astype(np.int32)
    matrix = confusion_matrix(actual, predicted, labels=[0, 1])
    return {
        "threshold": threshold,
        "accuracy": float(accuracy_score(actual, predicted)),
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
        "false_positive": int(matrix[0, 1]),
        "false_negative": int(matrix[1, 0]),
    }


def metric_summary(values: list[float]) -> dict[str, float]:
    array = np.asarray(values, dtype=np.float64)
    return {
        "mean": float(array.mean()),
        "std": float(array.std()),
        "minimum": float(array.min()),
        "maximum": float(array.max()),
    }


def make_markdown(result: dict[str, object]) -> str:
    pooled_actionability = result["pooled_actionability_metrics"]
    pooled_binary = result["pooled_binary_metrics"]
    summary = result["fold_metric_summary"]
    lines = [
        "# KoELECTRA v0.5 3-Tier Actionability 교차검증",
        "",
        "## 출력 계약",
        "",
        "```text",
        *[f"{index} {label}" for index, label in enumerate(ACTIONABILITY_LABELS)],
        "```",
        "",
        "`important_probability = P(ATTENTION_WORTHY) + P(ACTION_REQUIRED)`로 계산한다.",
        "",
        "## Fold별 결과",
        "",
        "| Fold | Rows | 3-tier Acc | Macro F1 | Binary threshold | Binary P | Binary R |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for fold in result["folds"]:
        multi = fold["actionability_metrics"]
        binary = fold["binary_metrics"]
        lines.append(
            f"| {fold['fold']} | {fold['rows']} | {multi['accuracy']:.3f} | "
            f"{multi['macro_f1']:.3f} | {binary['threshold']:.3f} | "
            f"{binary['precision']:.3f} | {binary['recall']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## 전체 OOF 결과",
            "",
            f"- Fold 평균 3-tier Accuracy: {summary['accuracy']['mean']:.3f} "
            f"± {summary['accuracy']['std']:.3f}",
            f"- Fold 평균 Macro F1: {summary['macro_f1']['mean']:.3f} "
            f"± {summary['macro_f1']['std']:.3f}",
            f"- Pooled 3-tier Accuracy: {pooled_actionability['accuracy']:.3f}",
            f"- Pooled Macro F1: {pooled_actionability['macro_f1']:.3f}",
            f"- 공통 중요 확률 임계값: {pooled_binary['threshold']:.6f}",
            f"- 공통 임계값 Binary Accuracy: {pooled_binary['accuracy']:.3f}",
            f"- 공통 임계값 Binary Precision: {pooled_binary['precision']:.3f}",
            f"- 공통 임계값 Binary Recall: {pooled_binary['recall']:.3f}",
            f"- 공통 임계값 FP/FN: {pooled_binary['false_positive']}/"
            f"{pooled_binary['false_negative']}",
            "",
            "## 클래스별 OOF 결과",
            "",
            "| Class | Precision | Recall | F1 | Support |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for label in ACTIONABILITY_LABELS:
        metric = pooled_actionability["per_class"][label]
        lines.append(
            f"| {label} | {metric['precision']:.3f} | {metric['recall']:.3f} | "
            f"{metric['f1']:.3f} | {metric['support']} |"
        )
    lines.extend(
        [
            "",
            "## 제한",
            "",
            "- 데이터는 합성 중심이므로 실제 알림 일반화 성능이 아니다.",
            "- 3-tier 성능과 중요/일반 합산 성능을 함께 통과해야 Android에 반영한다.",
            "- 기존 Room 12개는 데이터 설계에 참고했으므로 독립 테스트로 사용하지 않는다.",
            "- 개인 선호는 이 공통 모델의 정답이 아니라 Android 보정 계층에서 처리한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    fold_summaries = []
    rows: list[dict[str, object]] = []
    for fold_index in range(5):
        path = args.input_dir / f"fold_{fold_index}" / "training_report.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        fold_summaries.append(
            {
                "fold": fold_index,
                "rows": report["validation_size"],
                "actionability_metrics": report["actionability_metrics"],
                "binary_metrics": report[
                    "binary_metrics_at_recall_threshold"
                ],
            }
        )
        rows.extend(report["validation_rows"])

    actual_actionability = np.asarray(
        [row["actual_actionability_id"] for row in rows], dtype=np.int32
    )
    predicted_actionability = np.asarray(
        [row["predicted_actionability_id"] for row in rows], dtype=np.int32
    )
    binary_actual = np.asarray([row["label"] for row in rows], dtype=np.int32)
    important_probability = np.asarray(
        [row["important_probability"] for row in rows], dtype=np.float64
    )
    threshold = choose_threshold(
        binary_actual, important_probability, args.minimum_important_recall
    )
    pooled_actionability = multiclass_metrics(
        actual_actionability, predicted_actionability
    )
    pooled_binary = binary_metrics(binary_actual, important_probability, threshold)
    predicted_binary = (important_probability >= threshold).astype(np.int32)
    error_event_types = Counter(
        str(row["event_type"])
        for row, actual, predicted in zip(rows, binary_actual, predicted_binary)
        if actual != predicted
    )
    result: dict[str, object] = {
        "dataset_version": "0.5",
        "label_order": list(ACTIONABILITY_LABELS),
        "rows": len(rows),
        "folds": fold_summaries,
        "fold_metric_summary": {
            "accuracy": metric_summary(
                [fold["actionability_metrics"]["accuracy"] for fold in fold_summaries]
            ),
            "macro_f1": metric_summary(
                [fold["actionability_metrics"]["macro_f1"] for fold in fold_summaries]
            ),
        },
        "pooled_actionability_metrics": pooled_actionability,
        "pooled_binary_metrics": pooled_binary,
        "binary_error_event_types": dict(error_event_types.most_common()),
    }
    args.report_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.report_markdown.write_text(make_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
