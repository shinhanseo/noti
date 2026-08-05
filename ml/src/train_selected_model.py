import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline

from train_baseline import create_vectorizer, load_training_data
from train_final_model import (
    REFERENCE_NOTIFICATIONS,
    make_notification_text,
    sha256,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_DIR / "models"
MODEL_NAME = "noti_char_tfidf_mlp_v0.2"
JOBLIB_PATH = MODEL_DIR / f"{MODEL_NAME}.joblib"
PORTABLE_PATH = MODEL_DIR / f"{MODEL_NAME}_portable.json"
METADATA_PATH = MODEL_DIR / f"{MODEL_NAME}_metadata.json"
REFERENCE_PATH = MODEL_DIR / f"{MODEL_NAME}_reference_predictions.json"
BAKEOFF_RESULT_PATH = (
    PROJECT_DIR / "reports" / "v0.2_lightweight_model_bakeoff.json"
)


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", create_vectorizer()),
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
    )


def float32_flat(values: np.ndarray) -> list[float]:
    return values.astype(np.float32).ravel().astype(float).tolist()


def export_portable_model(pipeline: Pipeline) -> None:
    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["classifier"]
    layers = []

    for weights, biases in zip(
        classifier.coefs_,
        classifier.intercepts_,
        strict=True,
    ):
        layers.append(
            {
                "weights_shape": list(weights.shape),
                "weights_row_major": float32_flat(weights),
                "biases": float32_flat(biases),
            }
        )

    portable = {
        "schema_version": 1,
        "model_name": MODEL_NAME,
        "model_type": "char_tfidf_mlp",
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
            "vocabulary": {
                token: int(index)
                for token, index in vectorizer.vocabulary_.items()
            },
            "idf": float32_flat(vectorizer.idf_),
        },
        "network": {
            "hidden_activation": classifier.activation,
            "output_activation": classifier.out_activation_,
            "classes": classifier.classes_.astype(int).tolist(),
            "positive_class": 1,
            "decision_threshold": 0.5,
            "layers": layers,
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

    REFERENCE_PATH.write_text(
        json.dumps(
            {
                "model_name": MODEL_NAME,
                "probability_tolerance": 1e-6,
                "notifications": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def find_bakeoff_result() -> dict[str, object]:
    result = json.loads(BAKEOFF_RESULT_PATH.read_text(encoding="utf-8"))
    for candidate in result["candidates"]:
        if candidate["name"] == "char_tfidf_mlp":
            return {
                key: value
                for key, value in candidate.items()
                if key != "runs"
            }
    raise RuntimeError("Bake-off 결과에서 char_tfidf_mlp를 찾지 못했습니다.")


def main() -> None:
    _, data = load_training_data()
    pipeline = build_pipeline()
    pipeline.fit(data["text"], data["label"])

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, JOBLIB_PATH, compress=3)

    loaded = joblib.load(JOBLIB_PATH)
    before = pipeline.predict_proba(data["text"])[:, 1]
    after = loaded.predict_proba(data["text"])[:, 1]
    reload_max_difference = float(np.max(np.abs(before - after)))

    if reload_max_difference > 1e-12:
        raise RuntimeError(
            "저장 전후 예측값이 일치하지 않습니다: "
            f"{reload_max_difference}"
        )

    export_portable_model(pipeline)
    export_reference_predictions(pipeline)

    vectorizer = pipeline.named_steps["tfidf"]
    classifier = pipeline.named_steps["classifier"]
    metadata = {
        "status": "provisional_best_on_synthetic_v0.2",
        "model_name": MODEL_NAME,
        "model_type": "char_tfidf_mlp",
        "dataset_version": "0.2",
        "training_rows": len(data),
        "feature_count": len(vectorizer.vocabulary_),
        "hidden_layer_sizes": list(classifier.hidden_layer_sizes),
        "bakeoff": find_bakeoff_result(),
        "artifacts": {
            "joblib": JOBLIB_PATH.name,
            "portable": PORTABLE_PATH.name,
            "reference_predictions": REFERENCE_PATH.name,
        },
        "integrity": {
            "joblib_sha256": sha256(JOBLIB_PATH),
            "portable_sha256": sha256(PORTABLE_PATH),
            "reload_max_probability_difference": reload_max_difference,
        },
        "limitations": [
            "현재 1위는 합성 v0.2 데이터에서의 임시 선정 결과다.",
            "Pretrained embedding 모델과 실제 익명화 외부 평가를 아직 비교하지 않았다.",
            "Android 성능과 배터리는 이 모델 선정 범위에 포함되지 않았다.",
        ],
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("합성 v0.2 임시 최우수 모델 저장 완료")
    print(f"모델: {MODEL_NAME}")
    print(f"학습 데이터: {len(data)}")
    print(f"Feature: {len(vectorizer.vocabulary_)}")
    print(f"저장 전후 최대 확률 차이: {reload_max_difference:.3e}")
    print(f"Joblib: {JOBLIB_PATH}")
    print(f"Portable: {PORTABLE_PATH}")
    print(f"Metadata: {METADATA_PATH}")


if __name__ == "__main__":
    main()
