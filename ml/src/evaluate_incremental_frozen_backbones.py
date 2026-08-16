"""Evaluate previously frozen model predictions after human labeling."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from actionability_contract import ACTIONABILITY_LABELS
from compare_frozen_backbones_v05 import MODELS
from evaluate_granite_v05_v06_blind_holdout import (
    mcnemar_exact,
    model_metrics,
    paired_accuracy_interval,
    paired_important_f1_interval,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
PRIVATE_DIR = PROJECT_DIR / "data" / "private" / "room_export_2026-08-16_raw"
HOLDOUT_PATH = PRIVATE_DIR / "incremental_holdout_review.csv"
FROZEN_PATH = PRIVATE_DIR / "incremental_holdout_frozen_predictions.csv"
EVALUATION_PATH = PRIVATE_DIR / "incremental_holdout_frozen_evaluation.csv"
JSON_OUTPUT = PROJECT_DIR / "reports" / "incremental_frozen_benchmark_2026-08-16.json"
MARKDOWN_OUTPUT = PROJECT_DIR / "reports" / "incremental_frozen_benchmark_2026-08-16.md"


def markdown(report: dict[str, object]) -> str:
    lines = [
        "# 증분 Room Frozen Backbone 블라인드 평가",
        "",
        "라벨 입력 전에 봉인한 세 모델 예측을 새 실제 알림 정답과 비교했다.",
        "",
        "| 모델 | 3단계 Accuracy | 등장 클래스 Macro F1 | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for config in MODELS:
        key = config["key"]
        metrics = report["models"][key]
        binary = metrics["important_binary"]
        lines.append(
            f"| {key} | {metrics['three_class_accuracy']:.3f} | "
            f"{metrics['observed_class_macro_f1']:.3f} | {binary['precision']:.3f} | "
            f"{binary['recall']:.3f} | {binary['f1']:.3f} | "
            f"{binary['false_positive']} | {binary['false_negative']} |"
        )
    lines.extend(["", "## 대응 비교", ""])
    lines.extend(
        [
            "| 비교 | Accuracy 차이 | Accuracy 95% CI | 중요 F1 차이 | 중요 F1 95% CI | McNemar p |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, value in report["paired_comparisons"].items():
        accuracy = value["accuracy"]
        important = value["important_f1"]
        lines.append(
            f"| {name} | {accuracy['right_minus_left']:+.3f} | "
            f"{accuracy['bootstrap_95_low']:+.3f}~{accuracy['bootstrap_95_high']:+.3f} | "
            f"{important['right_minus_left']:+.3f} | "
            f"{important['bootstrap_95_low']:+.3f}~{important['bootstrap_95_high']:+.3f} | "
            f"{value['mcnemar']['two_sided_exact_p']:.6f} |"
        )
    lines.extend(
        [
            "",
            "45개는 이전 Room 스냅샷 이후에 도착한 시간상 독립 표본이다.",
            "모델 예측은 사람 라벨을 입력하기 전에 SHA-256과 함께 봉인했다.",
            "실제 알림 원문과 행별 결과는 private 경로에만 저장했다.",
            "표본이 작으므로 신뢰구간과 개별 오분류를 함께 해석해야 한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    holdout = pd.read_csv(HOLDOUT_PATH, dtype=str).fillna("")
    if not holdout["user_common_actionability"].isin(ACTIONABILITY_LABELS).all():
        raise ValueError("공통 Actionability 라벨이 완성되지 않았습니다.")
    frozen = pd.read_csv(FROZEN_PATH, dtype=str).fillna("")
    evaluation = holdout[["review_id", "private_id", "user_common_actionability"]].merge(
        frozen, on=["review_id", "private_id"], how="inner", validate="one_to_one"
    )
    if len(evaluation) != len(holdout):
        raise ValueError("검수 세트와 봉인 예측 행이 일치하지 않습니다.")

    actual = evaluation["user_common_actionability"].to_numpy()
    predictions: dict[str, np.ndarray] = {}
    report: dict[str, object] = {
        "protocol": {
            "holdout_rows": len(evaluation),
            "label_counts": holdout["user_common_actionability"].value_counts().to_dict(),
            "prediction_status": "FROZEN_BEFORE_HUMAN_LABELING",
        },
        "models": {},
    }
    for config in MODELS:
        key = config["key"]
        prediction = evaluation[f"{key}_actionability"].to_numpy()
        predictions[key] = prediction
        report["models"][key] = model_metrics(
            pd.Series(actual), pd.Series(prediction)
        )

    report["paired_comparisons"] = {}
    keys = [config["key"] for config in MODELS]
    for left_index, left in enumerate(keys):
        for right in keys[left_index + 1 :]:
            accuracy = paired_accuracy_interval(actual, predictions[left], predictions[right])
            important = paired_important_f1_interval(actual, predictions[left], predictions[right])
            report["paired_comparisons"][f"{right}_minus_{left}"] = {
                "accuracy": {
                    "right_minus_left": accuracy["v06_minus_v05"],
                    "bootstrap_95_low": accuracy["bootstrap_95_low"],
                    "bootstrap_95_high": accuracy["bootstrap_95_high"],
                },
                "important_f1": {
                    "right_minus_left": important["v06_minus_v05"],
                    "bootstrap_95_low": important["bootstrap_95_low"],
                    "bootstrap_95_high": important["bootstrap_95_high"],
                },
                "mcnemar": mcnemar_exact(actual, predictions[left], predictions[right]),
            }

    evaluation.to_csv(EVALUATION_PATH, index=False, encoding="utf-8-sig")
    JSON_OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(markdown(report), encoding="utf-8")
    print(markdown(report))


if __name__ == "__main__":
    main()
