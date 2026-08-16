"""Benchmark converted LiteRT embedding models on one connected Android device."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path


METRIC_PATTERNS = {
    "initialization_ms": r"Model initialization:\s+([0-9.]+) ms",
    "first_warmup_ms": r"Warmup \(first\):\s+([0-9.]+) ms",
    "average_warmup_ms": r"Warmup \(avg\):\s+([0-9.]+) ms",
    "average_inference_ms": r"Inference \(avg\):\s+([0-9.]+) ms",
    "minimum_inference_ms": r"Inference \(min\):\s+([0-9.]+) ms",
    "maximum_inference_ms": r"Inference \(max\):\s+([0-9.]+) ms",
    "inference_std_ms": r"Inference \(std\):\s+([0-9.]+)",
    "initial_footprint_mb": r"Init footprint:\s+([0-9.]+) MB",
    "overall_footprint_mb": r"Overall footprint:\s+([0-9.]+) MB",
}


def run(command: list[str], *, capture: bool = True) -> str:
    completed = subprocess.run(
        command,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
    )
    return completed.stdout or ""


def adb_command(adb: str, serial: str | None, *command: str) -> list[str]:
    target = ["-s", serial] if serial else []
    return [adb, *target, *command]


def adb_value(adb: str, serial: str | None, *command: str) -> str:
    return run(adb_command(adb, serial, "shell", *command)).strip()


def parse_metrics(output: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for name, pattern in METRIC_PATTERNS.items():
        match = re.search(pattern, output)
        if match:
            metrics[name] = float(match.group(1))
    if "average_inference_ms" not in metrics:
        raise RuntimeError(f"Benchmark summary was not found:\n{output[-4000:]}")
    return metrics


def median_metrics(trials: list[dict[str, float]]) -> dict[str, float]:
    keys = sorted({key for trial in trials for key in trial})
    return {
        key: statistics.median(trial[key] for trial in trials if key in trial)
        for key in keys
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+", type=Path)
    parser.add_argument("--adb", required=True)
    parser.add_argument("--serial")
    parser.add_argument("--benchmark-binary", type=Path, required=True)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--warmup-runs", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/reports/litert_android_emulator_benchmark_v1.json"),
    )
    args = parser.parse_args()

    remote_dir = "/data/local/tmp/noti-litert-benchmark"
    remote_binary = f"{remote_dir}/benchmark_model"
    run(adb_command(args.adb, args.serial, "shell", "mkdir", "-p", remote_dir))
    run(
        adb_command(
            args.adb, args.serial, "push", str(args.benchmark_binary), remote_binary
        )
    )
    run(adb_command(args.adb, args.serial, "shell", "chmod", "+x", remote_binary))

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "device": {
            "serial": run(
                adb_command(args.adb, args.serial, "get-serialno")
            ).strip(),
            "model": adb_value(
                args.adb, args.serial, "getprop", "ro.product.model"
            ),
            "abi": adb_value(
                args.adb, args.serial, "getprop", "ro.product.cpu.abi"
            ),
            "android_version": adb_value(
                args.adb, args.serial, "getprop", "ro.build.version.release"
            ),
            "sdk": adb_value(
                args.adb, args.serial, "getprop", "ro.build.version.sdk"
            ),
        },
        "conditions": {
            "accelerator": "CPU (XNNPACK)",
            "sequence_length": 64,
            "input_ids_range": [1, 100],
            "attention_mask_range": [1, 1],
            "trials": args.trials,
            "runs_per_trial": args.runs,
            "warmup_runs_per_trial": args.warmup_runs,
        },
        "models": [],
    }

    try:
        for model_path in args.models:
            model_path = model_path.resolve()
            remote_model = f"{remote_dir}/{model_path.name}"
            run(
                adb_command(
                    args.adb, args.serial, "push", str(model_path), remote_model
                )
            )
            trials = []
            for trial_index in range(args.trials):
                output = run(
                    adb_command(
                        args.adb,
                        args.serial,
                        "shell",
                        remote_binary,
                        f"--graph={remote_model}",
                        f"--num_runs={args.runs}",
                        f"--warmup_runs={args.warmup_runs}",
                        "--min_secs=0",
                        "--warmup_min_secs=0",
                        "--max_secs=150",
                        "--input_layer_value_range=serving_default_args_0,1,100:serving_default_args_1,1,1",
                    )
                )
                metrics = parse_metrics(output)
                metrics["trial"] = trial_index + 1
                trials.append(metrics)
                print(
                    f"{model_path.name} trial {trial_index + 1}: "
                    f"{metrics['average_inference_ms']:.2f} ms"
                )
            run(adb_command(args.adb, args.serial, "shell", "rm", remote_model))
            report["models"].append(
                {
                    "name": model_path.name,
                    "path": str(model_path),
                    "size_bytes": model_path.stat().st_size,
                    "trials": trials,
                    "median": median_metrics(trials),
                }
            )
    finally:
        run(adb_command(args.adb, args.serial, "shell", "rm", "-rf", remote_dir))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"saved: {args.output}")


if __name__ == "__main__":
    main()
