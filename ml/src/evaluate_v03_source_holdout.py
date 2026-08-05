import json
from pathlib import Path
from statistics import mean

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    log_loss,
    precision_score,
    recall_score,
)

from compare_lightweight_models import make_candidates
from train_baseline import load_training_data


PROJECT_DIR = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_DIR / "reports" / "v0.3_source_holdout.md"
RESULT_PATH = PROJECT_DIR / "reports" / "v0.3_source_holdout.json"


def evaluate(
    train_data: pd.DataFrame,
    test_data: pd.DataFrame,
    candidate_name: str,
) -> dict[str, object]:
    pipeline = make_candidates()[candidate_name]()
    pipeline.fit(train_data["text"], train_data["label"])
    predictions = pipeline.predict(test_data["text"])
    probabilities = pipeline.predict_proba(test_data["text"])[:, 1]
    matrix = confusion_matrix(test_data["label"], predictions, labels=[0, 1])
    return {
        "candidate": candidate_name,
        "train_rows": len(train_data),
        "test_rows": len(test_data),
        "accuracy": float(accuracy_score(test_data["label"], predictions)),
        "precision": float(precision_score(test_data["label"], predictions)),
        "recall": float(recall_score(test_data["label"], predictions)),
        "brier_score": float(brier_score_loss(test_data["label"], probabilities)),
        "log_loss": float(log_loss(test_data["label"], probabilities)),
        "false_positive": int(matrix[0, 1]),
        "false_negative": int(matrix[1, 0]),
    }


def table(rows: list[dict[str, object]]) -> list[str]:
    lines = [
        "| 후보 | 정확도 | Precision | Recall | Brier | FP | FN |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['candidate']}` | {row['accuracy']:.1%} | "
            f"{row['precision']:.3f} | {row['recall']:.3f} | "
            f"{row['brier_score']:.3f} | {row['false_positive']} | "
            f"{row['false_negative']} |"
        )
    return lines


def create_report(
    forward: list[dict[str, object]],
    reverse: list[dict[str, object]],
) -> str:
    return "\n".join(
        [
            "# v0.3 데이터 출처 홀드아웃",
            "",
            "## 목적",
            "",
            "생성 출처가 다른 문장을 학습과 평가에 섞지 않고, 한쪽에서 배운 "
            "분류 기준이 다른 문장 스타일로 이동하는지 확인한다.",
            "",
            "## v0.2 합성 240개 학습 → v0.3 현실형 신규 160개 평가",
            "",
            *table(forward),
            "",
            "## v0.3 현실형 신규 160개 학습 → v0.2 합성 240개 평가",
            "",
            *table(reverse),
            "",
            "## 해석 제한",
            "",
            "- 두 출처 모두 직접 생성한 합성 데이터이므로 실제 사용자 성능은 아니다.",
            "- 이 평가는 무작위 Fold 점수보다 문장 스타일 변화에 더 엄격하다.",
            "- 실제 Room 데이터는 라벨 검토 후 학습과 완전히 분리한 외부 평가로 사용한다.",
            "",
        ]
    )


def main() -> None:
    _, data = load_training_data("0.3")
    old_data = data[data["source"].eq("SYNTHETIC_REVIEWED")].copy()
    realistic_data = data[
        data["source"].eq("SYNTHETIC_REALISTIC_REVIEWED")
    ].copy()
    if len(old_data) != 240 or len(realistic_data) != 160:
        raise RuntimeError(
            f"예상하지 못한 출처 구성: old={len(old_data)}, "
            f"realistic={len(realistic_data)}"
        )

    candidate_names = list(make_candidates())
    forward = [
        evaluate(old_data, realistic_data, name) for name in candidate_names
    ]
    reverse = [
        evaluate(realistic_data, old_data, name) for name in candidate_names
    ]
    forward.sort(key=lambda row: (row["accuracy"], row["recall"]), reverse=True)
    reverse.sort(key=lambda row: (row["accuracy"], row["recall"]), reverse=True)

    payload = {
        "dataset_version": "0.3",
        "forward": {
            "train_source": "SYNTHETIC_REVIEWED",
            "test_source": "SYNTHETIC_REALISTIC_REVIEWED",
            "results": forward,
        },
        "reverse": {
            "train_source": "SYNTHETIC_REALISTIC_REVIEWED",
            "test_source": "SYNTHETIC_REVIEWED",
            "results": reverse,
        },
        "mean_forward_accuracy": mean(row["accuracy"] for row in forward),
        "mean_reverse_accuracy": mean(row["accuracy"] for row in reverse),
    }
    REPORT_PATH.write_text(create_report(forward, reverse), encoding="utf-8")
    RESULT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("v0.3 출처 홀드아웃 완료")
    for row in forward:
        print(
            f"{row['candidate']}: accuracy={row['accuracy']:.3f}, "
            f"recall={row['recall']:.3f}"
        )
    print(f"보고서: {REPORT_PATH}")


if __name__ == "__main__":
    main()
