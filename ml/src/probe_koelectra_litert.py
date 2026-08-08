"""Probe whether KoELECTRA-small can be exported to a LiteRT/TFLite model.

This script intentionally does not train a useful classifier. It attaches a
random two-class head to the pretrained encoder and verifies the deployment
path before we spend time fine-tuning it.
"""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import nn
from transformers import AutoModelForSequenceClassification, AutoTokenizer


DEFAULT_MODEL = "monologg/koelectra-small-v3-discriminator"
DEFAULT_TEXT = "쿠팡 주문하신 상품이 배송을 시작했습니다."


def default_output_dir() -> Path:
    script_path = globals().get("__file__")
    if script_path:
        return Path(script_path).resolve().parents[1] / "models" / "koelectra_litert_probe"
    return Path.cwd() / "koelectra_litert_probe"


class KoElectraForLiteRT(nn.Module):
    """Expose only fixed-shape tensors and logits to the converter."""

    def __init__(self, classifier: nn.Module) -> None:
        super().__init__()
        self.classifier = classifier

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: torch.Tensor,
    ) -> torch.Tensor:
        return self.classifier(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            return_dict=False,
        )[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--seq-len", type=int, default=64)
    parser.add_argument("--atol", type=float, default=1e-3)
    parser.add_argument("--text", default=DEFAULT_TEXT)
    parser.add_argument(
        "--attention-implementation",
        default="eager",
        choices=("eager", "sdpa"),
        help="Use eager attention by default for a simpler mobile conversion graph.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=default_output_dir(),
    )
    parser.add_argument(
        "--inspect-only",
        action="store_true",
        help="Load and inspect the model without importing LiteRT Torch.",
    )
    parser.add_argument(
        "--skip-torch-export",
        action="store_true",
        help="Skip the local torch.export compatibility check.",
    )
    args, _ = parser.parse_known_args()
    return args


def load_litert_torch() -> Any:
    """Support both the current and former package import names."""
    for module_name in ("litert_torch", "ai_edge_torch"):
        try:
            return importlib.import_module(module_name)
        except ImportError:
            continue
    raise RuntimeError(
        "LiteRT Torch를 찾을 수 없습니다. Linux/Colab의 Python 3.11 환경에서 "
        "`python -m pip install -r requirements-litert.txt`를 실행하세요."
    )


def as_numpy(value: Any) -> np.ndarray:
    if isinstance(value, (tuple, list)):
        value = value[0]
    if isinstance(value, dict):
        value = next(iter(value.values()))
    if isinstance(value, torch.Tensor):
        value = value.detach().cpu().numpy()
    return np.asarray(value)


def main() -> None:
    args = parse_args()
    if args.seq_len <= 0:
        raise ValueError("--seq-len은 1 이상이어야 합니다.")

    torch.manual_seed(42)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    classifier = AutoModelForSequenceClassification.from_pretrained(
        args.model,
        num_labels=2,
        attn_implementation=args.attention_implementation,
    ).eval()
    wrapper = KoElectraForLiteRT(classifier).eval()

    encoded = tokenizer(
        args.text,
        max_length=args.seq_len,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    input_ids = encoded["input_ids"].to(torch.int32)
    attention_mask = encoded["attention_mask"].to(torch.int32)
    token_type_ids = encoded.get(
        "token_type_ids",
        torch.zeros_like(input_ids),
    ).to(torch.int32)
    sample_inputs = (input_ids, attention_mask, token_type_ids)

    with torch.inference_mode():
        torch_logits = wrapper(*sample_inputs)

    parameter_count = sum(parameter.numel() for parameter in classifier.parameters())
    parameter_bytes = sum(
        parameter.numel() * parameter.element_size()
        for parameter in classifier.parameters()
    )
    report: dict[str, Any] = {
        "status": "inspection_complete",
        "purpose": "conversion_probe_only_random_classification_head",
        "model": args.model,
        "sequence_length": args.seq_len,
        "attention_implementation": args.attention_implementation,
        "parameter_count": parameter_count,
        "parameter_size_bytes": parameter_bytes,
        "parameter_size_mib": parameter_bytes / (1024**2),
        "vocabulary_size": tokenizer.vocab_size,
        "input_shapes": [list(tensor.shape) for tensor in sample_inputs],
        "input_dtypes": [str(tensor.dtype) for tensor in sample_inputs],
        "torch_logits": torch_logits.detach().cpu().tolist(),
        "environment": {
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            "torch": torch.__version__,
        },
    }

    print(f"모델: {args.model}")
    print(f"파라미터: {parameter_count:,}")
    print(f"파라미터 메모리(FP32): {report['parameter_size_mib']:.2f} MiB")
    print(f"Vocabulary: {tokenizer.vocab_size:,}")
    print(f"입력 shape: {report['input_shapes']}")
    print(f"PyTorch logits: {report['torch_logits']}")

    exported_program = None
    if not args.skip_torch_export:
        try:
            exported_program = torch.export.export(wrapper, sample_inputs)
            with torch.inference_mode():
                exported_logits = exported_program.module()(*sample_inputs)
        except Exception as error:
            report["torch_export"] = {
                "status": "failed",
                "error_type": type(error).__name__,
                "message": str(error),
            }
            print(f"torch.export 검사: 실패 ({type(error).__name__})")
            print(str(error))
        else:
            torch_export_diff = float(
                np.max(np.abs(as_numpy(torch_logits) - as_numpy(exported_logits)))
            )
            report["torch_export"] = {
                "status": "passed",
                "logits": as_numpy(exported_logits).tolist(),
                "max_absolute_logit_difference": torch_export_diff,
            }
            print("torch.export 검사: 성공")
            print(f"torch.export 최대 logits 차이: {torch_export_diff:.8f}")

    if not args.inspect_only:
        if platform.system() != "Linux":
            raise RuntimeError(
                "LiteRT Torch 변환은 Linux 환경에서 실행하세요. "
                "현재 환경에서는 --inspect-only만 지원합니다."
            )

        litert_torch = load_litert_torch()
        edge_model = litert_torch.convert(wrapper, sample_inputs)
        with torch.inference_mode():
            torch_logits_after_conversion = wrapper(*sample_inputs)
        edge_logits = as_numpy(edge_model(*sample_inputs))
        torch_logits_numpy = as_numpy(torch_logits)
        max_abs_diff = float(np.max(np.abs(torch_logits_numpy - edge_logits)))
        post_conversion_torch_diff = float(
            np.max(
                np.abs(
                    torch_logits_numpy
                    - as_numpy(torch_logits_after_conversion)
                )
            )
        )
        torch_probabilities = torch.softmax(torch_logits, dim=-1)
        edge_probabilities = torch.softmax(
            torch.from_numpy(edge_logits),
            dim=-1,
        )
        probability_diff = float(
            np.max(
                np.abs(
                    as_numpy(torch_probabilities)
                    - as_numpy(edge_probabilities)
                )
            )
        )

        tflite_path = args.output_dir / (
            "koelectra_small_probe_"
            f"{args.attention_implementation}_fp32.tflite"
        )
        edge_model.export(str(tflite_path))
        report.update(
            {
                "status": (
                    "conversion_complete"
                    if max_abs_diff <= args.atol
                    else "conversion_complete_numerical_mismatch"
                ),
                "tflite_path": str(tflite_path),
                "tflite_size_bytes": tflite_path.stat().st_size,
                "edge_logits": edge_logits.tolist(),
                "max_absolute_logit_difference": max_abs_diff,
                "post_conversion_torch_logits": as_numpy(
                    torch_logits_after_conversion
                ).tolist(),
                "post_conversion_torch_max_absolute_difference": (
                    post_conversion_torch_diff
                ),
                "torch_probabilities": as_numpy(torch_probabilities).tolist(),
                "edge_probabilities": as_numpy(edge_probabilities).tolist(),
                "max_absolute_probability_difference": probability_diff,
                "comparison_atol": args.atol,
            }
        )
        print(f"LiteRT logits: {report['edge_logits']}")
        print(f"변환 후 PyTorch logits 차이: {post_conversion_torch_diff:.8f}")
        print(f"최대 logits 차이: {max_abs_diff:.8f}")
        print(f"최대 확률 차이: {probability_diff:.8f}")
        print(f"TFLite 파일: {tflite_path}")
        print(f"TFLite 크기: {tflite_path.stat().st_size / (1024**2):.2f} MiB")

    tokenizer.save_pretrained(args.output_dir / "tokenizer")
    report_path = args.output_dir / "probe_report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"검사 보고서: {report_path}")


if __name__ == "__main__":
    main()
