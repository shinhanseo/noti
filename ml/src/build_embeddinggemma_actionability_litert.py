"""Build the deployable EmbeddingGemma INT8 encoder + MLP actionability model."""

from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import json
import shutil
import sys
import types
from pathlib import Path

import joblib
import numpy as np
import torch
from ai_edge_litert import schema_py_generated
from huggingface_hub import snapshot_download


def install_tensorflow_schema_shim() -> None:
    names = ("tensorflow", "tensorflow.lite", "tensorflow.lite.python")
    modules = {name: types.ModuleType(name) for name in names}
    for name, module in modules.items():
        module.__path__ = []
        module.__spec__ = importlib.machinery.ModuleSpec(
            name, loader=None, is_package=True
        )
    modules["tensorflow"].lite = modules["tensorflow.lite"]
    modules["tensorflow.lite"].python = modules["tensorflow.lite.python"]
    modules["tensorflow.lite.python"].schema_py_generated = schema_py_generated
    sys.modules.update(modules)
    sys.modules["tensorflow.lite.python.schema_py_generated"] = schema_py_generated


install_tensorflow_schema_shim()

import litert_torch  # noqa: E402
from litert_torch.generative.examples.embedding_gemma import embedding_gemma  # noqa: E402
from litert_torch.generative.quantize import quant_recipes  # noqa: E402


PROJECT_DIR = Path(__file__).resolve().parents[1]
MODEL_ID = "google/embeddinggemma-300m"
SEQUENCE_LENGTH = 64
CLASSIFICATION_PREFIX = "task: classification | query: "
HEAD_PATH = (
    PROJECT_DIR
    / "models"
    / "frozen_backbone_benchmark_v1"
    / "embeddinggemma_300m_mlp_32.joblib"
)
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "models" / "noti_embeddinggemma_actionability_v1"
MODEL_FILENAME = "noti_embeddinggemma_actionability_v1_int8.tflite"
LABELS = ["GENERAL", "ATTENTION_WORTHY", "ACTION_REQUIRED"]
TOKENIZER_FILES = [
    "tokenizer.json",
    "tokenizer.model",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "added_tokens.json",
]


class EmbeddingGemmaActionability(torch.nn.Module):
    def __init__(self, encoder: torch.nn.Module, sklearn_head: object):
        super().__init__()
        self.encoder = encoder
        self.config = encoder.config
        self.hidden = torch.nn.Linear(768, 32)
        self.output = torch.nn.Linear(32, 3)
        with torch.no_grad():
            self.hidden.weight.copy_(
                torch.from_numpy(np.asarray(sklearn_head.coefs_[0].T, dtype=np.float32))
            )
            self.hidden.bias.copy_(
                torch.from_numpy(np.asarray(sklearn_head.intercepts_[0], dtype=np.float32))
            )
            self.output.weight.copy_(
                torch.from_numpy(np.asarray(sklearn_head.coefs_[1].T, dtype=np.float32))
            )
            self.output.bias.copy_(
                torch.from_numpy(np.asarray(sklearn_head.intercepts_[1], dtype=np.float32))
            )

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        embedding = self.encoder(input_ids, attention_mask)
        hidden = torch.relu(self.hidden(embedding))
        logits = self.output(hidden)
        return torch.softmax(logits, dim=-1)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--allow-download", action="store_true")
    args = parser.parse_args()

    checkpoint = Path(
        snapshot_download(repo_id=MODEL_ID, local_files_only=not args.allow_download)
    )
    sklearn_head = joblib.load(HEAD_PATH)
    if list(sklearn_head.classes_) != [0, 1, 2]:
        raise ValueError(f"예상하지 못한 class 순서: {sklearn_head.classes_}")
    if [value.shape for value in sklearn_head.coefs_] != [(768, 32), (32, 3)]:
        raise ValueError("예상하지 못한 MLP Head 구조입니다.")

    encoder = embedding_gemma.build_model(checkpoint).eval()
    model = EmbeddingGemmaActionability(encoder, sklearn_head).eval()
    sample_inputs = (
        torch.ones((1, SEQUENCE_LENGTH), dtype=torch.long),
        torch.ones((1, SEQUENCE_LENGTH), dtype=torch.long),
    )
    with torch.inference_mode():
        sample_output = model(*sample_inputs)
    if sample_output.shape != (1, len(LABELS)):
        raise ValueError(f"예상하지 못한 출력 크기: {sample_output.shape}")
    if not torch.allclose(sample_output.sum(dim=1), torch.ones(1), atol=1e-5):
        raise ValueError("출력 확률 합이 1이 아닙니다.")

    edge_model = litert_torch.convert(
        model,
        sample_inputs,
        quant_config=quant_recipes.full_dynamic_recipe(model.config),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    target = args.output_dir / MODEL_FILENAME
    edge_model.export(str(target))

    tokenizer_dir = args.output_dir / "tokenizer"
    tokenizer_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for name in TOKENIZER_FILES:
        source = checkpoint / name
        if source.exists():
            destination = tokenizer_dir / name
            shutil.copy2(source, destination)
            copied.append(name)

    build = {
        "model_id": MODEL_ID,
        "sequence_length": SEQUENCE_LENGTH,
        "classification_prefix": CLASSIFICATION_PREFIX,
        "labels": LABELS,
        "output": "probabilities",
        "head": "MLP 768 -> 32 ReLU -> 3 Softmax",
        "quantization": "LiteRT full dynamic INT8 recipe",
        "model_file": target.name,
        "model_bytes": target.stat().st_size,
        "model_sha256": sha256(target),
        "head_file": str(HEAD_PATH.relative_to(PROJECT_DIR)),
        "head_sha256": sha256(HEAD_PATH),
        "tokenizer_files": copied,
    }
    (args.output_dir / "build_metadata.json").write_text(
        json.dumps(build, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(build, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
