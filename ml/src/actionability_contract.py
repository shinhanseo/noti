"""Shared output contract for the three-tier on-device actionability model."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


MODEL_CONTRACT_VERSION = "actionability-triage-v1"
ACTIONABILITY_LABELS = (
    "GENERAL",
    "ATTENTION_WORTHY",
    "ACTION_REQUIRED",
)
ACTIONABILITY_TO_ID = {
    label: index for index, label in enumerate(ACTIONABILITY_LABELS)
}
IMPORTANT_ACTIONABILITIES = frozenset(
    {"ATTENTION_WORTHY", "ACTION_REQUIRED"}
)
SOURCE_TO_MODEL_ACTIONABILITY = {
    "PROMOTIONAL": "GENERAL",
    "INFORMATIONAL": "GENERAL",
    "ATTENTION_WORTHY": "ATTENTION_WORTHY",
    "ACTION_REQUIRED": "ACTION_REQUIRED",
}


def encode_actionability(values: Sequence[str]) -> np.ndarray:
    unknown = sorted(set(values) - set(SOURCE_TO_MODEL_ACTIONABILITY))
    if unknown:
        raise ValueError(f"알 수 없는 actionability 값: {unknown}")
    return np.asarray(
        [
            ACTIONABILITY_TO_ID[SOURCE_TO_MODEL_ACTIONABILITY[value]]
            for value in values
        ],
        dtype=np.int32,
    )


def softmax(logits: np.ndarray) -> np.ndarray:
    values = np.asarray(logits, dtype=np.float64)
    shifted = values - np.max(values, axis=-1, keepdims=True)
    exponentials = np.exp(shifted)
    return exponentials / np.sum(exponentials, axis=-1, keepdims=True)


def important_probabilities(probabilities: np.ndarray) -> np.ndarray:
    values = np.asarray(probabilities, dtype=np.float64)
    if values.shape[-1] != len(ACTIONABILITY_LABELS):
        raise ValueError(
            f"확률의 마지막 차원은 {len(ACTIONABILITY_LABELS)}여야 합니다: "
            f"{values.shape}"
        )
    return (
        values[..., ACTIONABILITY_TO_ID["ATTENTION_WORTHY"]]
        + values[..., ACTIONABILITY_TO_ID["ACTION_REQUIRED"]]
    )


def model_score_delta(important_probability: float) -> int:
    """Map important probability to the policy's bounded -15..15 score."""
    probability = float(important_probability)
    if not 0.0 <= probability <= 1.0:
        raise ValueError(f"확률은 0부터 1 사이여야 합니다: {probability}")
    if probability >= 0.80:
        return 15
    if probability >= 0.65:
        return 10
    if probability >= 0.35:
        return 0
    if probability >= 0.20:
        return -10
    return -15


def predicted_actionability(probabilities: np.ndarray) -> list[str]:
    values = np.asarray(probabilities)
    indices = np.argmax(values, axis=-1)
    return [ACTIONABILITY_LABELS[int(index)] for index in np.atleast_1d(indices)]


def probability_columns(probabilities: np.ndarray) -> dict[str, np.ndarray]:
    values = np.asarray(probabilities, dtype=np.float64)
    return {
        f"probability_{label.lower()}": values[:, index]
        for index, label in enumerate(ACTIONABILITY_LABELS)
    }
