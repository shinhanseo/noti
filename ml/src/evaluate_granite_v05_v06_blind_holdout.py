"""Evaluate sealed v0.5/v0.6 predictions after all blind labels are complete."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from actionability_contract import ACTIONABILITY_LABELS


PROJECT_DIR = Path(__file__).resolve().parents[1]
PRIVATE_DIR = PROJECT_DIR / "data" / "private" / "room_export_2026-08-12_raw"
LABELS_PATH = PRIVATE_DIR / "blind_holdout_review_100.csv"
PREDICTIONS_PATH = PRIVATE_DIR / "blind_holdout_frozen_predictions_v05_v06.csv"
METADATA_PATH = (
    PROJECT_DIR
    / "models"
    / "granite_v05_v06_blind_freeze"
    / "freeze_metadata.json"
)
PRIVATE_RESULTS_PATH = PRIVATE_DIR / "blind_holdout_evaluation_v05_v06.csv"
JSON_OUTPUT = PROJECT_DIR / "reports" / "granite_v05_v06_blind_evaluation.json"
MARKDOWN_OUTPUT = PROJECT_DIR / "reports" / "granite_v05_v06_blind_evaluation.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def binary_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, object]:
    matrix = confusion_matrix(actual, predicted, labels=[False, True])
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "precision": float(precision_score(actual, predicted, zero_division=0)),
        "recall": float(recall_score(actual, predicted, zero_division=0)),
        "f1": float(f1_score(actual, predicted, zero_division=0)),
        "false_positive": int(matrix[0, 1]),
        "false_negative": int(matrix[1, 0]),
        "confusion_matrix": matrix.tolist(),
    }


def model_metrics(actual: pd.Series, predicted: pd.Series) -> dict[str, object]:
    actual_important = actual.ne("GENERAL").to_numpy()
    predicted_important = predicted.ne("GENERAL").to_numpy()
    observed_labels = [label for label in ACTIONABILITY_LABELS if actual.eq(label).any()]
    return {
        "three_class_accuracy": float(accuracy_score(actual, predicted)),
        "three_class_macro_f1": float(
            f1_score(actual, predicted, labels=ACTIONABILITY_LABELS, average="macro", zero_division=0)
        ),
        "observed_class_macro_f1": float(
            f1_score(actual, predicted, labels=observed_labels, average="macro", zero_division=0)
        ),
        "observed_labels": observed_labels,
        "three_class_confusion_matrix": confusion_matrix(
            actual, predicted, labels=ACTIONABILITY_LABELS
        ).tolist(),
        "important_binary": binary_metrics(actual_important, predicted_important),
    }


def paired_accuracy_interval(
    actual: np.ndarray, first: np.ndarray, second: np.ndarray
) -> dict[str, float]:
    rng = np.random.default_rng(20260815)
    differences = []
    for _ in range(10_000):
        indices = rng.integers(0, len(actual), len(actual))
        differences.append(
            (second[indices] == actual[indices]).mean()
            - (first[indices] == actual[indices]).mean()
        )
    low, high = np.percentile(differences, [2.5, 97.5])
    return {
        "v06_minus_v05": float((second == actual).mean() - (first == actual).mean()),
        "bootstrap_95_low": float(low),
        "bootstrap_95_high": float(high),
    }


def paired_important_f1_interval(
    actual: np.ndarray, first: np.ndarray, second: np.ndarray
) -> dict[str, float]:
    actual_binary = actual != "GENERAL"
    first_binary = first != "GENERAL"
    second_binary = second != "GENERAL"
    rng = np.random.default_rng(20260816)
    differences = []
    for _ in range(10_000):
        indices = rng.integers(0, len(actual), len(actual))
        differences.append(
            f1_score(
                actual_binary[indices], second_binary[indices], zero_division=0
            )
            - f1_score(
                actual_binary[indices], first_binary[indices], zero_division=0
            )
        )
    low, high = np.percentile(differences, [2.5, 97.5])
    return {
        "v06_minus_v05": float(
            f1_score(actual_binary, second_binary, zero_division=0)
            - f1_score(actual_binary, first_binary, zero_division=0)
        ),
        "bootstrap_95_low": float(low),
        "bootstrap_95_high": float(high),
    }


def mcnemar_exact(actual: np.ndarray, first: np.ndarray, second: np.ndarray) -> dict[str, float | int]:
    first_only = int(((first == actual) & (second != actual)).sum())
    second_only = int(((first != actual) & (second == actual)).sum())
    discordant = first_only + second_only
    if discordant == 0:
        p_value = 1.0
    else:
        tail = sum(
            math.comb(discordant, value)
            for value in range(0, min(first_only, second_only) + 1)
        ) / (2**discordant)
        p_value = min(1.0, 2 * tail)
    return {
        "v05_only_correct": first_only,
        "v06_only_correct": second_only,
        "two_sided_exact_p": p_value,
    }


def main() -> None:
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    expected_hash = metadata["artifacts"]["predictions_sha256"]
    if sha256(PREDICTIONS_PATH) != expected_hash:
        raise RuntimeError("봉인된 prediction 파일 SHA-256이 변경되었습니다.")

    labels = pd.read_csv(LABELS_PATH, dtype={"private_id": str}).fillna("")
    common_valid = labels["user_common_actionability"].isin(ACTIONABILITY_LABELS)
    personal_valid = labels["user_personal_preference"].isin({"GENERAL", "IMPORTANT"})
    if not (common_valid & personal_valid).all():
        complete = int((common_valid & personal_valid).sum())
        raise RuntimeError(f"블라인드 라벨이 {complete}/{len(labels)}개만 완료되었습니다.")

    predictions = pd.read_csv(PREDICTIONS_PATH, dtype={"private_id": str})
    data = labels.merge(
        predictions, on=["review_id", "private_id"], how="inner", validate="one_to_one"
    )
    if len(data) != len(labels):
        raise RuntimeError("라벨과 봉인 prediction의 행이 일치하지 않습니다.")

    results: dict[str, object] = {
        "status": "BLIND_EVALUATION_COMPLETE",
        "rows": len(data),
        "holdout_fingerprint": metadata["holdout_fingerprint"],
        "common_label_counts": data["user_common_actionability"].value_counts().to_dict(),
        "personal_label_counts": data["user_personal_preference"].value_counts().to_dict(),
    }
    unique = data.drop_duplicates(["package_name", "title", "body"], keep="first")
    results["deduplicated_rows"] = len(unique)
    for version in ("v05", "v06"):
        results[version] = {
            "common_model_raw": model_metrics(
                data["user_common_actionability"], data[f"{version}_actionability"]
            ),
            "common_model_deduplicated": model_metrics(
                unique["user_common_actionability"], unique[f"{version}_actionability"]
            ),
            "final_app_personal_binary_raw": binary_metrics(
                data["user_personal_preference"].eq("IMPORTANT").to_numpy(),
                data[f"{version}_final_level"].eq("IMPORTANT").to_numpy(),
            ),
            "final_app_personal_binary_deduplicated": binary_metrics(
                unique["user_personal_preference"].eq("IMPORTANT").to_numpy(),
                unique[f"{version}_final_level"].eq("IMPORTANT").to_numpy(),
            ),
            "final_level_counts": data[f"{version}_final_level"].value_counts().to_dict(),
        }

    actual = data["user_common_actionability"].to_numpy()
    v05 = data["v05_actionability"].to_numpy()
    v06 = data["v06_actionability"].to_numpy()
    results["paired_comparison"] = {
        "accuracy_difference": paired_accuracy_interval(actual, v05, v06),
        "important_f1_difference": paired_important_f1_interval(actual, v05, v06),
        "mcnemar": mcnemar_exact(actual, v05, v06),
    }

    data.to_csv(PRIVATE_RESULTS_PATH, index=False, encoding="utf-8-sig")
    JSON_OUTPUT.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# Granite v0.5/v0.6 블라인드 Room 평가",
        "",
        f"- 평가 행: {len(data)}개",
        f"- 봉인 fingerprint: `{metadata['holdout_fingerprint']}`",
        f"- 봉인 prediction SHA-256: `{expected_hash}`",
        "",
        "| 모델 | 3단계 정확도 | 등장 클래스 Macro F1 | 고정 3클래스 Macro F1 | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for version in ("v05", "v06"):
        value = results[version]["common_model_raw"]
        binary = value["important_binary"]
        lines.append(
            f"| {version} | {value['three_class_accuracy']:.3f} | "
            f"{value['observed_class_macro_f1']:.3f} | {value['three_class_macro_f1']:.3f} | "
            f"{binary['precision']:.3f} | "
            f"{binary['recall']:.3f} | {binary['f1']:.3f} | "
            f"{binary['false_positive']} | {binary['false_negative']} |"
        )
    lines.extend(
        [
            "",
            f"반복 제거 보조 평가 행: {len(unique)}개",
            "",
            "| 모델 | 반복 제거 3단계 정확도 | 반복 제거 Macro F1 |",
            "| --- | ---: | ---: |",
        ]
    )
    for version in ("v05", "v06"):
        value = results[version]["common_model_deduplicated"]
        lines.append(
            f"| {version} | {value['three_class_accuracy']:.3f} | "
            f"{value['three_class_macro_f1']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Kotlin 규칙과 결합한 최종 앱 개인 선호 이진 결과",
            "",
            "| 모델 | 정확도 | Precision | Recall | F1 | FP | FN |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for version in ("v05", "v06"):
        value = results[version]["final_app_personal_binary_raw"]
        lines.append(
            f"| {version} | {value['accuracy']:.3f} | {value['precision']:.3f} | "
            f"{value['recall']:.3f} | {value['f1']:.3f} | "
            f"{value['false_positive']} | {value['false_negative']} |"
        )
    difference = results["paired_comparison"]["accuracy_difference"]
    f1_difference = results["paired_comparison"]["important_f1_difference"]
    mcnemar = results["paired_comparison"]["mcnemar"]
    lines.extend(
        [
            "",
            f"v0.6-v0.5 정확도 차이: {difference['v06_minus_v05']:.3f} "
            f"(paired bootstrap 95% CI {difference['bootstrap_95_low']:.3f}~{difference['bootstrap_95_high']:.3f})",
            f"McNemar exact p={mcnemar['two_sided_exact_p']:.4f}",
            f"v0.6-v0.5 중요 F1 차이: {f1_difference['v06_minus_v05']:.3f} "
            f"(paired bootstrap 95% CI {f1_difference['bootstrap_95_low']:.3f}~{f1_difference['bootstrap_95_high']:.3f})",
            "",
            "`ACTION_REQUIRED` 정답이 0개이므로 고정 3클래스 Macro F1만으로 모델을 선택하지 않는다.",
            "",
        ]
    )
    MARKDOWN_OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
