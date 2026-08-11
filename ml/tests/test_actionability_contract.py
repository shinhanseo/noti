"""Regression tests for the Android-facing actionability model contract."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from actionability_contract import (  # noqa: E402
    encode_actionability,
    important_probabilities,
    model_score_delta,
    predicted_actionability,
    softmax,
)


class ActionabilityContractTest(unittest.TestCase):
    def test_source_labels_are_merged_into_three_model_labels(self) -> None:
        encoded = encode_actionability(
            [
                "PROMOTIONAL",
                "INFORMATIONAL",
                "ATTENTION_WORTHY",
                "ACTION_REQUIRED",
            ]
        )
        np.testing.assert_array_equal(encoded, [0, 0, 1, 2])

    def test_important_probability_sums_attention_and_action(self) -> None:
        probabilities = np.asarray([[0.25, 0.30, 0.45]])
        np.testing.assert_allclose(important_probabilities(probabilities), [0.75])
        self.assertEqual(predicted_actionability(probabilities), ["ACTION_REQUIRED"])

    def test_score_boundaries_match_importance_policy(self) -> None:
        cases = {
            1.00: 15,
            0.80: 15,
            0.79: 10,
            0.65: 10,
            0.64: 0,
            0.35: 0,
            0.34: -10,
            0.20: -10,
            0.19: -15,
            0.00: -15,
        }
        for probability, expected in cases.items():
            with self.subTest(probability=probability):
                self.assertEqual(model_score_delta(probability), expected)

    def test_softmax_is_stable_for_large_logits(self) -> None:
        probabilities = softmax(np.asarray([[1000.0, 1001.0, 1002.0]]))
        np.testing.assert_allclose(probabilities.sum(axis=1), [1.0])

    def test_invalid_probability_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            model_score_delta(1.01)


if __name__ == "__main__":
    unittest.main()
