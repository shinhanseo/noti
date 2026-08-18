"""Compare newly shortlisted compact multilingual backbones for noti."""

from __future__ import annotations

import gc
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import compare_new_ondevice_backbones_v1 as benchmark


PROJECT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_DIR / ".cache" / "compact_mobile_backbone_benchmark_v2"
MODEL_DIR = PROJECT_DIR / "models" / "compact_mobile_backbone_benchmark_v2"
PRIVATE_PREDICTIONS = (
    PROJECT_DIR
    / "data"
    / "private"
    / "compact_mobile_backbone_benchmark_v2_predictions.csv"
)
JSON_OUTPUT = PROJECT_DIR / "reports" / "compact_mobile_backbone_benchmark_v2.json"
MARKDOWN_OUTPUT = PROJECT_DIR / "reports" / "compact_mobile_backbone_benchmark_v2.md"

MODELS: tuple[dict[str, Any], ...] = (
    {
        "key": "bekko_embedding_v1_a8m",
        "model_id": "hotchpotch/bekko-embedding-v1-a8m",
        "prompt_name": None,
        "prefix": "",
        "trust_remote_code": False,
        "batch_size": 64,
        "release_date": "2026-07-07",
        "license": "MIT",
        "deployment_artifact": "default ONNX with int8 token embedding table",
        "deployment_model_bytes": 130_099_079,
        "deployment_tokenizer_bytes": 34_363_442,
        "deployment_quantization_note": "recommended by model author",
    },
    {
        "key": "bekko_embedding_v1_a25m",
        "model_id": "hotchpotch/bekko-embedding-v1-a25m",
        "prompt_name": None,
        "prefix": "",
        "trust_remote_code": False,
        "batch_size": 32,
        "release_date": "2026-07-19",
        "license": "MIT",
        "deployment_artifact": "ARM64 qint8 ONNX",
        "deployment_model_bytes": 123_979_898,
        "deployment_tokenizer_bytes": 34_363_442,
        "deployment_quantization_note": "experimental; author warns quality may regress",
    },
    {
        "key": "koen_e5_tiny",
        "model_id": "exp-models/dragonkue-KoEn-E5-Tiny",
        "prompt_name": None,
        "prefix": "query: ",
        "trust_remote_code": False,
        "batch_size": 64,
        "release_date": "2025-05-13",
        "license": "Apache-2.0",
        "deployment_artifact": "ARM64 qint8 ONNX",
        "deployment_model_bytes": 38_275_821,
        "deployment_tokenizer_bytes": 2_931_715,
        "deployment_quantization_note": "prebuilt in the model repository",
    },
)


def markdown(results: dict[str, Any]) -> str:
    lines = [
        "# Compact mobile backbone 동일조건 비교 v2",
        "",
        "기존 후보를 제외하고 새 소형 후보 세 개를 v0.5 600개, Android v2 전처리, 고정 5-Fold, 동일 MLP 32-unit, Room 145개로 비교했다.",
        "",
        "## 성능과 배포 크기",
        "",
        "| 모델 | 합성 CV Acc | Room 100 Acc | Room 45 Acc | Room 145 Acc | 중요 Precision | 중요 Recall | 중요 F1 | FP | FN | 모델+토크나이저 MiB |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for config in MODELS:
        value = results["models"][config["key"]]
        evaluation = value["evaluation"]
        room = evaluation["room_145"]
        binary = room["important_binary"]
        package_bytes = (
            config["deployment_model_bytes"] + config["deployment_tokenizer_bytes"]
        )
        lines.append(
            f"| {config['key']} | {evaluation['cross_validation']['three_class_accuracy']:.3f} | "
            f"{evaluation['room_100']['three_class_accuracy']:.3f} | "
            f"{evaluation['room_45']['three_class_accuracy']:.3f} | "
            f"{room['three_class_accuracy']:.3f} | {binary['precision']:.3f} | "
            f"{binary['recall']:.3f} | {binary['f1']:.3f} | "
            f"{binary['false_positive']} | {binary['false_negative']} | "
            f"{package_bytes / 1024**2:.1f} |"
        )
    lines.extend(
        [
            "",
            "## Python CPU 참고 측정",
            "",
            "| 모델 | 전체 파라미터 | 차원 | 단일 median ms | 단일 p95 ms | 배포 artifact |",
            "| --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for config in MODELS:
        value = results["models"][config["key"]]
        runtime = value["runtime"]
        lines.append(
            f"| {config['key']} | {runtime['parameter_count']:,} | "
            f"{runtime['embedding_dimension']} | {runtime['single_median_ms']:.2f} | "
            f"{runtime['single_p95_ms']:.2f} | {config['deployment_artifact']} |"
        )
    lines.extend(
        [
            "",
            "Room 145개는 회고적 개발 비교이며 최종 블라인드 결과가 아니다.",
            "배포 크기는 Hugging Face 저장소에서 확인한 모델 파일과 tokenizer.json의 합이며 Android 라이브러리 용량은 제외한다.",
            "실제 채택 전 승자의 ONNX 출력을 검증하고 Android 실기기에서 속도·메모리·배터리를 측정해야 한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    benchmark.CACHE_DIR = CACHE_DIR
    benchmark.MODEL_DIR = MODEL_DIR
    benchmark.MODELS = MODELS

    training = benchmark.experiment.load_training_data(benchmark.DATA_PATH)
    holdout = benchmark.load_holdouts()
    all_texts = list(dict.fromkeys([*training["text"], *holdout["text"]]))
    positions = {text: index for index, text in enumerate(all_texts)}
    training_indices = [positions[text] for text in training["text"]]
    holdout_indices = [positions[text] for text in holdout["text"]]
    results: dict[str, Any] = {
        "protocol": {
            "training_rows": len(training),
            "holdout_rows": len(holdout),
            "holdout_sources": holdout["source_holdout"].value_counts().to_dict(),
            "max_length": benchmark.MAX_LENGTH,
            "head": "mlp_32",
            "folds": 5,
            "random_seed": 42,
            "preprocessing": benchmark.PREPROCESSING_VERSION,
            "blind_status": "RETROSPECTIVE_DEVELOPMENT_NOT_PRISTINE_BLIND",
        },
        "models": {},
    }
    private = holdout[
        ["source_holdout", "review_id", "private_id", "user_common_actionability"]
    ].copy()
    predictions_by_model: dict[str, np.ndarray] = {}
    for config in MODELS:
        print(f"\n{config['key']} embedding", flush=True)
        vectors, runtime = benchmark.get_embeddings(config, all_texts)
        evaluation, predictions = benchmark.evaluate(
            training,
            holdout,
            vectors[training_indices],
            vectors[holdout_indices],
            config["key"],
        )
        results["models"][config["key"]] = {
            "model_id": config["model_id"],
            "release_date": config["release_date"],
            "license": config["license"],
            "prefix": config["prefix"],
            "runtime": runtime,
            "deployment": {
                "artifact": config["deployment_artifact"],
                "model_bytes": config["deployment_model_bytes"],
                "tokenizer_bytes": config["deployment_tokenizer_bytes"],
                "package_bytes": config["deployment_model_bytes"]
                + config["deployment_tokenizer_bytes"],
                "note": config["deployment_quantization_note"],
            },
            "evaluation": evaluation,
        }
        predictions_by_model[config["key"]] = predictions
        private[f"{config['key']}_actionability"] = predictions
        del vectors
        gc.collect()

    results["paired_comparisons"] = {
        source: benchmark.paired_comparisons(holdout, predictions_by_model, source)
        for source in ("room_100", "room_45", "room_145")
    }
    PRIVATE_PREDICTIONS.parent.mkdir(parents=True, exist_ok=True)
    private.to_csv(PRIVATE_PREDICTIONS, index=False, encoding="utf-8-sig")
    JSON_OUTPUT.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(markdown(results), encoding="utf-8")
    print("\n" + markdown(results))


if __name__ == "__main__":
    main()
