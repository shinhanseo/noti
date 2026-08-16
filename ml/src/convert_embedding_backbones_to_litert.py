"""Convert the two frozen embedding candidates to fixed-sequence LiteRT files."""

from __future__ import annotations

import argparse
import importlib.machinery
import os
import sys
import types
from pathlib import Path

import torch
from ai_edge_litert import schema_py_generated
from huggingface_hub import snapshot_download


def install_tensorflow_schema_shim() -> None:
    """Avoid loading TensorFlow only for its duplicated TFLite schema module."""
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
from litert_torch.generative.quantize import quant_attrs  # noqa: E402
from litert_torch.generative.quantize import quant_recipes  # noqa: E402
from transformers import AutoModel  # noqa: E402


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_DIR / "models" / "litert_mobile_benchmark"
SEQUENCE_LENGTH = 64


class GraniteEmbedder(torch.nn.Module):
    def __init__(self, checkpoint: Path):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(
            checkpoint,
            dtype=torch.float32,
            attn_implementation="eager",
            local_files_only=True,
        )

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        hidden = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            return_dict=False,
        )[0]
        return torch.nn.functional.normalize(hidden[:, 0, :], p=2, dim=1)


def checkpoint(model_id: str, allow_download: bool) -> Path:
    return Path(
        snapshot_download(repo_id=model_id, local_files_only=not allow_download)
    )


def convert_granite(output_dir: Path, allow_download: bool) -> Path:
    model = GraniteEmbedder(
        checkpoint(
            "ibm-granite/granite-embedding-97m-multilingual-r2", allow_download
        )
    ).eval()
    sample_inputs = (
        torch.ones((1, SEQUENCE_LENGTH), dtype=torch.long),
        torch.ones((1, SEQUENCE_LENGTH), dtype=torch.long),
    )
    edge_model = litert_torch.convert(
        model,
        sample_inputs,
        quant_config=quant_recipes.full_weight_only_recipe(),
    )
    target = output_dir / "granite_97m_seq64_q8_weight_only.tflite"
    edge_model.export(str(target))
    return target


def convert_embeddinggemma(output_dir: Path, allow_download: bool) -> Path:
    model = embedding_gemma.build_model(
        checkpoint("google/embeddinggemma-300m", allow_download)
    ).eval()
    sample_inputs = (
        torch.ones((1, SEQUENCE_LENGTH), dtype=torch.long),
        torch.ones((1, SEQUENCE_LENGTH), dtype=torch.long),
    )
    edge_model = litert_torch.convert(
        model,
        sample_inputs,
        quant_config=quant_recipes.full_dynamic_recipe(model.config),
    )
    target = output_dir / "embeddinggemma_300m_seq64_q8.tflite"
    edge_model.export(str(target))
    return target


def convert_embeddinggemma_int4(output_dir: Path, allow_download: bool) -> Path:
    model = embedding_gemma.build_model(
        checkpoint("google/embeddinggemma-300m", allow_download)
    ).eval()
    sample_inputs = (
        torch.ones((1, SEQUENCE_LENGTH), dtype=torch.long),
        torch.ones((1, SEQUENCE_LENGTH), dtype=torch.long),
    )
    edge_model = litert_torch.convert(
        model,
        sample_inputs,
        quant_config=quant_recipes.full_dynamic_recipe(
            model.config,
            weight_dtype=quant_attrs.Dtype.INT4,
            granularity=quant_attrs.Granularity.BLOCKWISE_32,
        ),
    )
    target = output_dir / "embeddinggemma_300m_seq64_q4_block32.tflite"
    edge_model.export(str(target))
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        choices=("granite", "embeddinggemma", "embeddinggemma_int4", "all"),
        default="all",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--allow-download", action="store_true")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    converters = {
        "granite": convert_granite,
        "embeddinggemma": convert_embeddinggemma,
        "embeddinggemma_int4": convert_embeddinggemma_int4,
    }
    selected = converters if args.model == "all" else {args.model: converters[args.model]}
    for name, converter in selected.items():
        target = converter(args.output_dir, args.allow_download)
        print(f"{name}: {target} ({target.stat().st_size / 1024**2:.1f} MiB)")


if __name__ == "__main__":
    main()
