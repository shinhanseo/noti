import hashlib
import json
from pathlib import Path
from statistics import mean, pstdev

import joblib
import numpy as np
from sklearn.metrics import confusion_matrix
from sklearn.pipeline import Pipeline

from analyze_baseline_errors import cross_validate
from evaluate_stability import RANDOM_STATES, evaluate_random_state
from train_baseline import (
    DATA_PATH,
    create_model,
    create_vectorizer,
    load_training_data,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_DIR / "models"
MODEL_NAME = "noti_char_tfidf_logreg_v0.2"
JOBLIB_PATH = MODEL_DIR / f"{MODEL_NAME}.joblib"
PORTABLE_PATH = MODEL_DIR / f"{MODEL_NAME}_portable.json"
METADATA_PATH = MODEL_DIR / f"{MODEL_NAME}_metadata.json"
REFERENCE_PATH = MODEL_DIR / f"{MODEL_NAME}_reference_predictions.json"

REFERENCE_NOTIFICATIONS = [
    {
        "title": "결제 상태 안내",
        "body": "자동이체 처리 중 문제가 발생했습니다.",
    },
    {
        "title": "예약 변경",
        "body": "예약 시간이 내일 오전 9시로 변경되었습니다.",
    },
    {
        "title": "확인 요청",
        "body": "등록된 결제 수단을 다시 확인해주세요.",
    },
    {
        "title": "배송 안내",
        "body": "주문한 상품이 오늘 오후 도착할 예정입니다.",
    },
    {
        "title": "쿠폰 도착",
        "body": "오늘까지 사용할 수 있는 할인 쿠폰입니다.",
    },
    {
        "title": "콘텐츠 소식",
        "body": "관심 등록한 콘텐츠가 이번 주 공개될 예정입니다.",
    },
    {
        "title": "일정 알림",
        "body": "등록한 일정이 한 시간 후 시작됩니다.",
    },
    {
        "title": "오늘의집",
        "body": "설치 배송 일정이 예정보다 앞당겨졌습니다.",
    },
]


def make_notification_text(title: str, body: str) -> str:
    return f"{title.strip()} {body.strip()}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", create_vectorizer()),
            ("classifier", create_model()),
        ]
    )


def export_portable_model(pipeline: Pipeline) -> None:
    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["classifier"]

    portable = {
        "schema_version": 1,
        "model_name": MODEL_NAME,
        "model_type": "char_tfidf_logistic_regression",
        "input": {
            "fields": ["title", "body"],
            "separator": " ",
            "strip_whitespace": True,
        },
        "vectorizer": {
            "analyzer": "char",
            "lowercase": bool(vectorizer.lowercase),
            "ngram_min": int(vectorizer.ngram_range[0]),
            "ngram_max": int(vectorizer.ngram_range[1]),
            "min_df": int(vectorizer.min_df),
            "norm": vectorizer.norm,
            "sublinear_tf": bool(vectorizer.sublinear_tf),
            "vocabulary": {
                token: int(index)
                for token, index in vectorizer.vocabulary_.items()
            },
            "idf": vectorizer.idf_.astype(float).tolist(),
        },
        "classifier": {
            "classes": classifier.classes_.astype(int).tolist(),
            "positive_class": 1,
            "decision_threshold": 0.5,
            "coefficients": classifier.coef_[0].astype(float).tolist(),
            "intercept": float(classifier.intercept_[0]),
        },
    }

    PORTABLE_PATH.write_text(
        json.dumps(portable, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def export_reference_predictions(pipeline: Pipeline) -> None:
    texts = [
        make_notification_text(row["title"], row["body"])
        for row in REFERENCE_NOTIFICATIONS
    ]
    probabilities = pipeline.predict_proba(texts)[:, 1]

    rows = []
    for notification, probability in zip(
        REFERENCE_NOTIFICATIONS,
        probabilities,
        strict=True,
    ):
        rows.append(
            {
                **notification,
                "text": make_notification_text(
                    notification["title"],
                    notification["body"],
                ),
                "important_probability": float(probability),
                "prediction": int(probability >= 0.5),
            }
        )

    reference = {
        "model_name": MODEL_NAME,
        "probability_tolerance": 1e-9,
        "notifications": rows,
    }
    REFERENCE_PATH.write_text(
        json.dumps(reference, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    _, data = load_training_data()
    pipeline = build_pipeline()
    pipeline.fit(data["text"], data["label"])

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, JOBLIB_PATH, compress=3)

    loaded_pipeline = joblib.load(JOBLIB_PATH)
    before = pipeline.predict_proba(data["text"])[:, 1]
    after = loaded_pipeline.predict_proba(data["text"])[:, 1]
    reload_max_difference = float(np.max(np.abs(before - after)))

    if reload_max_difference > 1e-12:
        raise RuntimeError(
            "저장 전후 예측값이 일치하지 않습니다: "
            f"{reload_max_difference}"
        )

    seed_42_results, seed_42_folds = cross_validate(data)
    seed_42_wrong = seed_42_results[~seed_42_results["is_correct"]]
    seed_42_matrix = confusion_matrix(
        seed_42_results["label"],
        seed_42_results["prediction"],
        labels=[0, 1],
    )

    stability_rows = [
        evaluate_random_state(data, random_state)
        for random_state in RANDOM_STATES
    ]
    stability_accuracies = [
        float(row["accuracy"])
        for row in stability_rows
    ]

    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["classifier"]

    export_portable_model(pipeline)
    export_reference_predictions(pipeline)

    metadata = {
        "model_name": MODEL_NAME,
        "model_type": "char_tfidf_logistic_regression",
        "dataset_version": "0.2",
        "training_rows": len(data),
        "label_counts": {
            str(label): int(count)
            for label, count in data["label"].value_counts().sort_index().items()
        },
        "template_group_count": int(data["template_group"].nunique()),
        "feature_count": int(len(vectorizer.vocabulary_)),
        "parameters": {
            "analyzer": "char",
            "ngram_range": list(vectorizer.ngram_range),
            "min_df": int(vectorizer.min_df),
            "logistic_regression_max_iter": int(classifier.max_iter),
        },
        "evaluation": {
            "method": "StratifiedGroupKFold",
            "folds": len(seed_42_folds),
            "random_state_42_accuracy": float(
                seed_42_results["is_correct"].mean()
            ),
            "random_state_42_errors": int(len(seed_42_wrong)),
            "random_state_42_confusion_matrix": seed_42_matrix.tolist(),
            "repeated_random_state_count": len(stability_rows),
            "repeated_accuracy_mean": mean(stability_accuracies),
            "repeated_accuracy_std": pstdev(stability_accuracies),
            "repeated_accuracy_min": min(stability_accuracies),
            "repeated_accuracy_max": max(stability_accuracies),
        },
        "artifacts": {
            "joblib": JOBLIB_PATH.name,
            "portable": PORTABLE_PATH.name,
            "reference_predictions": REFERENCE_PATH.name,
        },
        "integrity": {
            "training_data_sha256": sha256(DATA_PATH),
            "joblib_sha256": sha256(JOBLIB_PATH),
            "portable_sha256": sha256(PORTABLE_PATH),
            "reload_max_probability_difference": reload_max_difference,
        },
        "limitations": [
            "합성 데이터 성능이며 실제 사용자 알림 성능이 아니다.",
            "확률 보정을 별도로 수행하지 않았다.",
            "joblib 파일은 신뢰할 수 있는 환경에서만 로드해야 한다.",
        ],
    }

    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("최종 모델 학습 및 저장 완료")
    print(f"학습 데이터: {len(data)}")
    print(f"Vocabulary: {len(vectorizer.vocabulary_)}")
    print(f"저장 전후 최대 확률 차이: {reload_max_difference:.3e}")
    print(f"Joblib: {JOBLIB_PATH}")
    print(f"Portable: {PORTABLE_PATH}")
    print(f"Metadata: {METADATA_PATH}")
    print(f"Reference: {REFERENCE_PATH}")


if __name__ == "__main__":
    main()
