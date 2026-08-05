import argparse
import json
import tempfile
from pathlib import Path
from statistics import mean, pstdev
from typing import Callable

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    log_loss,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.naive_bayes import ComplementNB
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import FeatureUnion, Pipeline

from evaluate_stability import RANDOM_STATES
from train_baseline import create_model, create_vectorizer, load_training_data


PROJECT_DIR = Path(__file__).resolve().parents[1]


def make_candidates() -> dict[str, Callable[[], Pipeline]]:
    return {
        "char_tfidf_logreg": lambda: Pipeline(
            [
                ("features", create_vectorizer()),
                ("classifier", create_model()),
            ]
        ),
        "char_word_tfidf_logreg": lambda: Pipeline(
            [
                (
                    "features",
                    FeatureUnion(
                        [
                            ("char", create_vectorizer()),
                            (
                                "word",
                                TfidfVectorizer(
                                    analyzer="word",
                                    ngram_range=(1, 2),
                                    min_df=2,
                                ),
                            ),
                        ]
                    ),
                ),
                ("classifier", create_model()),
            ]
        ),
        "char_tfidf_sgd_log_loss": lambda: Pipeline(
            [
                ("features", create_vectorizer()),
                (
                    "classifier",
                    SGDClassifier(
                        loss="log_loss",
                        max_iter=2000,
                        tol=1e-4,
                        random_state=42,
                    ),
                ),
            ]
        ),
        "char_tfidf_complement_nb": lambda: Pipeline(
            [
                ("features", create_vectorizer()),
                ("classifier", ComplementNB(alpha=1.0)),
            ]
        ),
        "char_tfidf_mlp": lambda: Pipeline(
            [
                ("features", create_vectorizer()),
                (
                    "classifier",
                    MLPClassifier(
                        hidden_layer_sizes=(32,),
                        activation="relu",
                        alpha=0.0001,
                        max_iter=1000,
                        random_state=42,
                    ),
                ),
            ]
        ),
    }


def evaluate_candidate(
    data: pd.DataFrame,
    factory: Callable[[], Pipeline],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []

    for random_state in RANDOM_STATES:
        splitter = StratifiedGroupKFold(
            n_splits=5,
            shuffle=True,
            random_state=random_state,
        )
        predictions = np.full(len(data), -1, dtype=int)
        probabilities = np.full(len(data), -1.0, dtype=float)
        maximum_group_overlap = 0

        for train_index, test_index in splitter.split(
            data,
            y=data["label"],
            groups=data["template_group"],
        ):
            train_data = data.iloc[train_index]
            test_data = data.iloc[test_index]
            overlap = set(train_data["template_group"]) & set(
                test_data["template_group"]
            )
            maximum_group_overlap = max(
                maximum_group_overlap,
                len(overlap),
            )

            pipeline = factory()
            pipeline.fit(train_data["text"], train_data["label"])
            predictions[test_index] = pipeline.predict(test_data["text"])
            probabilities[test_index] = pipeline.predict_proba(
                test_data["text"]
            )[:, 1]

        if np.any(predictions < 0):
            raise RuntimeError("일부 데이터에 예측값이 생성되지 않았습니다.")
        if np.any(probabilities < 0.0):
            raise RuntimeError("일부 데이터에 확률값이 생성되지 않았습니다.")

        matrix = confusion_matrix(data["label"], predictions, labels=[0, 1])
        results.append(
            {
                "random_state": random_state,
                "accuracy": float(np.mean(predictions == data["label"])),
                "precision": precision_score(data["label"], predictions),
                "recall": recall_score(data["label"], predictions),
                "brier_score": brier_score_loss(
                    data["label"],
                    probabilities,
                ),
                "log_loss": log_loss(data["label"], probabilities),
                "false_positive": int(matrix[0, 1]),
                "false_negative": int(matrix[1, 0]),
                "maximum_group_overlap": maximum_group_overlap,
            }
        )

    return results


def fitted_artifact_size(
    data: pd.DataFrame,
    factory: Callable[[], Pipeline],
) -> tuple[int, int]:
    pipeline = factory()
    pipeline.fit(data["text"], data["label"])
    transformed = pipeline.named_steps["features"].transform(data["text"])

    with tempfile.NamedTemporaryFile(suffix=".joblib") as temporary:
        joblib.dump(pipeline, temporary.name, compress=3)
        size_bytes = Path(temporary.name).stat().st_size

    return size_bytes, int(transformed.shape[1])


def create_report(
    summaries: list[dict[str, object]],
    dataset_version: str,
    dataset_rows: int,
) -> str:
    lines = [
        f"# v{dataset_version} 경량 모델 Bake-off",
        "",
        "## 목적",
        "",
        f"동일한 검토 완료 REVIEW 데이터 {dataset_rows}개와 동일한 20개 "
        "`random_state`의 5-Fold `StratifiedGroupKFold`를 사용해 "
        "경량 분류 후보를 비교한다.",
        "",
        "## 요약",
        "",
        "| 순위 | 후보 | 평균 정확도 | 최저 정확도 | 평균 Precision | "
        "평균 Recall | Brier | Log Loss | 평균 FP | 평균 FN | "
        "전체 학습 Joblib | Feature |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for rank, row in enumerate(summaries, start=1):
        lines.append(
            f"| {rank} | `{row['name']}` | "
            f"{row['accuracy_mean']:.1%} | "
            f"{row['accuracy_min']:.1%} | "
            f"{row['precision_mean']:.3f} | "
            f"{row['recall_mean']:.3f} | "
            f"{row['brier_score_mean']:.3f} | "
            f"{row['log_loss_mean']:.3f} | "
            f"{row['false_positive_mean']:.1f} | "
            f"{row['false_negative_mean']:.1f} | "
            f"{row['joblib_size_bytes'] / 1024:.1f} KiB | "
            f"{row['feature_count']} |"
        )

    lines.extend(
        [
            "",
            "## 선정 원칙",
            "",
            "1. 합성 데이터 평균 정확도만으로 실제 최종 모델을 확정하지 않는다.",
            "2. 중요한 알림을 놓치는 False Negative와 Recall을 함께 본다.",
            "3. 전체 학습 모델 크기와 확률 출력 가능 여부를 함께 본다.",
            "4. Brier Score와 Log Loss는 낮을수록 확률 품질이 좋다.",
            "5. 실제 익명화 외부 평가 데이터가 생기면 동일 후보를 다시 비교한다.",
            "6. 이 표의 Joblib 크기는 Python 직렬화 크기이며 Android 앱 크기가 아니다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-version",
        default="0.2",
        choices=("0.2", "0.3"),
    )
    args = parser.parse_args()
    _, data = load_training_data(args.dataset_version)
    report_path = (
        PROJECT_DIR
        / "reports"
        / f"v{args.dataset_version}_lightweight_model_bakeoff.md"
    )
    result_path = (
        PROJECT_DIR
        / "reports"
        / f"v{args.dataset_version}_lightweight_model_bakeoff.json"
    )
    summaries: list[dict[str, object]] = []

    for name, factory in make_candidates().items():
        print(f"평가 시작: {name}")
        rows = evaluate_candidate(data, factory)
        size_bytes, feature_count = fitted_artifact_size(data, factory)
        accuracies = [float(row["accuracy"]) for row in rows]

        summary = {
            "name": name,
            "accuracy_mean": mean(accuracies),
            "accuracy_std": pstdev(accuracies),
            "accuracy_min": min(accuracies),
            "accuracy_max": max(accuracies),
            "precision_mean": mean(
                float(row["precision"])
                for row in rows
            ),
            "recall_mean": mean(float(row["recall"]) for row in rows),
            "brier_score_mean": mean(
                float(row["brier_score"])
                for row in rows
            ),
            "log_loss_mean": mean(
                float(row["log_loss"])
                for row in rows
            ),
            "false_positive_mean": mean(
                int(row["false_positive"])
                for row in rows
            ),
            "false_negative_mean": mean(
                int(row["false_negative"])
                for row in rows
            ),
            "maximum_group_overlap": max(
                int(row["maximum_group_overlap"])
                for row in rows
            ),
            "joblib_size_bytes": size_bytes,
            "feature_count": feature_count,
            "runs": rows,
        }
        summaries.append(summary)
        print(
            f"완료: {name}, "
            f"accuracy={summary['accuracy_mean']:.3f}, "
            f"recall={summary['recall_mean']:.3f}"
        )

    summaries.sort(
        key=lambda row: (
            row["accuracy_mean"],
            row["recall_mean"],
            -row["joblib_size_bytes"],
        ),
        reverse=True,
    )

    report_path.write_text(
        create_report(summaries, args.dataset_version, len(data)),
        encoding="utf-8",
    )
    result_path.write_text(
        json.dumps(
            {
                "dataset_version": args.dataset_version,
                "dataset_rows": len(data),
                "candidates": summaries,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"보고서: {report_path}")
    print(f"상세 결과: {result_path}")


if __name__ == "__main__":
    main()
