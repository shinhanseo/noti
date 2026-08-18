"""Build and verify the self-contained KoEn-E5-Tiny Android ONNX package."""

from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import onnx
import onnxruntime as ort
import sentencepiece as spm
from onnx import TensorProto, helper, numpy_helper
from huggingface_hub import try_to_load_from_cache
from sentencepiece import sentencepiece_model_pb2
from transformers import AutoTokenizer

import compare_new_ondevice_backbones_v1 as benchmark


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_ID = "exp-models/dragonkue-KoEn-E5-Tiny"
BASE_ONNX = (
    PROJECT_DIR
    / "models"
    / "compact_mobile_backbone_benchmark_v2"
    / "onnx_artifacts"
    / "koen_e5_tiny"
    / "model_qint8_arm64.onnx"
)
HEAD_PATH = (
    PROJECT_DIR
    / "models"
    / "compact_mobile_onnx_validation_v2"
    / "koen_e5_tiny_arm64_int8_mlp_32.joblib"
)
OUTPUT_DIR = PROJECT_DIR / "models" / "koen_e5_tiny_android_v1"
OUTPUT_ONNX = OUTPUT_DIR / "noti_koen_e5_tiny_actionability_v1_int8.onnx"
OUTPUT_TOKENIZER = OUTPUT_DIR / "tokenizer.model"
OUTPUT_MANIFEST = OUTPUT_DIR / "manifest.json"
ANDROID_ASSET_DIR = PROJECT_DIR.parent / "app" / "src" / "main" / "assets" / "ai"
PREFIX = "query: "
MAX_LENGTH = 64


def local_tokenizer_json(tokenizer: Any) -> Path:
    cached = try_to_load_from_cache(MODEL_ID, "tokenizer.json")
    if not isinstance(cached, str):
        raise FileNotFoundError(f"tokenizer.json is not cached for {MODEL_ID}")
    value = Path(cached)
    if not value.exists():
        raise FileNotFoundError(value)
    return value


def build_sentencepiece_model(tokenizer_json: Path, output: Path) -> None:
    spec = json.loads(tokenizer_json.read_text(encoding="utf-8"))
    model_spec = spec["model"]
    if model_spec["type"] != "Unigram":
        raise ValueError("Only a Hugging Face Unigram tokenizer is supported")

    proto = sentencepiece_model_pb2.ModelProto()
    proto.trainer_spec.model_type = sentencepiece_model_pb2.TrainerSpec.UNIGRAM
    proto.trainer_spec.vocab_size = len(model_spec["vocab"])
    proto.trainer_spec.unk_id = 3
    proto.trainer_spec.bos_id = 0
    proto.trainer_spec.eos_id = 2
    proto.trainer_spec.pad_id = 1
    proto.trainer_spec.unk_piece = "<unk>"
    proto.trainer_spec.bos_piece = "<s>"
    proto.trainer_spec.eos_piece = "</s>"
    proto.trainer_spec.pad_piece = "<pad>"

    normalizers = spec["normalizer"]["normalizers"]
    precompiled = next(value for value in normalizers if value["type"] == "Precompiled")
    proto.normalizer_spec.name = "noti_huggingface_precompiled"
    proto.normalizer_spec.precompiled_charsmap = base64.b64decode(
        precompiled["precompiled_charsmap"]
    )
    proto.normalizer_spec.add_dummy_prefix = True
    proto.normalizer_spec.remove_extra_whitespaces = True
    proto.normalizer_spec.escape_whitespaces = True

    for index, (piece, score) in enumerate(model_spec["vocab"]):
        value = proto.pieces.add()
        value.piece = piece
        value.score = float(score)
        if index == 3:
            value.type = sentencepiece_model_pb2.ModelProto.SentencePiece.UNKNOWN
        elif index in (0, 1, 2, 41347):
            value.type = sentencepiece_model_pb2.ModelProto.SentencePiece.CONTROL
        else:
            value.type = sentencepiece_model_pb2.ModelProto.SentencePiece.NORMAL

    output.write_bytes(proto.SerializeToString())


def add_actionability_head(base_path: Path, head_path: Path, output: Path) -> None:
    model = onnx.load(base_path)
    classifier = joblib.load(head_path)
    if classifier.classes_.tolist() != [0, 1, 2]:
        raise ValueError(f"Unexpected class order: {classifier.classes_.tolist()}")

    initializers = [
        numpy_helper.from_array(np.asarray(classifier.coefs_[0], dtype=np.float32), "mlp_w1"),
        numpy_helper.from_array(np.asarray(classifier.intercepts_[0], dtype=np.float32), "mlp_b1"),
        numpy_helper.from_array(np.asarray(classifier.coefs_[1], dtype=np.float32), "mlp_w2"),
        numpy_helper.from_array(np.asarray(classifier.intercepts_[1], dtype=np.float32), "mlp_b2"),
        numpy_helper.from_array(np.asarray([2], dtype=np.int64), "axes_unsqueeze_2"),
        numpy_helper.from_array(np.asarray([1], dtype=np.int64), "axes_reduce_1"),
        numpy_helper.from_array(np.asarray([1e-12], dtype=np.float32), "norm_epsilon"),
    ]
    nodes = [
        helper.make_node("Cast", ["attention_mask"], ["attention_mask_float"], to=TensorProto.FLOAT),
        helper.make_node(
            "Unsqueeze",
            ["attention_mask_float", "axes_unsqueeze_2"],
            ["attention_mask_3d"],
        ),
        helper.make_node(
            "Mul", ["last_hidden_state", "attention_mask_3d"], ["masked_hidden"]
        ),
        helper.make_node(
            "ReduceSum", ["masked_hidden", "axes_reduce_1"], ["hidden_sum"], keepdims=0
        ),
        helper.make_node(
            "ReduceSum", ["attention_mask_3d", "axes_reduce_1"], ["token_count"], keepdims=0
        ),
        helper.make_node("Div", ["hidden_sum", "token_count"], ["mean_embedding"]),
        helper.make_node(
            "ReduceL2", ["mean_embedding"], ["embedding_norm"], axes=[1], keepdims=1
        ),
        helper.make_node("Add", ["embedding_norm", "norm_epsilon"], ["safe_norm"]),
        helper.make_node("Div", ["mean_embedding", "safe_norm"], ["embedding"]),
        helper.make_node("Gemm", ["embedding", "mlp_w1", "mlp_b1"], ["hidden_1"]),
        helper.make_node("Relu", ["hidden_1"], ["activated_1"]),
        helper.make_node("Gemm", ["activated_1", "mlp_w2", "mlp_b2"], ["logits"]),
        helper.make_node("Softmax", ["logits"], ["probabilities"], axis=1),
    ]
    model.graph.initializer.extend(initializers)
    model.graph.node.extend(nodes)
    del model.graph.output[:]
    model.graph.output.append(
        helper.make_tensor_value_info(
            "probabilities", TensorProto.FLOAT, ["batch_size", 3]
        )
    )
    onnx.checker.check_model(model)
    onnx.save(model, output)


def encode_huggingface(tokenizer: Any, text: str) -> tuple[list[int], list[int]]:
    encoded = tokenizer(
        PREFIX + text,
        max_length=MAX_LENGTH,
        padding="max_length",
        truncation=True,
    )
    return encoded["input_ids"], encoded["attention_mask"]


def encode_sentencepiece(processor: spm.SentencePieceProcessor, text: str) -> tuple[list[int], list[int]]:
    pieces = processor.encode(PREFIX + text, out_type=int)[: MAX_LENGTH - 2]
    ids = [0, *pieces, 2]
    mask = [1] * len(ids)
    padding = MAX_LENGTH - len(ids)
    return ids + [1] * padding, mask + [0] * padding


def onnx_probability(
    session: ort.InferenceSession, ids: list[int], mask: list[int]
) -> np.ndarray:
    input_ids = np.asarray([ids], dtype=np.int64)
    attention_mask = np.asarray([mask], dtype=np.int64)
    return session.run(
        ["probabilities"],
        {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": np.zeros_like(input_ids),
        },
    )[0][0]


def verification_texts() -> list[str]:
    training = benchmark.experiment.load_training_data(benchmark.DATA_PATH)
    holdout = benchmark.load_holdouts()
    return list(dict.fromkeys([*training["text"], *holdout["text"]]))


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
    build_sentencepiece_model(local_tokenizer_json(tokenizer), OUTPUT_TOKENIZER)
    add_actionability_head(BASE_ONNX, HEAD_PATH, OUTPUT_ONNX)

    processor = spm.SentencePieceProcessor(model_file=str(OUTPUT_TOKENIZER))
    texts = verification_texts()
    mismatches = []
    for index, text in enumerate(texts):
        expected = encode_huggingface(tokenizer, text)
        actual = encode_sentencepiece(processor, text)
        if actual != expected:
            mismatches.append(index)
    if mismatches:
        raise AssertionError(
            f"SentencePiece conversion mismatch on {len(mismatches)} texts: {mismatches[:10]}"
        )

    session = ort.InferenceSession(str(OUTPUT_ONNX), providers=["CPUExecutionProvider"])
    golden_text = "배송 출발 주문하신 상품이 오늘 오후 도착할 예정입니다."
    golden_ids, golden_mask = encode_sentencepiece(processor, golden_text)
    golden_probability = onnx_probability(session, golden_ids, golden_mask)
    manifest = {
        "model_version": "noti_koen_e5_tiny_actionability_v1",
        "base_model": MODEL_ID,
        "onnx_bytes": OUTPUT_ONNX.stat().st_size,
        "tokenizer_bytes": OUTPUT_TOKENIZER.stat().st_size,
        "max_length": MAX_LENGTH,
        "prefix": PREFIX,
        "input_order": ["input_ids", "attention_mask", "token_type_ids"],
        "output": "probabilities",
        "labels": ["GENERAL", "ATTENTION_WORTHY", "ACTION_REQUIRED"],
        "tokenizer_verification_rows": len(texts),
        "tokenizer_mismatches": len(mismatches),
        "golden": {
            "normalized_text": golden_text,
            "input_ids": golden_ids,
            "attention_mask": golden_mask,
            "probabilities": [float(value) for value in golden_probability],
        },
    }
    OUTPUT_MANIFEST.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ANDROID_ASSET_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUTPUT_ONNX, ANDROID_ASSET_DIR / OUTPUT_ONNX.name)
    shutil.copyfile(OUTPUT_TOKENIZER, ANDROID_ASSET_DIR / OUTPUT_TOKENIZER.name)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
