"""Evaluate quantized LiteRT backbones on the new incremental Room holdout."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

import compare_frozen_backbones_v05 as benchmark
from actionability_contract import ACTIONABILITY_LABELS, predicted_actionability
from evaluate_granite_v05_v06_blind_holdout import model_metrics
from evaluate_litert_backbones_v05 import MODELS, cosine_rows, tflite_embeddings
from notification_text_preprocessor import normalize_notification_text


PROJECT_DIR = Path(__file__).resolve().parents[1]
PRIVATE_DIR = PROJECT_DIR / "data" / "private" / "room_export_2026-08-16_raw"
HOLDOUT_PATH = PRIVATE_DIR / "incremental_holdout_review.csv"
FROZEN_PATH = PRIVATE_DIR / "incremental_holdout_frozen_predictions.csv"
PRIVATE_OUTPUT = PRIVATE_DIR / "incremental_holdout_litert_evaluation.csv"
JSON_OUTPUT = PROJECT_DIR / "reports" / "incremental_litert_quality_2026-08-16.json"
MARKDOWN_OUTPUT = PROJECT_DIR / "reports" / "incremental_litert_quality_2026-08-16.md"


def markdown(report: dict[str, object]) -> str:
    lines = [
        "# 증분 Room LiteRT 양자화 품질 평가",
        "",
        "새 실제 알림 45개에서 양자화 모델과 봉인된 원본 모델 예측을 비교했다.",
        "",
        "| 모델 | TFLite MiB | 원본과 예측 불일치 | Accuracy | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for config in MODELS:
        key = str(config["key"])
        value = report["models"][key]
        metrics = value["room_holdout"]
        binary = metrics["important_binary"]
        lines.append(
            f"| {key} | {value['tflite_bytes'] / 1024**2:.1f} | "
            f"{value['prediction_disagreements_vs_full_precision']} | "
            f"{metrics['three_class_accuracy']:.3f} | {binary['precision']:.3f} | "
            f"{binary['recall']:.3f} | {binary['f1']:.3f} | "
            f"{binary['false_positive']} | {binary['false_negative']} |"
        )
    lines.extend(
        [
            "",
            "원본 모델 예측은 사람 라벨 입력 전에 봉인한 파일을 사용했다.",
            "행별 실제 알림 결과는 private 경로에만 저장했다.",
            "이 평가는 양자화에 따른 품질 변화이며 실기기 지연시간 측정은 이전 Benchmark를 유지한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    holdout = pd.read_csv(HOLDOUT_PATH, dtype=str).fillna("")
    if not holdout["user_common_actionability"].isin(ACTIONABILITY_LABELS).all():
        raise ValueError("공통 Actionability 라벨이 완성되지 않았습니다.")
    frozen = pd.read_csv(FROZEN_PATH, dtype=str).fillna("")
    if not holdout[["review_id", "private_id"]].equals(
        frozen[["review_id", "private_id"]]
    ):
        raise ValueError("검수 세트와 봉인 예측 행 순서가 일치하지 않습니다.")

    texts = [
        normalize_notification_text(package, title, body)
        for package, title, body in zip(
            holdout["package_name"], holdout["title"], holdout["body"]
        )
    ]
    private = holdout[["review_id", "private_id", "user_common_actionability"]].copy()
    report: dict[str, object] = {
        "protocol": {
            "holdout_rows": len(holdout),
            "max_length": benchmark.MAX_LENGTH,
            "preprocessing": benchmark.PREPROCESSING_VERSION,
            "head": "same saved MLP 32-unit head as full-precision benchmark",
        },
        "models": {},
    }
    for config in MODELS:
        key = str(config["key"])
        head_key = str(config.get("head_key", key))
        print(f"{key}: LiteRT embedding {len(holdout)} rows")
        quantized = tflite_embeddings(config, texts)
        cache = benchmark.cache_path(
            str(config["model_id"]),
            str(config["adapter"]),
            str(config["prefix"]),
            texts,
        )
        if not cache.exists():
            raise FileNotFoundError(f"봉인 단계의 원본 Embedding cache가 없습니다: {cache}")
        full_precision = np.load(cache)["embeddings"]
        cosine = cosine_rows(full_precision, quantized)
        head = joblib.load(benchmark.MODEL_DIR / f"{head_key}_mlp_32.joblib")
        probabilities = np.asarray(head.predict_proba(quantized), dtype=np.float64)
        predictions = np.asarray(predicted_actionability(probabilities))
        expected = frozen[f"{head_key}_actionability"].to_numpy()
        private[f"{key}_actionability"] = predictions
        for index, label in enumerate(ACTIONABILITY_LABELS):
            private[f"{key}_probability_{label.lower()}"] = probabilities[:, index]
        report["models"][key] = {
            "tflite_bytes": Path(config["tflite"]).stat().st_size,
            "embedding_cosine_mean": float(cosine.mean()),
            "embedding_cosine_min": float(cosine.min()),
            "prediction_disagreements_vs_full_precision": int(
                np.sum(predictions != expected)
            ),
            "room_holdout": model_metrics(
                holdout["user_common_actionability"], pd.Series(predictions)
            ),
        }

    private.to_csv(PRIVATE_OUTPUT, index=False, encoding="utf-8-sig")
    JSON_OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(markdown(report), encoding="utf-8")
    print(markdown(report))


if __name__ == "__main__":
    main()
