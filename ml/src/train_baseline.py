import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)
from sklearn.model_selection import StratifiedGroupKFold


PROJECT_DIR = Path(__file__).resolve().parents[1]

DEFAULT_DATASET_VERSION = "0.2"


def dataset_paths(dataset_version: str) -> tuple[Path, Path]:
    public_dir = PROJECT_DIR / "data" / "public"
    return (
        public_dir / f"train_notifications_v{dataset_version}.csv",
        public_dir / f"context_notifications_v{dataset_version}.csv",
    )


def make_text(data: pd.DataFrame) -> pd.Series:
    return (
        data["title"].fillna("").str.strip()
        + " "
        + data["body"].fillna("").str.strip()
    )


def create_vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 5),
        min_df=2,
    )


def create_model() -> LogisticRegression:
    return LogisticRegression(
        max_iter=1000,
        random_state=42,
    )


def load_training_data(
    dataset_version: str = DEFAULT_DATASET_VERSION,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    data_path, _ = dataset_paths(dataset_version)
    all_data = pd.read_csv(data_path)

    model_eligible = (
        all_data["model_eligible"]
        .astype(str)
        .str.lower()
        .eq("true")
    )

    data = all_data[
        model_eligible
        & all_data["clarity"].eq("CLEAR")
    ].copy()

    data["text"] = make_text(data)
    data = data.reset_index(drop=True)

    return all_data, data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset-version",
        default=DEFAULT_DATASET_VERSION,
        choices=("0.2", "0.3"),
    )
    args = parser.parse_args()
    all_data, data = load_training_data(args.dataset_version)

    print(f"v{args.dataset_version} 전체 학습·대조 데이터")
    print(all_data.shape)

    print("\n실제 모델 학습 대상")
    print(data.shape)

    print("\n학습 대상 Label")
    print(data["label"].value_counts().sort_index())

    print("\n학습 대상 앱 개수")
    print(data["app_name"].nunique())

    print("\n학습 대상 Template Group 개수")
    print(data["template_group"].nunique())

    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    predictions = np.zeros(len(data), dtype=int)
    important_probabilities = np.zeros(len(data), dtype=float)

    print("\n교차 검증 Fold")

    for fold, (train_index, test_index) in enumerate(
        splitter.split(
            data,
            y=data["label"],
            groups=data["template_group"],
        ),
        start=1,
    ):
        train_data = data.iloc[train_index]
        test_data = data.iloc[test_index]

        train_groups = set(train_data["template_group"])
        test_groups = set(test_data["template_group"])
        overlapping_groups = train_groups & test_groups

        vectorizer = create_vectorizer()
        train_vectors = vectorizer.fit_transform(
            train_data["text"]
        )
        test_vectors = vectorizer.transform(
            test_data["text"]
        )

        model = create_model()
        model.fit(
            train_vectors,
            train_data["label"],
        )

        fold_predictions = model.predict(test_vectors)
        fold_probabilities = model.predict_proba(
            test_vectors
        )[:, 1]

        predictions[test_index] = fold_predictions
        important_probabilities[test_index] = fold_probabilities

        fold_accuracy = accuracy_score(
            test_data["label"],
            fold_predictions,
        )

        print(
            f"Fold {fold}: "
            f"train={len(train_data)}, "
            f"test={len(test_data)}, "
            f"accuracy={fold_accuracy:.3f}, "
            f"group_overlap={len(overlapping_groups)}"
        )

    print("\n전체 교차 검증 정확도")
    print(
        accuracy_score(
            data["label"],
            predictions,
        )
    )

    print("\n혼동 행렬")
    print(
        confusion_matrix(
            data["label"],
            predictions,
        )
    )

    print("\n분류 결과")
    print(
        classification_report(
            data["label"],
            predictions,
            digits=3,
        )
    )

    results = data[
        [
            "id",
            "app_name",
            "title",
            "body",
            "label",
            "template_group",
        ]
    ].copy()

    results["prediction"] = predictions
    results["important_probability"] = important_probabilities
    results["uncertainty"] = (
        results["important_probability"] - 0.5
    ).abs()

    wrong_results = results[
        results["label"] != results["prediction"]
    ].copy()

    print("\n오분류 개수")
    print(len(wrong_results))

    if not wrong_results.empty:
        print("\n오분류 예시")
        print(
            wrong_results.sort_values(
                "uncertainty",
                ascending=False,
            )[
                [
                    "id",
                    "app_name",
                    "title",
                    "label",
                    "prediction",
                    "important_probability",
                ]
            ].head(20).to_string(index=False)
        )

    print("\n모델이 가장 애매하게 판단한 학습 대상")
    print(
        results.sort_values("uncertainty")
        [
            [
                "id",
                "app_name",
                "title",
                "label",
                "prediction",
                "important_probability",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )

    final_vectorizer = create_vectorizer()
    final_vectors = final_vectorizer.fit_transform(
        data["text"]
    )

    final_model = create_model()
    final_model.fit(
        final_vectors,
        data["label"],
    )

    print("\n최종 Vocabulary 크기")
    print(len(final_vectorizer.get_feature_names_out()))

    _, context_data_path = dataset_paths(args.dataset_version)
    context_data = pd.read_csv(context_data_path)
    context_data["text"] = make_text(context_data)

    context_vectors = final_vectorizer.transform(
        context_data["text"]
    )

    context_data["important_probability"] = (
        final_model.predict_proba(context_vectors)[:, 1]
    )
    context_data["prediction"] = (
        context_data["important_probability"] >= 0.5
    ).astype(int)
    context_data["uncertainty"] = (
        context_data["important_probability"] - 0.5
    ).abs()

    print("\n문맥 의존 데이터 중 가장 애매한 알림")
    print(
        context_data.sort_values("uncertainty")
        [
            [
                "id",
                "app_name",
                "title",
                "body",
                "prediction",
                "important_probability",
            ]
        ]
        .head(15)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
