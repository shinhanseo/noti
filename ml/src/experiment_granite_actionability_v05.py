"""Run the common v0.5 thin-head experiment with Granite Embedding 97M R2."""

from __future__ import annotations

from pathlib import Path

import experiment_embeddinggemma_actionability_v05 as experiment


PROJECT_DIR = Path(__file__).resolve().parents[1]

experiment.MODEL_ID = (
    "ibm-granite/granite-embedding-97m-multilingual-r2"
)
experiment.CLASSIFICATION_PREFIX = ""
experiment.PRIVATE_OUTPUT_PATH = (
    experiment.PRIVATE_DIR / "granite_97m_actionability_predictions.csv"
)
experiment.REPORT_JSON_PATH = (
    PROJECT_DIR / "reports" / "granite_97m_actionability_v0.5.json"
)
experiment.REPORT_MARKDOWN_PATH = (
    PROJECT_DIR / "reports" / "granite_97m_actionability_v0.5.md"
)
experiment.MODEL_OUTPUT_DIR = (
    PROJECT_DIR / "models" / "granite_97m_actionability_v0.5"
)


if __name__ == "__main__":
    experiment.main()
