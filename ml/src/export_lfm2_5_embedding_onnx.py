"""Export LFM2.5 Embedding to fixed-shape ONNX and verify dynamic INT8 quality."""

from __future__ import annotations

import gc
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parents[1]
os.environ.setdefault("HF_MODULES_CACHE", str(PROJECT_DIR / ".cache" / "huggingface_modules"))

import joblib
import numpy as np
import onnx
import onnxruntime as ort
import pandas as pd
import torch
from huggingface_hub import snapshot_download
from onnxruntime.quantization import QuantType, quantize_dynamic
from onnxruntime.quantization.matmul_nbits_quantizer import (
    DefaultWeightOnlyQuantConfig,
    MatMulNBitsQuantizer,
)
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer

import compare_new_ondevice_backbones_v1 as benchmark
from actionability_contract import predicted_actionability
from evaluate_granite_v05_v06_blind_holdout import model_metrics


MODEL_KEY = "lfm2_5_embedding_350m"
MODEL_ID = "LiquidAI/LFM2.5-Embedding-350M"
PROMPT = "document: "
SEQUENCE_LENGTH = 64
OUTPUT_DIR = PROJECT_DIR / "models" / "lfm2_5_embedding_onnx"
FP32_PATH = OUTPUT_DIR / "lfm2_5_embedding_350m_seq64_fp32.onnx"
INT8_PATH = OUTPUT_DIR / "lfm2_5_embedding_350m_seq64_dynamic_int8.onnx"
INT4_PATH = OUTPUT_DIR / "lfm2_5_embedding_350m_seq64_weight_int4.onnx"
CACHE_DIR = PROJECT_DIR / ".cache" / "lfm2_5_embedding_onnx"
REPORT_PATH = PROJECT_DIR / "reports" / "lfm2_5_embedding_onnx_v1.json"
MARKDOWN_PATH = PROJECT_DIR / "reports" / "lfm2_5_embedding_onnx_v1.md"
BENCHMARK_ROWS = 30


class LfmEmbeddingForOnnx(torch.nn.Module):
    def __init__(self, sentence_model: SentenceTransformer):
        super().__init__()
        self.encoder = sentence_model[0].auto_model

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        hidden = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            use_cache=False,
            return_dict=False,
        )[0]
        return torch.nn.functional.normalize(hidden[:, 0, :].float(), p=2, dim=1)


def load_model() -> LfmEmbeddingForOnnx:
    sentence_model = SentenceTransformer(
        MODEL_ID,
        device="cpu",
        local_files_only=True,
        trust_remote_code=True,
    )
    sentence_model.max_seq_length = SEQUENCE_LENGTH
    patched = benchmark.apply_lfm_transformers_compatibility(sentence_model)
    if patched == 0:
        raise RuntimeError("LFM ShortConv compatibility patch target was not found.")
    # Android ONNX Runtime portability is better with an FP32 source graph.
    sentence_model.float().eval()
    return LfmEmbeddingForOnnx(sentence_model).eval()


def load_tokenizer() -> Any:
    snapshot = snapshot_download(repo_id=MODEL_ID, local_files_only=True)
    return AutoTokenizer.from_pretrained(snapshot, local_files_only=True)


def tokenize(tokenizer: Any, texts: list[str]) -> tuple[np.ndarray, np.ndarray]:
    encoded = tokenizer(
        [PROMPT + text for text in texts],
        return_tensors="np",
        padding="max_length",
        truncation=True,
        max_length=SEQUENCE_LENGTH,
    )
    return (
        encoded["input_ids"].astype(np.int64),
        encoded["attention_mask"].astype(np.int64),
    )


def export_fp32(model: LfmEmbeddingForOnnx, tokenizer: Any) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ids, mask = tokenize(tokenizer, ["카드 승인에 실패했습니다. 확인해주세요."])
    torch.onnx.export(
        model,
        (torch.from_numpy(ids), torch.from_numpy(mask)),
        FP32_PATH,
        input_names=["input_ids", "attention_mask"],
        output_names=["sentence_embedding"],
        opset_version=18,
        dynamo=True,
        external_data=True,
        optimize=True,
    )


def export_int8() -> None:
    quantize_dynamic(
        FP32_PATH,
        INT8_PATH,
        per_channel=True,
        weight_type=QuantType.QInt8,
        op_types_to_quantize=["MatMul", "Gemm"],
        use_external_data_format=True,
        extra_options={"MatMulConstBOnly": True},
    )


def export_int4() -> None:
    config = DefaultWeightOnlyQuantConfig(
        block_size=128,
        is_symmetric=True,
        bits=4,
        op_types_to_quantize=("MatMul",),
    )
    quantizer = MatMulNBitsQuantizer(str(FP32_PATH), algo_config=config)
    quantizer.process()
    quantizer.model.save_model_to_file(
        str(INT4_PATH), use_external_data_format=True
    )


def artifact_bytes(path: Path) -> int:
    return sum(
        candidate.stat().st_size
        for candidate in path.parent.glob(f"{path.name}*")
        if candidate.is_file()
    )


def graph_metadata(path: Path) -> dict[str, object]:
    model = onnx.load(path, load_external_data=False)
    ops: dict[str, int] = {}
    for node in model.graph.node:
        ops[node.op_type] = ops.get(node.op_type, 0) + 1
    return {
        "ir_version": model.ir_version,
        "opset": {item.domain or "ai.onnx": item.version for item in model.opset_import},
        "node_count": len(model.graph.node),
        "operator_counts": dict(sorted(ops.items())),
    }


def create_session(path: Path) -> ort.InferenceSession:
    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(
        str(path), sess_options=options, providers=["CPUExecutionProvider"]
    )


def run_session(
    session: ort.InferenceSession,
    input_ids: np.ndarray,
    attention_mask: np.ndarray,
) -> np.ndarray:
    vectors = []
    for ids, mask in zip(input_ids, attention_mask):
        result = session.run(
            ["sentence_embedding"],
            {
                "input_ids": ids[None, :],
                "attention_mask": mask[None, :],
            },
        )[0]
        vectors.append(result[0])
    return np.asarray(vectors, dtype=np.float32)


def benchmark_session(
    session: ort.InferenceSession,
    input_ids: np.ndarray,
    attention_mask: np.ndarray,
) -> dict[str, float | int]:
    sample_count = min(BENCHMARK_ROWS, len(input_ids))
    for index in range(min(5, sample_count)):
        run_session(session, input_ids[index : index + 1], attention_mask[index : index + 1])
    durations = []
    for index in range(sample_count):
        started = time.perf_counter()
        run_session(session, input_ids[index : index + 1], attention_mask[index : index + 1])
        durations.append((time.perf_counter() - started) * 1000)
    return {
        "single_median_ms": float(np.median(durations)),
        "single_p95_ms": float(np.percentile(durations, 95)),
        "single_samples": sample_count,
    }


def cosine_rows(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    numerator = np.sum(left * right, axis=1)
    denominator = np.linalg.norm(left, axis=1) * np.linalg.norm(right, axis=1)
    return numerator / np.maximum(denominator, 1e-12)


def pytorch_source_reference(
    texts: list[str],
    input_ids: np.ndarray,
    attention_mask: np.ndarray,
) -> np.ndarray:
    digest = hashlib.sha256()
    for text in texts:
        digest.update(text.encode("utf-8"))
        digest.update(b"\0")
    target = CACHE_DIR / f"room_fp32_source_batch1_{digest.hexdigest()[:16]}.npz"
    if target.exists():
        return np.load(target)["embeddings"]
    model = load_model()
    chunks = []
    with torch.inference_mode():
        # The deployed graph is fixed to batch 1. LFM's current bidirectional
        # ShortConv implementation is slightly batch-sensitive, so the source
        # reference must use the exact same batch contract.
        for offset in range(len(texts)):
            chunks.append(
                model(
                    torch.from_numpy(input_ids[offset : offset + 1]),
                    torch.from_numpy(attention_mask[offset : offset + 1]),
                ).cpu().numpy()
            )
    vectors = np.concatenate(chunks, axis=0).astype(np.float32)
    target.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(target, embeddings=vectors)
    del model
    gc.collect()
    return vectors


def load_reference() -> tuple[pd.DataFrame, np.ndarray]:
    training = benchmark.experiment.load_training_data(benchmark.DATA_PATH)
    holdout = benchmark.load_holdouts()
    all_texts = list(dict.fromkeys([*training["text"], *holdout["text"]]))
    positions = {text: index for index, text in enumerate(all_texts)}
    holdout_indices = [positions[text] for text in holdout["text"]]
    config = next(config for config in benchmark.MODELS if config["key"] == MODEL_KEY)
    cache = benchmark.cache_path(config, all_texts)
    if not cache.exists():
        raise FileNotFoundError(f"Full-precision embedding cache not found: {cache}")
    return holdout, np.load(cache)["embeddings"][holdout_indices]


def evaluate_variant(
    name: str,
    path: Path,
    tokenizer: Any,
    holdout: pd.DataFrame,
    benchmark_reference: np.ndarray,
    source_reference: np.ndarray,
    input_ids: np.ndarray,
    attention_mask: np.ndarray,
) -> tuple[dict[str, object], np.ndarray]:
    load_started = time.perf_counter()
    session = create_session(path)
    load_seconds = time.perf_counter() - load_started
    vectors = run_session(session, input_ids, attention_mask)
    source_cosine = cosine_rows(source_reference, vectors)
    benchmark_cosine = cosine_rows(benchmark_reference, vectors)
    head = joblib.load(benchmark.MODEL_DIR / f"{MODEL_KEY}_mlp_32.joblib")
    predictions = np.asarray(predicted_actionability(head.predict_proba(vectors)))
    result: dict[str, object] = {
        "artifact_bytes": artifact_bytes(path),
        "session_load_seconds": load_seconds,
        "cosine_vs_export_source_mean": float(source_cosine.mean()),
        "cosine_vs_export_source_min": float(source_cosine.min()),
        "max_absolute_error_vs_export_source": float(
            np.max(np.abs(source_reference - vectors))
        ),
        "cosine_vs_benchmark_bf16_mean": float(benchmark_cosine.mean()),
        "cosine_vs_benchmark_bf16_min": float(benchmark_cosine.min()),
        "prediction_disagreements_vs_pytorch": 0,
        "room_145": model_metrics(
            holdout["user_common_actionability"], pd.Series(predictions)
        ),
        "runtime": benchmark_session(session, input_ids, attention_mask),
        "graph": graph_metadata(path),
    }
    print(f"{name}: {path} ({result['artifact_bytes'] / 1024**2:.1f} MiB)")
    del session
    gc.collect()
    return result, predictions


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# LFM2.5 Embedding ONNX 변환 검증 v1",
        "",
        "배치 1, 64 tokens, `document:` 프롬프트로 고정한 encoder를 동일한 MLP head와 Room 145개로 검증했다.",
        "",
        "| 모델 | 크기 MiB | 동일 FP32 source cosine 평균/최소 | 기존 BF16 cosine 평균/최소 | 예측 불일치 | Room Acc | 중요 Recall | 중요 F1 | median ms | p95 ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key in ("fp32", "dynamic_int8", "weight_int4"):
        value = report["variants"][key]
        room = value["room_145"]
        binary = room["important_binary"]
        lines.append(
            f"| {key} | {value['artifact_bytes'] / 1024**2:.1f} | "
            f"{value['cosine_vs_export_source_mean']:.6f} / {value['cosine_vs_export_source_min']:.6f} | "
            f"{value['cosine_vs_benchmark_bf16_mean']:.6f} / {value['cosine_vs_benchmark_bf16_min']:.6f} | "
            f"{value['prediction_disagreements_vs_pytorch']} | "
            f"{room['three_class_accuracy']:.3f} | {binary['recall']:.3f} | "
            f"{binary['f1']:.3f} | {value['runtime']['single_median_ms']:.2f} | "
            f"{value['runtime']['single_p95_ms']:.2f} |"
        )
    lines.extend(
        [
            "",
            "Mac CPU + ONNX Runtime 측정이며 Android 실기기 결과가 아니다.",
            "LFM 공식 bidirectional ShortConv는 배치 크기에 따라 출력이 조금 달라져 배포 계약과 검증 기준을 모두 batch 1로 고정했다.",
            "INT4가 가장 작지만 403 MiB이고 `com.microsoft::MatMulNBits`를 사용하므로 현재 상태로 앱에 채택하지 않는다.",
            "다음 후보는 더 작은 backbone을 찾거나 LFM 지식을 작은 학생 모델로 증류해야 한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    tokenizer = load_tokenizer()
    if not FP32_PATH.exists():
        print("Exporting FP32 ONNX", flush=True)
        model = load_model()
        export_fp32(model, tokenizer)
        del model
        gc.collect()
    if not INT8_PATH.exists():
        print("Quantizing dynamic INT8 ONNX", flush=True)
        export_int8()
    if not INT4_PATH.exists():
        print("Quantizing weight-only INT4 ONNX", flush=True)
        export_int4()

    holdout, benchmark_reference = load_reference()
    input_ids, attention_mask = tokenize(tokenizer, holdout["text"].tolist())
    source_reference = pytorch_source_reference(
        holdout["text"].tolist(),
        input_ids,
        attention_mask,
    )
    reference_head = joblib.load(benchmark.MODEL_DIR / f"{MODEL_KEY}_mlp_32.joblib")
    reference_predictions = np.asarray(
        predicted_actionability(reference_head.predict_proba(benchmark_reference))
    )
    report: dict[str, Any] = {
        "protocol": {
            "model_id": MODEL_ID,
            "sequence_length": SEQUENCE_LENGTH,
            "batch_size": 1,
            "batch_contract_reason": (
                "The current bidirectional ShortConv implementation is slightly "
                "batch-sensitive, so export and source verification both use batch 1."
            ),
            "prompt": PROMPT,
            "holdout_rows": len(holdout),
            "head": "same frozen mlp_32 head as new_ondevice_backbone_benchmark_v1",
            "runtime": "ONNX Runtime CPUExecutionProvider, 4 intra-op threads",
        },
        "variants": {},
    }
    for key, path in (
        ("fp32", FP32_PATH),
        ("dynamic_int8", INT8_PATH),
        ("weight_int4", INT4_PATH),
    ):
        value, predictions = evaluate_variant(
            key,
            path,
            tokenizer,
            holdout,
            benchmark_reference,
            source_reference,
            input_ids,
            attention_mask,
        )
        value["prediction_disagreements_vs_pytorch"] = int(
            np.sum(predictions != reference_predictions)
        )
        report["variants"][key] = value

    report["decision"] = {
        "status": "REJECT_CURRENT_LFM_ARTIFACT_FOR_ANDROID",
        "reason": (
            "The smallest tested artifact is still about 403 MiB and relies on "
            "the com.microsoft MatMulNBits contrib operator."
        ),
        "next": "distill to a smaller student or evaluate a smaller backbone",
    }

    fp32 = report["variants"]["fp32"]
    if fp32["cosine_vs_export_source_min"] < 0.99999:
        raise RuntimeError("FP32 ONNX output does not match its PyTorch export source.")

    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    MARKDOWN_PATH.write_text(markdown(report), encoding="utf-8")
    print("\n" + markdown(report))


if __name__ == "__main__":
    main()
