"""Validate and package the final single-file EmbeddingGemma classifier."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from ai_edge_litert.interpreter import Interpreter
from transformers import AutoTokenizer

import compare_frozen_backbones_v05 as benchmark
from actionability_contract import ACTIONABILITY_LABELS, predicted_actionability
from evaluate_granite_v05_v06_blind_holdout import model_metrics
from evaluate_litert_backbones_v05 import MODELS, tflite_embeddings
from notification_text_preprocessor import (
    PREPROCESSING_VERSION,
    normalize_notification_text,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
CLASSIFICATION_PREFIX = "task: classification | query: "
PACKAGE_DIR = PROJECT_DIR / "models" / "noti_embeddinggemma_actionability_v1"
MODEL_PATH = PACKAGE_DIR / "noti_embeddinggemma_actionability_v1_int8.tflite"
TOKENIZER_DIR = PACKAGE_DIR / "tokenizer"
HEAD_PATH = (
    PROJECT_DIR
    / "models"
    / "frozen_backbone_benchmark_v1"
    / "embeddinggemma_300m_mlp_32.joblib"
)
OLD_HOLDOUT = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-12_raw"
    / "blind_holdout_review_100.csv"
)
NEW_HOLDOUT = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-16_raw"
    / "incremental_holdout_review.csv"
)
PRIVATE_OUTPUT = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-16_raw"
    / "embeddinggemma_actionability_v1_evaluation.csv"
)
REPORT_PATH = PROJECT_DIR / "reports" / "embeddinggemma_actionability_v1_validation.json"
GOLDEN_PATH = PACKAGE_DIR / "golden_test_cases.json"
METADATA_PATH = PACKAGE_DIR / "model_metadata.json"
README_PATH = PACKAGE_DIR / "README.md"


GOLDEN_CASES = [
    {
        "id": "shipping_started",
        "package_name": "com.example.shopping",
        "title": "배송 출발",
        "body": "주문하신 상품이 오늘 오후 도착할 예정입니다.",
    },
    {
        "id": "promotion_coupon",
        "package_name": "com.example.shopping",
        "title": "주말 특가 쿠폰",
        "body": "(광고) 오늘만 사용할 수 있는 할인 쿠폰입니다. 수신거부: 설정",
    },
    {
        "id": "bank_withdrawal_upcoming",
        "package_name": "com.example.bank",
        "title": "출금 예정",
        "body": "내일 후불교통 이용금액이 출금될 예정입니다. 계좌 잔액을 확인해주세요.",
    },
    {
        "id": "reply_required",
        "package_name": "com.example.work",
        "title": "회의 자료 요청",
        "body": "오늘 오후 3시까지 자료를 회신해주세요.",
    },
    {
        "id": "calendar_soon",
        "package_name": "com.example.calendar",
        "title": "병원 예약",
        "body": "등록한 일정이 한 시간 후 시작됩니다.",
    },
    {
        "id": "social_like",
        "package_name": "com.example.social",
        "title": "좋아요 알림",
        "body": "회원님의 게시물을 좋아합니다.",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_holdout(path: Path, set_name: str) -> pd.DataFrame:
    data = pd.read_csv(path, dtype=str).fillna("")
    if not data["user_common_actionability"].isin(ACTIONABILITY_LABELS).all():
        raise ValueError(f"{set_name} 라벨이 완성되지 않았습니다.")
    data = data.copy()
    data["set_name"] = set_name
    data["text"] = [
        normalize_notification_text(package, title, body)
        for package, title, body in zip(
            data["package_name"], data["title"], data["body"]
        )
    ]
    return data


class FinalRunner:
    def __init__(self) -> None:
        self.interpreter = Interpreter(model_path=str(MODEL_PATH), num_threads=4)
        self.runner = self.interpreter.get_signature_runner("serving_default")

    def predict(self, input_ids: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
        result = self.runner(
            args_0=input_ids.astype(np.int64),
            args_1=attention_mask.astype(np.int64),
        )
        return np.asarray(result["output_0"], dtype=np.float32)


def final_probabilities(
    runner: FinalRunner, tokenizer: object, texts: list[str]
) -> np.ndarray:
    values = []
    for text in texts:
        encoded = tokenizer(
            CLASSIFICATION_PREFIX + text,
            return_tensors="np",
            padding="max_length",
            truncation=True,
            max_length=benchmark.MAX_LENGTH,
        )
        values.append(runner.predict(encoded["input_ids"], encoded["attention_mask"])[0])
    return np.asarray(values, dtype=np.float32)


def metrics_for(actual: pd.Series, predictions: np.ndarray) -> dict[str, object]:
    return model_metrics(actual.reset_index(drop=True), pd.Series(predictions))


def main() -> None:
    old = load_holdout(OLD_HOLDOUT, "corrected_room_100")
    new = load_holdout(NEW_HOLDOUT, "temporal_blind_room_45")
    holdout = pd.concat([old, new], ignore_index=True)
    texts = holdout["text"].tolist()

    config = next(
        value for value in MODELS if value["key"] == "embeddinggemma_300m"
    )
    split_embeddings = tflite_embeddings(config, texts)
    head = joblib.load(HEAD_PATH)
    split_probability = np.asarray(head.predict_proba(split_embeddings), dtype=np.float32)

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_DIR, local_files_only=True)
    runner = FinalRunner()
    final_probability = final_probabilities(runner, tokenizer, texts)
    if not np.allclose(final_probability.sum(axis=1), 1.0, atol=1e-5):
        raise ValueError("최종 TFLite 확률 합이 1이 아닙니다.")

    split_prediction = np.asarray(predicted_actionability(split_probability))
    final_prediction = np.asarray(predicted_actionability(final_probability))
    disagreements = int(np.sum(split_prediction != final_prediction))
    max_error = float(np.max(np.abs(split_probability - final_probability)))
    mean_error = float(np.mean(np.abs(split_probability - final_probability)))
    if disagreements:
        raise RuntimeError(f"분리 파이프라인과 최종 TFLite 예측이 {disagreements}개 다릅니다.")
    if max_error > 0.02:
        raise RuntimeError(f"최종 TFLite 확률 오차가 허용값을 넘었습니다: {max_error}")

    private = holdout[
        ["set_name", "review_id", "private_id", "user_common_actionability"]
    ].copy()
    for index, label in enumerate(ACTIONABILITY_LABELS):
        private[f"split_probability_{label.lower()}"] = split_probability[:, index]
        private[f"final_probability_{label.lower()}"] = final_probability[:, index]
    private["split_actionability"] = split_prediction
    private["final_actionability"] = final_prediction
    private.to_csv(PRIVATE_OUTPUT, index=False, encoding="utf-8-sig")

    report: dict[str, object] = {
        "model_sha256": sha256(MODEL_PATH),
        "rows": len(holdout),
        "split_vs_final": {
            "prediction_disagreements": disagreements,
            "probability_max_absolute_error": max_error,
            "probability_mean_absolute_error": mean_error,
        },
        "evaluation": {},
    }
    for set_name in holdout["set_name"].unique():
        mask = holdout["set_name"].eq(set_name).to_numpy()
        report["evaluation"][set_name] = metrics_for(
            holdout.loc[mask, "user_common_actionability"], final_prediction[mask]
        )
    report["evaluation"]["combined_145"] = metrics_for(
        holdout["user_common_actionability"], final_prediction
    )

    golden_output = []
    for case in GOLDEN_CASES:
        normalized = normalize_notification_text(
            case["package_name"], case["title"], case["body"]
        )
        encoded = tokenizer(
            CLASSIFICATION_PREFIX + normalized,
            return_tensors="np",
            padding="max_length",
            truncation=True,
            max_length=benchmark.MAX_LENGTH,
        )
        started = time.perf_counter()
        probability = runner.predict(encoded["input_ids"], encoded["attention_mask"])[0]
        duration_ms = (time.perf_counter() - started) * 1000
        golden_output.append(
            {
                **case,
                "normalized_text": normalized,
                "classification_text": CLASSIFICATION_PREFIX + normalized,
                "input_ids": encoded["input_ids"][0].astype(int).tolist(),
                "attention_mask": encoded["attention_mask"][0].astype(int).tolist(),
                "probabilities": {
                    label: float(probability[index])
                    for index, label in enumerate(ACTIONABILITY_LABELS)
                },
                "prediction": ACTIONABILITY_LABELS[int(np.argmax(probability))],
                "local_reference_inference_ms": duration_ms,
            }
        )
    GOLDEN_PATH.write_text(
        json.dumps(golden_output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    input_details = runner.interpreter.get_input_details()
    output_details = runner.interpreter.get_output_details()
    tokenizer_files = {}
    for path in sorted(TOKENIZER_DIR.iterdir()):
        if path.is_file():
            tokenizer_files[path.name] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
    metadata = {
        "model_name": "noti_embeddinggemma_actionability_v1",
        "model_version": 1,
        "base_model": "google/embeddinggemma-300m",
        "preprocessing_version": PREPROCESSING_VERSION,
        "classification_prefix": CLASSIFICATION_PREFIX,
        "sequence_length": benchmark.MAX_LENGTH,
        "padding": "max_length",
        "truncation": True,
        "input_contract": {
            "args_0": {
                "semantic_name": "input_ids",
                "shape": input_details[0]["shape"].astype(int).tolist(),
                "dtype": str(input_details[0]["dtype"].__name__),
            },
            "args_1": {
                "semantic_name": "attention_mask",
                "shape": input_details[1]["shape"].astype(int).tolist(),
                "dtype": str(input_details[1]["dtype"].__name__),
            },
        },
        "output_contract": {
            "output_0": {
                "semantic_name": "probabilities",
                "shape": output_details[0]["shape"].astype(int).tolist(),
                "dtype": str(output_details[0]["dtype"].__name__),
                "label_order": ACTIONABILITY_LABELS,
            }
        },
        "tokenizer": {
            "type": "EmbeddingGemma SentencePiece/Hugging Face tokenizer",
            "pad_token_id": int(tokenizer.pad_token_id),
            "bos_token_id": int(tokenizer.bos_token_id),
            "eos_token_id": int(tokenizer.eos_token_id),
            "files": tokenizer_files,
        },
        "model_file": {
            "name": MODEL_PATH.name,
            "bytes": MODEL_PATH.stat().st_size,
            "sha256": sha256(MODEL_PATH),
        },
        "golden_test_file": {
            "name": GOLDEN_PATH.name,
            "sha256": sha256(GOLDEN_PATH),
        },
        "validation_report": str(REPORT_PATH.relative_to(PROJECT_DIR)),
    }
    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    README_PATH.write_text(
        "\n".join(
            [
                "# noti EmbeddingGemma Actionability v1",
                "",
                "Android 전달용 단일 LiteRT/TFLite 분류 모델 패키지다.",
                "",
                "## 입출력",
                "",
                "- `args_0`: `input_ids`, int64 `[1, 64]`",
                "- `args_1`: `attention_mask`, int64 `[1, 64]`",
                "- `output_0`: float32 확률 `[GENERAL, ATTENTION_WORTHY, ACTION_REQUIRED]`",
                "",
                "전처리 문자열 앞에 `task: classification | query: `를 붙인 뒤 토큰화한다.",
                "64 token으로 자르고 `max_length` padding을 적용한다.",
                "Kotlin 구현은 `golden_test_cases.json`의 token ID와 확률을 단위 테스트로 검증해야 한다.",
                "",
                "## 파일",
                "",
                f"- `{MODEL_PATH.name}`",
                "- `tokenizer/`",
                "- `model_metadata.json`",
                "- `golden_test_cases.json`",
                "- `build_metadata.json`",
                "",
                "이 모델은 먼저 shadow mode로 연결하며 현재 중요도 결과를 직접 변경하지 않는다.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
