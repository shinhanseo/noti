import json
import math
from pathlib import Path

import numpy as np

from verify_portable_model import create_char_ngrams


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_NAME = "noti_char_tfidf_mlp_v0.2"
PORTABLE_PATH = PROJECT_DIR / "models" / f"{MODEL_NAME}_portable.json"
REFERENCE_PATH = (
    PROJECT_DIR
    / "models"
    / f"{MODEL_NAME}_reference_predictions.json"
)


def sigmoid(value: float) -> float:
    if value >= 0:
        negative_exp = math.exp(-value)
        return 1.0 / (1.0 + negative_exp)
    positive_exp = math.exp(value)
    return positive_exp / (1.0 + positive_exp)


def predict_probability(model: dict[str, object], text: str) -> float:
    vectorizer = model["vectorizer"]
    network = model["network"]

    if vectorizer["lowercase"]:
        text = text.lower()

    counts = create_char_ngrams(
        text,
        int(vectorizer["ngram_min"]),
        int(vectorizer["ngram_max"]),
    )
    vocabulary = vectorizer["vocabulary"]
    idf = vectorizer["idf"]
    feature_count = len(idf)
    features = np.zeros(feature_count, dtype=np.float64)

    for token, count in counts.items():
        index = vocabulary.get(token)
        if index is not None:
            features[int(index)] = float(count) * float(idf[index])

    norm = float(np.linalg.norm(features))
    if norm > 0.0:
        features /= norm

    values = features
    layers = network["layers"]

    for layer_index, layer in enumerate(layers):
        shape = tuple(int(value) for value in layer["weights_shape"])
        weights = np.asarray(
            layer["weights_row_major"],
            dtype=np.float64,
        ).reshape(shape)
        biases = np.asarray(layer["biases"], dtype=np.float64)
        values = values @ weights + biases

        if layer_index < len(layers) - 1:
            values = np.maximum(values, 0.0)

    return sigmoid(float(values[0]))


def main() -> None:
    model = json.loads(PORTABLE_PATH.read_text(encoding="utf-8"))
    reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    tolerance = float(reference["probability_tolerance"])
    maximum_difference = 0.0

    for row in reference["notifications"]:
        actual = predict_probability(model, row["text"])
        expected = float(row["important_probability"])
        difference = abs(actual - expected)
        maximum_difference = max(maximum_difference, difference)

        if difference > tolerance:
            raise RuntimeError(
                "Portable MLP 예측값이 기준과 다릅니다: "
                f"expected={expected}, actual={actual}, "
                f"difference={difference}, text={row['text']}"
            )

    print("선정 MLP Portable 모델 검증 완료")
    print(f"검증 알림: {len(reference['notifications'])}")
    print(f"최대 확률 차이: {maximum_difference:.3e}")
    print(f"허용 오차: {tolerance:.1e}")


if __name__ == "__main__":
    main()
