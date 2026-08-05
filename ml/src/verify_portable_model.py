import json
import math
from collections import Counter
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_NAME = "noti_char_tfidf_logreg_v0.2"
PORTABLE_PATH = PROJECT_DIR / "models" / f"{MODEL_NAME}_portable.json"
REFERENCE_PATH = (
    PROJECT_DIR
    / "models"
    / f"{MODEL_NAME}_reference_predictions.json"
)


def create_char_ngrams(
    text: str,
    ngram_min: int,
    ngram_max: int,
) -> Counter[str]:
    counts: Counter[str] = Counter()
    for size in range(ngram_min, ngram_max + 1):
        for start in range(len(text) - size + 1):
            counts[text[start : start + size]] += 1
    return counts


def predict_probability(model: dict[str, object], text: str) -> float:
    vectorizer = model["vectorizer"]
    classifier = model["classifier"]

    if vectorizer["lowercase"]:
        text = text.lower()

    counts = create_char_ngrams(
        text,
        int(vectorizer["ngram_min"]),
        int(vectorizer["ngram_max"]),
    )
    vocabulary = vectorizer["vocabulary"]
    idf = vectorizer["idf"]
    coefficients = classifier["coefficients"]

    weighted_values: list[tuple[int, float]] = []
    squared_sum = 0.0

    for token, count in counts.items():
        index = vocabulary.get(token)
        if index is None:
            continue

        value = float(count) * float(idf[index])
        weighted_values.append((int(index), value))
        squared_sum += value * value

    norm = math.sqrt(squared_sum)
    decision = float(classifier["intercept"])

    if norm > 0.0:
        for index, value in weighted_values:
            decision += float(coefficients[index]) * (value / norm)

    if decision >= 0:
        negative_exp = math.exp(-decision)
        return 1.0 / (1.0 + negative_exp)

    positive_exp = math.exp(decision)
    return positive_exp / (1.0 + positive_exp)


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
                "Portable 모델 예측값이 기준과 다릅니다: "
                f"text={row['text']}, expected={expected}, "
                f"actual={actual}, difference={difference}"
            )

    print("Portable 모델 검증 완료")
    print(f"검증 알림: {len(reference['notifications'])}")
    print(f"최대 확률 차이: {maximum_difference:.3e}")
    print(f"허용 오차: {tolerance:.1e}")


if __name__ == "__main__":
    main()
