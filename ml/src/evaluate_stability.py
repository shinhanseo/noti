from pathlib import Path
from statistics import mean, pstdev

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold

from train_baseline import (
    create_model,
    create_vectorizer,
    load_training_data,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
REPORT_PATH = PROJECT_DIR / "reports" / "v0.2_stability_evaluation.md"
RANDOM_STATES = (*range(19), 42)
REFERENCE_RANDOM_STATE = 42


def evaluate_random_state(
    data: pd.DataFrame,
    random_state: int,
) -> dict[str, object]:
    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=random_state,
    )

    predictions = np.full(len(data), -1, dtype=int)
    fold_accuracies: list[float] = []
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
        maximum_group_overlap = max(maximum_group_overlap, len(overlap))

        vectorizer = create_vectorizer()
        train_vectors = vectorizer.fit_transform(train_data["text"])
        test_vectors = vectorizer.transform(test_data["text"])

        model = create_model()
        model.fit(train_vectors, train_data["label"])
        fold_predictions = model.predict(test_vectors)

        predictions[test_index] = fold_predictions
        fold_accuracies.append(
            accuracy_score(test_data["label"], fold_predictions)
        )

    if np.any(predictions < 0):
        raise RuntimeError("일부 데이터에 out-of-fold 예측이 생성되지 않았습니다.")

    matrix = confusion_matrix(data["label"], predictions, labels=[0, 1])

    return {
        "random_state": random_state,
        "accuracy": accuracy_score(data["label"], predictions),
        "errors": int((predictions != data["label"].to_numpy()).sum()),
        "false_positive": int(matrix[0, 1]),
        "false_negative": int(matrix[1, 0]),
        "fold_min": min(fold_accuracies),
        "fold_max": max(fold_accuracies),
        "fold_std": pstdev(fold_accuracies),
        "maximum_group_overlap": maximum_group_overlap,
    }


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend(
        "| " + " | ".join(str(value) for value in row) + " |"
        for row in rows
    )
    return "\n".join(lines)


def create_report(results: pd.DataFrame) -> str:
    accuracies = results["accuracy"].tolist()
    reference = results[
        results["random_state"].eq(REFERENCE_RANDOM_STATE)
    ].iloc[0]
    runs_at_least_90 = int((results["accuracy"] >= 0.9).sum())

    rows = []
    for row in results.itertuples(index=False):
        rows.append(
            [
                row.random_state,
                f"{row.accuracy:.1%}",
                row.errors,
                row.false_positive,
                row.false_negative,
                f"{row.fold_min:.1%}",
                f"{row.fold_max:.1%}",
                f"{row.fold_std:.3f}",
                row.maximum_group_overlap,
            ]
        )

    return "\n".join(
        [
            "# v0.2 반복 교차 검증 안정성 평가",
            "",
            "## 목적",
            "",
            "동일한 문자 n-gram TF-IDF와 Logistic Regression 모델을 유지한 채, "
            "`StratifiedGroupKFold`의 `random_state`만 20번 바꿔 성능이 "
            "특정 분할에 얼마나 의존하는지 확인한다.",
            "",
            "각 반복에서도 같은 `template_group`은 학습과 평가에 동시에 "
            "포함되지 않는다.",
            "",
            "## 요약",
            "",
            f"- 반복 횟수: {len(results)}회",
            f"- 평균 정확도: {mean(accuracies):.1%}",
            f"- 반복별 정확도 표준편차: {pstdev(accuracies):.3f}",
            f"- 최저 정확도: {min(accuracies):.1%}",
            f"- 최고 정확도: {max(accuracies):.1%}",
            f"- 평균 오분류: {results['errors'].mean():.1f}개",
            f"- 평균 False Positive: {results['false_positive'].mean():.1f}개",
            f"- 평균 False Negative: {results['false_negative'].mean():.1f}개",
            f"- 최대 Template Group 중복: {results['maximum_group_overlap'].max()}개",
            f"- 기존 random_state=42 정확도: {reference.accuracy:.1%}",
            f"- 정확도 90% 이상인 반복: {runs_at_least_90}/{len(results)}회",
            "",
            "## 반복별 결과",
            "",
            markdown_table(
                [
                    "random_state",
                    "정확도",
                    "오분류",
                    "FP",
                    "FN",
                    "Fold 최저",
                    "Fold 최고",
                    "Fold 표준편차",
                    "그룹 중복",
                ],
                rows,
            ),
            "",
            "## 해석할 때 주의할 점",
            "",
            "- 이 평가는 데이터 분할에 따른 변동을 확인하는 안정성 실험이다.",
            "- 20회 중 대부분은 90% 이상이지만 최저 결과가 83.3%이므로 "
            "분할 영향을 완전히 제거했다고 볼 수는 없다.",
            "- 같은 합성 데이터 240개를 반복 사용하므로 새로운 실제 알림에 "
            "대한 일반화 성능을 증명하지 않는다.",
            "- 평균 정확도와 범위가 안정적이어도 실제 익명화 알림 또는 별도 "
            "외부 평가 세트 검증이 필요하다.",
            "",
        ]
    )


def main() -> None:
    _, data = load_training_data()
    result_rows = [
        evaluate_random_state(data, random_state)
        for random_state in RANDOM_STATES
    ]
    results = pd.DataFrame(result_rows)

    report = create_report(results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print("v0.2 반복 교차 검증 안정성 평가")
    print(f"반복 횟수: {len(results)}")
    print(f"평균 정확도: {results['accuracy'].mean():.3f}")
    print(f"정확도 표준편차: {results['accuracy'].std(ddof=0):.3f}")
    print(
        "정확도 범위: "
        f"{results['accuracy'].min():.3f} ~ "
        f"{results['accuracy'].max():.3f}"
    )
    print(
        "최대 Template Group 중복: "
        f"{results['maximum_group_overlap'].max()}"
    )
    print(f"보고서: {REPORT_PATH}")


if __name__ == "__main__":
    main()
