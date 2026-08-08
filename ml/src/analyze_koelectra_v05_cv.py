"""Aggregate fixed five-fold KoELECTRA v0.5 reports."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.metrics import precision_score, recall_score


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_DIR / "models" / "koelectra_v0.5_cv"
DEFAULT_JSON = PROJECT_DIR / "reports" / "koelectra_v0.5_cross_validation.json"
DEFAULT_MARKDOWN = PROJECT_DIR / "reports" / "koelectra_v0.5_cross_validation.md"
POOLED_THRESHOLD = 0.6587844491004944


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--report-markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--pooled-threshold", type=float, default=POOLED_THRESHOLD)
    return parser.parse_args()


def metrics(labels: np.ndarray, predictions: np.ndarray) -> dict[str, object]:
    matrix = confusion_matrix(labels, predictions, labels=[0, 1])
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "confusion_matrix": matrix.tolist(),
        "false_positive": int(matrix[0, 1]),
        "false_negative": int(matrix[1, 0]),
    }


def make_markdown(result: dict[str, object]) -> str:
    pooled = result["pooled_out_of_fold"]
    mean = result["fold_metric_summary"]
    lines = [
        "# KoELECTRA v0.5 고정 5-Fold 교차검증",
        "",
        "## 실험 조건",
        "",
        f"- 학습 가능 데이터: {result['rows']}개",
        "- 같은 `template_group`은 하나의 fold에만 배치",
        "- 각 fold마다 나머지 4개 fold로 학습하고 보지 않은 1개 fold를 평가",
        "- 모델: `monologg/koelectra-small-v3-discriminator`",
        "- 분류 헤드 3 epoch + 상위 encoder 2개 layer 6 epoch 미세조정",
        "",
        "## Fold별 결과",
        "",
        "| Fold | Rows | Threshold | Accuracy | Precision | Recall | F1 | FP | FN |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for fold in result["folds"]:
        metric = fold["metrics"]
        lines.append(
            f"| {fold['fold']} | {fold['rows']} | {fold['threshold']:.3f} | "
            f"{metric['accuracy']:.3f} | {metric['precision']:.3f} | "
            f"{metric['recall']:.3f} | {metric['f1']:.3f} | "
            f"{metric['false_positive']} | {metric['false_negative']} |"
        )
    lines.extend(
        [
            "",
            "## 요약",
            "",
            f"- Fold 평균 Accuracy: {mean['accuracy']['mean']:.3f} "
            f"(표준편차 {mean['accuracy']['std']:.3f})",
            f"- Fold 평균 Precision: {mean['precision']['mean']:.3f}",
            f"- Fold 평균 Recall: {mean['recall']['mean']:.3f}",
            f"- Fold 평균 F1: {mean['f1']['mean']:.3f}",
            f"- OOF 공통 임계값: {result['pooled_threshold']:.6f}",
            f"- 공통 임계값 OOF Accuracy: {pooled['accuracy']:.3f}",
            f"- 공통 임계값 OOF Precision: {pooled['precision']:.3f}",
            f"- 공통 임계값 OOF Recall: {pooled['recall']:.3f}",
            f"- 공통 임계값 OOF F1: {pooled['f1']:.3f}",
            f"- 공통 임계값 오탐/미탐: FP {pooled['false_positive']}, "
            f"FN {pooled['false_negative']}",
            "",
            "## 오분류 집중 유형",
            "",
        ]
    )
    for event_type, count in result["pooled_error_event_types"].items():
        lines.append(f"- `{event_type}`: {count}개")
    lines.extend(
        [
            "",
            "## 해석과 제한",
            "",
            "- Fold 3 Accuracy가 0.800으로 다른 fold보다 크게 낮아 문장군에 따른 편차가 여전히 크다.",
            "- 각 fold가 고른 임계값도 0.392~0.858로 달라 확률 보정이 안정적이지 않다.",
            "- 합성 중심 데이터의 교차검증 결과이므로 실제 사용자 알림 성능으로 해석하지 않는다.",
            "- 최종 모델의 임계값은 모든 OOF 예측을 합쳐 Recall 0.9 이상 조건으로 정한 값이다.",
            "- Android 연결 전 새 사용자·새 시점에서 모은 미사용 실제 알림 평가가 필요하다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    fold_reports = []
    all_rows: list[dict[str, object]] = []
    for fold_index in range(5):
        path = args.input_dir / f"fold_{fold_index}" / "training_report.json"
        report = json.loads(path.read_text(encoding="utf-8"))
        chosen = report["validation_at_recall_threshold"]
        fold_reports.append(
            {
                "fold": fold_index,
                "rows": report["validation_size"],
                "threshold": chosen["threshold"],
                "metrics": {
                    key: chosen[key]
                    for key in [
                        "accuracy",
                        "precision",
                        "recall",
                        "f1",
                        "confusion_matrix",
                        "false_positive",
                        "false_negative",
                    ]
                },
            }
        )
        for row in report["validation_rows"]:
            all_rows.append({**row, "fold": fold_index})

    labels = np.asarray([row["label"] for row in all_rows], dtype=np.int32)
    probabilities = np.asarray(
        [row["important_probability"] for row in all_rows], dtype=np.float64
    )
    predictions = (probabilities >= args.pooled_threshold).astype(np.int32)
    error_events = Counter(
        str(row["event_type"])
        for row, actual, prediction in zip(all_rows, labels, predictions)
        if actual != prediction
    )
    metric_names = ["accuracy", "precision", "recall", "f1"]
    summary = {}
    for name in metric_names:
        values = np.asarray(
            [fold["metrics"][name] for fold in fold_reports], dtype=np.float64
        )
        summary[name] = {
            "mean": float(values.mean()),
            "std": float(values.std()),
            "minimum": float(values.min()),
            "maximum": float(values.max()),
        }
    result: dict[str, object] = {
        "dataset_version": "0.5",
        "rows": len(all_rows),
        "folds": fold_reports,
        "fold_metric_summary": summary,
        "pooled_threshold": args.pooled_threshold,
        "pooled_out_of_fold": metrics(labels, predictions),
        "pooled_error_event_types": dict(error_events.most_common()),
    }
    args.report_json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.report_markdown.write_text(make_markdown(result), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
