"""Freeze v0.5/v0.6 heads and blind predictions before labels are revealed."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

import experiment_embeddinggemma_actionability_v05 as experiment
from actionability_contract import (
    ACTIONABILITY_LABELS,
    important_probabilities,
    model_score_delta,
    predicted_actionability,
)
from compare_granite_v05_v06_active_learning import MODEL_ID, embed_all
from notification_text_preprocessor import PREPROCESSING_VERSION, normalize_notification_text
from prepare_active_learning_review import DEFAULT_DATABASE, DEFAULT_REPLAY, load_room


PROJECT_DIR = Path(__file__).resolve().parents[1]
V05_PATH = PROJECT_DIR / "data" / "public" / "train_notifications_v0.5.csv"
V06_PATH = PROJECT_DIR / "data" / "public" / "train_notifications_v0.6.csv"
PRIVATE_DIR = PROJECT_DIR / "data" / "private" / "room_export_2026-08-12_raw"
HOLDOUT_PATH = PRIVATE_DIR / "blind_holdout_review_100.csv"
PREDICTIONS_PATH = PRIVATE_DIR / "blind_holdout_frozen_predictions_v05_v06.csv"
MODEL_DIR = PROJECT_DIR / "models" / "granite_v05_v06_blind_freeze"
METADATA_PATH = MODEL_DIR / "freeze_metadata.json"
REPORT_PATH = PROJECT_DIR / "reports" / "granite_v05_v06_blind_freeze.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fit(data: pd.DataFrame, vectors: np.ndarray) -> object:
    head = experiment.make_head("mlp_32")
    labels = data["actionability_id"].to_numpy(dtype=np.int32)
    experiment.fit_head(head, "mlp_32", vectors, labels)
    return head


def final_level(rule_score: int, rule_level: str, probability: float) -> str:
    score = rule_score
    if rule_level == "REVIEW":
        score += model_score_delta(probability)
    if score >= 40:
        return "IMPORTANT"
    if score >= 25:
        return "REVIEW"
    return "GENERAL"


def main() -> None:
    holdout = pd.read_csv(HOLDOUT_PATH, dtype={"private_id": str}).fillna("")
    if holdout[["user_common_actionability", "user_personal_preference"]].ne("").any().any():
        raise RuntimeError("라벨이 이미 입력되어 있어 blind prediction을 봉인할 수 없습니다.")
    holdout["text"] = [
        normalize_notification_text(package, title, body)
        for package, title, body in zip(
            holdout["package_name"], holdout["title"], holdout["body"]
        )
    ]
    v05 = experiment.load_training_data(V05_PATH)
    v06 = experiment.load_training_data(V06_PATH)
    vectors = embed_all(v05, v06, holdout)
    heads = {
        "v05": fit(v05, vectors["v05"]),
        "v06": fit(v06, vectors["v06"]),
    }

    room = load_room(DEFAULT_DATABASE, DEFAULT_REPLAY).set_index("private_id")
    output = holdout[["review_id", "private_id"]].copy()
    output["rule_score_v2"] = output["private_id"].map(room["rule_score_v2"])
    output["rule_level_v2"] = output["private_id"].map(room["rule_level_v2"])
    for version, head in heads.items():
        probabilities = head.predict_proba(vectors["active"])
        important = important_probabilities(probabilities)
        for index, label in enumerate(ACTIONABILITY_LABELS):
            output[f"{version}_probability_{label.lower()}"] = probabilities[:, index]
        output[f"{version}_actionability"] = predicted_actionability(probabilities)
        output[f"{version}_important_probability"] = important
        output[f"{version}_model_score_delta"] = [
            model_score_delta(value) for value in important
        ]
        output[f"{version}_final_level"] = [
            final_level(int(score), str(level), float(probability))
            for score, level, probability in zip(
                output["rule_score_v2"], output["rule_level_v2"], important
            )
        ]

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(heads["v05"], MODEL_DIR / "granite_mlp_v05.joblib")
    joblib.dump(heads["v06"], MODEL_DIR / "granite_mlp_v06.joblib")
    output.to_csv(PREDICTIONS_PATH, index=False, encoding="utf-8-sig")
    holdout_fingerprint = hashlib.sha256(
        "\n".join(holdout["private_id"]).encode("utf-8")
    ).hexdigest()
    metadata = {
        "status": "FROZEN_BEFORE_LABELING",
        "model_id": MODEL_ID,
        "head": "MLPClassifier(hidden_layer_sizes=(32,), random_state=42)",
        "preprocessing_version": PREPROCESSING_VERSION,
        "label_order": list(ACTIONABILITY_LABELS),
        "holdout_rows": len(holdout),
        "holdout_fingerprint": holdout_fingerprint,
        "training_data": {
            "v0.5": {"rows": len(v05), "sha256": sha256(V05_PATH)},
            "v0.6": {"rows": len(v06), "sha256": sha256(V06_PATH)},
        },
        "artifacts": {
            "v0.5_head_sha256": sha256(MODEL_DIR / "granite_mlp_v05.joblib"),
            "v0.6_head_sha256": sha256(MODEL_DIR / "granite_mlp_v06.joblib"),
            "predictions_sha256": sha256(PREDICTIONS_PATH),
        },
        "runtime": {"scikit_learn": sklearn.__version__},
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    report = "\n".join(
        [
            "# Granite v0.5/v0.6 블라인드 예측 봉인",
            "",
            "- 상태: `FROZEN_BEFORE_LABELING`",
            f"- 모델: `{MODEL_ID}` + MLP 32-unit",
            f"- 전처리: `{PREPROCESSING_VERSION}`",
            f"- 홀드아웃: {len(holdout)}개",
            f"- 홀드아웃 fingerprint: `{holdout_fingerprint}`",
            f"- v0.5 학습 행: {len(v05)}개",
            f"- v0.6 학습 행: {len(v06)}개",
            f"- 비공개 예측 파일 SHA-256: `{metadata['artifacts']['predictions_sha256']}`",
            "",
            "사람 라벨을 보기 전에 두 모델의 확률과 앱 최종 등급을 저장했다.",
            "라벨 입력 뒤에는 이 파일을 다시 생성하지 않고 해시를 검증해 평가한다.",
            "",
        ]
    )
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
