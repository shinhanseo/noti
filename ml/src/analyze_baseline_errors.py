from pathlib import Path
from statistics import pstdev

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
REPORT_PATH = PROJECT_DIR / "reports" / "v0.2_error_analysis.md"

INITIAL_BASELINE = {
    "accuracy": 0.7666666667,
    "errors": 56,
    "false_positive": 40,
    "false_negative": 16,
    "template_groups": 12,
    "fold_std": 0.243,
}


def markdown_table(
    headers: list[str],
    rows: list[list[object]],
) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]

    for row in rows:
        values = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(values) + " |")

    return lines


def load_model_data() -> pd.DataFrame:
    _, data = load_training_data()
    return data


def cross_validate(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    splitter = StratifiedGroupKFold(
        n_splits=5,
        shuffle=True,
        random_state=42,
    )

    predictions = np.zeros(len(data), dtype=int)
    probabilities = np.zeros(len(data), dtype=float)
    fold_numbers = np.zeros(len(data), dtype=int)
    fold_rows: list[dict[str, object]] = []

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

        vectorizer = create_vectorizer()
        train_vectors = vectorizer.fit_transform(train_data["text"])
        test_vectors = vectorizer.transform(test_data["text"])

        model = create_model()
        model.fit(train_vectors, train_data["label"])

        fold_predictions = model.predict(test_vectors)
        fold_probabilities = model.predict_proba(test_vectors)[:, 1]

        predictions[test_index] = fold_predictions
        probabilities[test_index] = fold_probabilities
        fold_numbers[test_index] = fold

        matrix = confusion_matrix(
            test_data["label"],
            fold_predictions,
            labels=[0, 1],
        )

        fold_rows.append(
            {
                "fold": fold,
                "test_count": len(test_data),
                "label_0": int((test_data["label"] == 0).sum()),
                "label_1": int((test_data["label"] == 1).sum()),
                "accuracy": accuracy_score(
                    test_data["label"],
                    fold_predictions,
                ),
                "false_positive": int(matrix[0, 1]),
                "false_negative": int(matrix[1, 0]),
                "test_groups": ", ".join(
                    sorted(test_data["template_group"].unique())
                ),
            }
        )

    results = data.copy()
    results["fold"] = fold_numbers
    results["prediction"] = predictions
    results["important_probability"] = probabilities
    results["is_correct"] = results["label"].eq(results["prediction"])
    results["error_type"] = "correct"
    results.loc[
        results["label"].eq(0) & results["prediction"].eq(1),
        "error_type",
    ] = "false_positive"
    results.loc[
        results["label"].eq(1) & results["prediction"].eq(0),
        "error_type",
    ] = "false_negative"
    results["confidence"] = (
        results["important_probability"] - 0.5
    ).abs()

    return results, pd.DataFrame(fold_rows)


def create_report(
    results: pd.DataFrame,
    fold_summary: pd.DataFrame,
) -> str:
    total = len(results)
    wrong = results[~results["is_correct"]].copy()
    false_positive = wrong[wrong["error_type"].eq("false_positive")]
    false_negative = wrong[wrong["error_type"].eq("false_negative")]
    accuracy = results["is_correct"].mean()
    fold_std = pstdev(fold_summary["accuracy"].tolist())
    template_group_count = results["template_group"].nunique()

    template_summary = (
        results.groupby(
            ["template_group", "label", "notification_type"],
            as_index=False,
        )
        .agg(
            count=("id", "size"),
            errors=("is_correct", lambda values: int((~values).sum())),
            average_probability=("important_probability", "mean"),
        )
    )
    template_summary["error_rate"] = (
        template_summary["errors"] / template_summary["count"]
    )
    template_summary = template_summary.sort_values(
        ["error_rate", "errors"],
        ascending=False,
    )

    type_summary = (
        results.groupby(
            ["notification_type", "label"],
            as_index=False,
        )
        .agg(
            count=("id", "size"),
            errors=("is_correct", lambda values: int((~values).sum())),
            average_probability=("important_probability", "mean"),
        )
    )
    type_summary["error_rate"] = type_summary["errors"] / type_summary["count"]
    type_summary = type_summary.sort_values(
        ["error_rate", "errors"],
        ascending=False,
    )

    app_summary = (
        results.groupby("app_name", as_index=False)
        .agg(
            count=("id", "size"),
            errors=("is_correct", lambda values: int((~values).sum())),
        )
    )
    app_summary["error_rate"] = app_summary["errors"] / app_summary["count"]
    app_summary = app_summary.sort_values(
        ["errors", "app_name"],
        ascending=[False, True],
    )

    high_confidence_errors = wrong.sort_values(
        "confidence",
        ascending=False,
    ).head(20)

    unstable_templates = template_summary[
        template_summary["error_rate"] >= 0.5
    ]

    lines = [
        "# v0.2 베이스라인 오분류 분석",
        "",
        "## 목적",
        "",
        "문자 n-gram TF-IDF와 Logistic Regression 베이스라인이 "
        "REVIEW 알림에서 틀리는 원인을 문장 템플릿, 알림 유형, 앱별로 분해한다.",
        "",
        "동일한 `template_group`은 학습과 평가에 동시에 들어가지 않으며, "
        "아래 결과는 5-Fold 교차 검증의 out-of-fold 예측만 사용한다.",
        "",
        "## 전체 결과",
        "",
        f"- 평가 데이터: {total}개",
        f"- 정확도: {accuracy:.1%}",
        f"- 전체 오분류: {len(wrong)}개",
        f"- 일반 알림을 중요로 판단한 false positive: {len(false_positive)}개",
        f"- 중요 알림을 일반으로 판단한 false negative: {len(false_negative)}개",
        f"- Template Group: {template_group_count}개",
        f"- Fold 정확도 표준편차: {fold_std:.3f}",
        "",
        "## 일정형 템플릿 확장 전후 비교",
        "",
        "모델과 평가 방법은 유지하고, 중요 일정과 선택 일정의 문장 구조만 "
        "각각 2개에서 5개로 늘렸다.",
        "",
    ]

    comparison_rows = [
        [
            "정확도",
            f"{INITIAL_BASELINE['accuracy']:.1%}",
            f"{accuracy:.1%}",
            f"{accuracy - INITIAL_BASELINE['accuracy']:+.1%}p",
        ],
        [
            "전체 오분류",
            INITIAL_BASELINE["errors"],
            len(wrong),
            len(wrong) - INITIAL_BASELINE["errors"],
        ],
        [
            "False Positive",
            INITIAL_BASELINE["false_positive"],
            len(false_positive),
            len(false_positive) - INITIAL_BASELINE["false_positive"],
        ],
        [
            "False Negative",
            INITIAL_BASELINE["false_negative"],
            len(false_negative),
            len(false_negative) - INITIAL_BASELINE["false_negative"],
        ],
        [
            "Template Group",
            INITIAL_BASELINE["template_groups"],
            template_group_count,
            template_group_count - INITIAL_BASELINE["template_groups"],
        ],
        [
            "Fold 정확도 표준편차",
            f"{INITIAL_BASELINE['fold_std']:.3f}",
            f"{fold_std:.3f}",
            f"{fold_std - INITIAL_BASELINE['fold_std']:+.3f}",
        ],
    ]

    lines.extend(
        markdown_table(
            ["지표", "확장 전", "확장 후", "변화"],
            comparison_rows,
        )
    )

    lines.extend(
        [
        "",
        "## Fold별 결과",
        "",
        ]
    )

    fold_rows = []
    for row in fold_summary.itertuples(index=False):
        fold_rows.append(
            [
                row.fold,
                row.test_count,
                f"{row.label_0}/{row.label_1}",
                f"{row.accuracy:.1%}",
                row.false_positive,
                row.false_negative,
                row.test_groups,
            ]
        )

    lines.extend(
        markdown_table(
            [
                "Fold",
                "평가 수",
                "Label 0/1",
                "정확도",
                "FP",
                "FN",
                "평가 Template Group",
            ],
            fold_rows,
        )
    )

    lines.extend(
        [
            "",
            "## Template Group별 오류",
            "",
        ]
    )

    template_rows = []
    for row in template_summary.itertuples(index=False):
        template_rows.append(
            [
                row.template_group,
                row.label,
                row.notification_type,
                row.count,
                row.errors,
                f"{row.error_rate:.1%}",
                f"{row.average_probability:.3f}",
            ]
        )

    lines.extend(
        markdown_table(
            [
                "Template Group",
                "Label",
                "유형",
                "개수",
                "오류",
                "오류율",
                "평균 중요 확률",
            ],
            template_rows,
        )
    )

    lines.extend(
        [
            "",
            "## 알림 유형별 오류",
            "",
        ]
    )

    type_rows = []
    for row in type_summary.itertuples(index=False):
        type_rows.append(
            [
                row.notification_type,
                row.label,
                row.count,
                row.errors,
                f"{row.error_rate:.1%}",
                f"{row.average_probability:.3f}",
            ]
        )

    lines.extend(
        markdown_table(
            [
                "알림 유형",
                "Label",
                "개수",
                "오류",
                "오류율",
                "평균 중요 확률",
            ],
            type_rows,
        )
    )

    lines.extend(
        [
            "",
            "## 앱별 오류",
            "",
        ]
    )

    app_rows = []
    for row in app_summary.itertuples(index=False):
        app_rows.append(
            [
                row.app_name,
                row.count,
                row.errors,
                f"{row.error_rate:.1%}",
            ]
        )

    lines.extend(
        markdown_table(
            ["앱", "개수", "오류", "오류율"],
            app_rows,
        )
    )

    lines.extend(
        [
            "",
            "## 확신이 큰 오분류 예시",
            "",
        ]
    )

    error_rows = []
    for row in high_confidence_errors.itertuples(index=False):
        error_rows.append(
            [
                row.id,
                row.app_name,
                row.title,
                row.label,
                row.prediction,
                f"{row.important_probability:.3f}",
                row.template_group,
            ]
        )

    lines.extend(
        markdown_table(
            [
                "ID",
                "앱",
                "제목",
                "정답",
                "예측",
                "중요 확률",
                "Template Group",
            ],
            error_rows,
        )
    )

    unstable_names = ", ".join(
        f"`{name}`"
        for name in unstable_templates["template_group"].tolist()
    )

    lines.extend(
        [
            "",
            "## 해석",
            "",
            f"- 오류율이 50% 이상인 Template Group: {unstable_names}",
            "- 일정형 문장을 각 라벨 5개 구조로 늘리자 정확도는 "
            f"{accuracy - INITIAL_BASELINE['accuracy']:.1%}p 상승하고 오분류는 "
            f"{INITIAL_BASELINE['errors'] - len(wrong)}개 감소했다.",
            "- Fold 정확도 표준편차도 0.243에서 "
            f"{fold_std:.3f}으로 줄어, 템플릿 구성에 따른 성능 변동이 완화됐다.",
            "- false positive가 false negative보다 많으므로 현재 모델은 "
            "일반 REVIEW 알림을 중요하다고 과하게 올리는 경향이 있다.",
            "- 앱별 데이터 수와 라벨은 동일하므로 앱 자체보다 문장 유형이 "
            "오류를 더 크게 설명한다.",
            "",
            "## 다음 데이터 보완 기준",
            "",
            "1. 오류율이 높은 알림 유형부터 서로 다른 문장 구조를 최소 5개 이상 추가한다.",
            "2. 시간·일정 표현이 있지만 중요하지 않은 hard negative를 늘린다.",
            "3. `긴급`, `실패`, `확인해주세요` 없이도 중요한 hard positive를 늘린다.",
            "4. 제목이 앱 이름뿐이고 핵심이 본문에만 있는 사례를 두 라벨에 고르게 추가한다.",
            "5. 모델 설정은 유지하고 데이터만 보완한 뒤 같은 교차 검증을 반복한다.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    data = load_model_data()
    results, fold_summary = cross_validate(data)
    report = create_report(results, fold_summary)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    wrong = results[~results["is_correct"]]
    print("v0.2 오분류 분석")
    print(f"평가 데이터: {len(results)}")
    print(f"정확도: {results['is_correct'].mean():.3f}")
    print(f"오분류: {len(wrong)}")
    print(
        "초기 베이스라인 대비 정확도: "
        f"{results['is_correct'].mean() - INITIAL_BASELINE['accuracy']:+.3f}"
    )
    print(
        "False Positive: "
        f"{int(wrong['error_type'].eq('false_positive').sum())}"
    )
    print(
        "False Negative: "
        f"{int(wrong['error_type'].eq('false_negative').sum())}"
    )
    print(f"보고서: {REPORT_PATH}")


if __name__ == "__main__":
    main()
