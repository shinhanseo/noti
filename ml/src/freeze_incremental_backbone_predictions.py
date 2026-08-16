"""Freeze three model predictions before labeling the incremental Room holdout."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from actionability_contract import ACTIONABILITY_LABELS
from compare_frozen_backbones_v05 import MODELS, MODEL_DIR, get_embeddings
from notification_text_preprocessor import normalize_notification_text


PROJECT_DIR = Path(__file__).resolve().parents[1]
PRIVATE_DIR = PROJECT_DIR / "data" / "private" / "room_export_2026-08-16_raw"
HOLDOUT_PATH = PRIVATE_DIR / "incremental_holdout_review.csv"
OUTPUT_PATH = PRIVATE_DIR / "incremental_holdout_frozen_predictions.csv"
REPORT_PATH = PROJECT_DIR / "reports" / "incremental_predictions_freeze_2026-08-16.md"
LABEL_COLUMNS = ["user_common_actionability", "user_personal_preference"]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    holdout = pd.read_csv(HOLDOUT_PATH, dtype=str).fillna("")
    if holdout[LABEL_COLUMNS].ne("").any().any():
        raise ValueError("라벨이 이미 입력돼 예측 봉인을 중단합니다.")

    texts = [
        normalize_notification_text(package, title, body)
        for package, title, body in zip(
            holdout["package_name"], holdout["title"], holdout["body"]
        )
    ]
    output = holdout[["review_id", "private_id"]].copy()
    model_metadata: dict[str, object] = {}
    for config in MODELS:
        key = config["key"]
        print(f"{key} embedding")
        vectors, runtime = get_embeddings(config, texts)
        head_path = MODEL_DIR / f"{key}_mlp_32.joblib"
        if not head_path.exists():
            raise FileNotFoundError(f"학습된 Head가 없습니다: {head_path}")
        head = joblib.load(head_path)
        probabilities = np.asarray(head.predict_proba(vectors), dtype=np.float64)
        if probabilities.shape != (len(holdout), len(ACTIONABILITY_LABELS)):
            raise ValueError(f"예상하지 못한 확률 크기: {probabilities.shape}")
        for index, label in enumerate(ACTIONABILITY_LABELS):
            output[f"{key}_probability_{label.lower()}"] = probabilities[:, index]
        output[f"{key}_actionability"] = np.asarray(ACTIONABILITY_LABELS)[
            probabilities.argmax(axis=1)
        ]
        model_metadata[key] = {
            "model_id": config["model_id"],
            "head_sha256": file_sha256(head_path),
            "embedding_dimension": runtime["embedding_dimension"],
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    metadata = {
        "holdout_rows": len(holdout),
        "holdout_sha256": file_sha256(HOLDOUT_PATH),
        "predictions_sha256": file_sha256(OUTPUT_PATH),
        "models": model_metadata,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# 증분 Room 모델 예측 봉인",
                "",
                f"- 라벨 입력 전 행 수: {len(holdout)}개",
                f"- 검수 파일 SHA-256: `{metadata['holdout_sha256']}`",
                f"- 예측 파일 SHA-256: `{metadata['predictions_sha256']}`",
                "",
                "```json",
                json.dumps(metadata["models"], ensure_ascii=False, indent=2),
                "```",
                "",
                "세 모델의 예측 확률과 라벨을 사람의 정답 입력 전에 저장했다.",
                "평가 시 이 파일은 다시 생성하지 않고 봉인된 값을 그대로 사용한다.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(REPORT_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
