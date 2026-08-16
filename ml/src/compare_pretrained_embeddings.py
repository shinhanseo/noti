import argparse
import hashlib
import json
import platform
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean, pstdev

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    brier_score_loss,
    confusion_matrix,
    log_loss,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.neural_network import MLPClassifier

from evaluate_stability import RANDOM_STATES
from train_baseline import load_training_data


PROJECT_DIR = Path(__file__).resolve().parents[1]
CACHE_DIR = PROJECT_DIR / ".cache" / "pretrained_embeddings"


@dataclass(frozen=True)
class EmbeddingCandidate:
    name: str
    model_id: str
    text_prefix: str
    max_sequence_length: int
    notes: str


CANDIDATES = {
    "multilingual_e5_small": EmbeddingCandidate(
        name="multilingual_e5_small",
        model_id="intfloat/multilingual-e5-small",
        text_prefix="query: ",
        max_sequence_length=64,
        notes="1순위 균형 후보. 분류 특징에는 query 접두사를 사용한다.",
    ),
    "paraphrase_multilingual_minilm_l12": EmbeddingCandidate(
        name="paraphrase_multilingual_minilm_l12",
        model_id=(
            "sentence-transformers/"
            "paraphrase-multilingual-MiniLM-L12-v2"
        ),
        text_prefix="",
        max_sequence_length=64,
        notes=(
            "EmbeddingGemma 인증 차단 시 사용하는 공개 다국어 비교 후보. "
            "문장 유사도 목적의 384차원 모델이다."
        ),
    ),
    "embeddinggemma_300m": EmbeddingCandidate(
        name="embeddinggemma_300m",
        model_id="google/embeddinggemma-300m",
        text_prefix="task: classification | query: ",
        max_sequence_length=64,
        notes=(
            "정확도 상한 후보. Hugging Face에서 Gemma 사용 약관 동의와 "
            "로그인이 필요할 수 있다."
        ),
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="사전학습 문장 임베딩 + 얕은 분류기 비교 실험"
    )
    parser.add_argument(
        "--dataset-version",
        default="0.3",
        choices=("0.2", "0.3"),
        help="실험에 사용할 noti 데이터셋 버전",
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=sorted(CANDIDATES),
        default=list(CANDIDATES),
        help="평가할 임베딩 후보",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="random_state=42 한 번만 실행",
    )
    parser.add_argument(
        "--force-embeddings",
        action="store_true",
        help="기존 임베딩 캐시를 무시하고 다시 생성",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="이미 다운로드된 모델만 사용",
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="기존 TF-IDF + MLP 기준선을 결과에서 제외",
    )
    return parser.parse_args()


def dataset_fingerprint(texts: list[str]) -> str:
    digest = hashlib.sha256()
    for text in texts:
        digest.update(text.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def cache_path(
    candidate: EmbeddingCandidate,
    fingerprint: str,
) -> Path:
    safe_model_id = candidate.model_id.replace("/", "__")
    filename = (
        f"{safe_model_id}_seq{candidate.max_sequence_length}_"
        f"{fingerprint[:12]}.npz"
    )
    return CACHE_DIR / filename


def source_snapshot_size(model_id: str) -> int:
    from huggingface_hub import snapshot_download

    snapshot = Path(
        snapshot_download(
            repo_id=model_id,
            local_files_only=True,
        )
    )
    return sum(
        path.stat().st_size
        for path in snapshot.rglob("*")
        if path.is_file()
    )


def create_embeddings(
    candidate: EmbeddingCandidate,
    texts: list[str],
    fingerprint: str,
    force: bool,
    local_files_only: bool,
) -> tuple[np.ndarray, dict[str, object]]:
    target = cache_path(candidate, fingerprint)
    if target.exists() and not force:
        started = time.perf_counter()
        cached = np.load(target)
        embeddings = cached["embeddings"]
        return embeddings, {
            "cache_hit": True,
            "embedding_seconds": time.perf_counter() - started,
            "source_snapshot_bytes": source_snapshot_size(
                candidate.model_id
            ),
            "cache_path": str(target.relative_to(PROJECT_DIR)),
        }

    from sentence_transformers import SentenceTransformer

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    load_started = time.perf_counter()
    model = SentenceTransformer(
        candidate.model_id,
        device="cpu",
        local_files_only=local_files_only,
    )
    model.max_seq_length = candidate.max_sequence_length
    model_load_seconds = time.perf_counter() - load_started

    prepared_texts = [candidate.text_prefix + text for text in texts]
    encode_started = time.perf_counter()
    embeddings = model.encode(
        prepared_texts,
        batch_size=16,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype(np.float32)
    embedding_seconds = time.perf_counter() - encode_started

    np.savez_compressed(target, embeddings=embeddings)
    return embeddings, {
        "cache_hit": False,
        "model_load_seconds": model_load_seconds,
        "embedding_seconds": embedding_seconds,
        "sentences_per_second": len(texts) / embedding_seconds,
        "source_snapshot_bytes": source_snapshot_size(candidate.model_id),
        "cache_path": str(target.relative_to(PROJECT_DIR)),
    }


def make_heads(random_state: int) -> dict[str, object]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=2000,
            random_state=random_state,
        ),
        "mlp_32": MLPClassifier(
            hidden_layer_sizes=(32,),
            activation="relu",
            alpha=0.0001,
            max_iter=1000,
            random_state=random_state,
        ),
    }


def evaluate_head(
    embeddings: np.ndarray,
    labels: np.ndarray,
    groups: np.ndarray,
    head_name: str,
    random_states: tuple[int, ...],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for random_state in random_states:
        splitter = StratifiedGroupKFold(
            n_splits=5,
            shuffle=True,
            random_state=random_state,
        )
        predictions = np.full(len(labels), -1, dtype=int)
        probabilities = np.full(len(labels), -1.0, dtype=float)
        maximum_group_overlap = 0

        for train_index, test_index in splitter.split(
            embeddings,
            y=labels,
            groups=groups,
        ):
            train_groups = set(groups[train_index])
            test_groups = set(groups[test_index])
            maximum_group_overlap = max(
                maximum_group_overlap,
                len(train_groups & test_groups),
            )

            model = make_heads(random_state)[head_name]
            model.fit(embeddings[train_index], labels[train_index])
            predictions[test_index] = model.predict(embeddings[test_index])
            probabilities[test_index] = model.predict_proba(
                embeddings[test_index]
            )[:, 1]

        if np.any(predictions < 0) or np.any(probabilities < 0.0):
            raise RuntimeError("일부 데이터에 out-of-fold 예측이 없습니다.")

        matrix = confusion_matrix(labels, predictions, labels=[0, 1])
        rows.append(
            {
                "random_state": random_state,
                "accuracy": float(np.mean(predictions == labels)),
                "precision": float(precision_score(labels, predictions)),
                "recall": float(recall_score(labels, predictions)),
                "brier_score": float(
                    brier_score_loss(labels, probabilities)
                ),
                "log_loss": float(log_loss(labels, probabilities)),
                "false_positive": int(matrix[0, 1]),
                "false_negative": int(matrix[1, 0]),
                "maximum_group_overlap": maximum_group_overlap,
            }
        )

    return rows


def fitted_head_size(
    embeddings: np.ndarray,
    labels: np.ndarray,
    head_name: str,
) -> int:
    model = make_heads(42)[head_name]
    model.fit(embeddings, labels)
    target = CACHE_DIR / f"temporary_{head_name}.joblib"
    joblib.dump(model, target, compress=3)
    size_bytes = target.stat().st_size
    target.unlink()
    return size_bytes


def summarize(
    candidate: EmbeddingCandidate,
    head_name: str,
    rows: list[dict[str, object]],
    embeddings: np.ndarray,
    labels: np.ndarray,
    timing: dict[str, object],
) -> dict[str, object]:
    accuracies = [float(row["accuracy"]) for row in rows]
    return {
        "candidate": candidate.name,
        "model_id": candidate.model_id,
        "head": head_name,
        "embedding_dimensions": int(embeddings.shape[1]),
        "max_sequence_length": candidate.max_sequence_length,
        "text_prefix": candidate.text_prefix,
        "accuracy_mean": mean(accuracies),
        "accuracy_std": pstdev(accuracies),
        "accuracy_min": min(accuracies),
        "accuracy_max": max(accuracies),
        "precision_mean": mean(float(row["precision"]) for row in rows),
        "recall_mean": mean(float(row["recall"]) for row in rows),
        "brier_score_mean": mean(
            float(row["brier_score"]) for row in rows
        ),
        "log_loss_mean": mean(float(row["log_loss"]) for row in rows),
        "false_positive_mean": mean(
            int(row["false_positive"]) for row in rows
        ),
        "false_negative_mean": mean(
            int(row["false_negative"]) for row in rows
        ),
        "maximum_group_overlap": max(
            int(row["maximum_group_overlap"]) for row in rows
        ),
        "head_joblib_size_bytes": fitted_head_size(
            embeddings,
            labels,
            head_name,
        ),
        "artifact_size_scope": "classifier_head_only",
        "source_model_size_bytes": int(timing["source_snapshot_bytes"]),
        "timing": timing,
        "runs": rows,
    }


def load_tfidf_baseline(
    random_states: tuple[int, ...],
    lightweight_result_path: Path,
) -> dict[str, object]:
    payload = json.loads(lightweight_result_path.read_text(encoding="utf-8"))
    source = next(
        row
        for row in payload["candidates"]
        if row["name"] == "char_tfidf_mlp"
    )
    rows = [
        row
        for row in source["runs"]
        if int(row["random_state"]) in random_states
    ]
    if len(rows) != len(random_states):
        raise RuntimeError("기준선 결과에 요청한 random_state가 모두 없습니다.")

    accuracies = [float(row["accuracy"]) for row in rows]
    return {
        "candidate": "char_tfidf",
        "model_id": "scikit-learn/TfidfVectorizer",
        "head": "mlp_32",
        "embedding_dimensions": int(source["feature_count"]),
        "max_sequence_length": None,
        "text_prefix": "",
        "accuracy_mean": mean(accuracies),
        "accuracy_std": pstdev(accuracies),
        "accuracy_min": min(accuracies),
        "accuracy_max": max(accuracies),
        "precision_mean": mean(float(row["precision"]) for row in rows),
        "recall_mean": mean(float(row["recall"]) for row in rows),
        "brier_score_mean": mean(
            float(row["brier_score"]) for row in rows
        ),
        "log_loss_mean": mean(float(row["log_loss"]) for row in rows),
        "false_positive_mean": mean(
            int(row["false_positive"]) for row in rows
        ),
        "false_negative_mean": mean(
            int(row["false_negative"]) for row in rows
        ),
        "maximum_group_overlap": max(
            int(row["maximum_group_overlap"]) for row in rows
        ),
        "head_joblib_size_bytes": int(source["joblib_size_bytes"]),
        "artifact_size_scope": "full_python_pipeline",
        "source_model_size_bytes": int(source["joblib_size_bytes"]),
        "timing": {"source_report": str(lightweight_result_path.name)},
        "runs": rows,
    }


def friendly_failure(
    candidate: EmbeddingCandidate,
    error: Exception,
) -> str:
    message = str(error).replace("\n", " ")
    if candidate.name == "embeddinggemma_300m":
        return (
            "Hugging Face에서 Gemma 사용 약관에 동의하고 인증한 계정이 "
            "필요해 모델 파일을 내려받지 못했습니다."
        )
    if "couldn't find them in the cached files" in message.lower():
        return (
            "모델이 로컬 캐시에 없고 offline 실행을 사용해 이번 실험에서는 "
            "가중치를 불러오지 못했습니다."
        )
    return message[:1000]


def create_report(result: dict[str, object]) -> str:
    summaries = result["summaries"]
    failures = result["failures"]
    lines = [
        f"# v{result['dataset_version']} 사전학습 Embedding Bake-off",
        "",
        "## 실험 목적",
        "",
        f"동일한 v{result['dataset_version']} 검토 완료 REVIEW 데이터 "
        f"{result['dataset_rows']}개와 `template_group` 기반 분할을 "
        "사용해 사전학습 문장 Embedding과 얕은 분류기 조합을 비교한다.",
        "Embedding 모델은 고정하고 분류기만 각 Fold에서 학습한다.",
        "",
        "## 결과",
        "",
        "| 순위 | 특징 생성 | 분류기 | 평균 정확도 | 최저 정확도 | "
        "Precision | Recall | Brier | 평균 FP | 평균 FN | 차원 | 원본 크기 | "
        "분류 Head |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for rank, row in enumerate(summaries, start=1):
        lines.append(
            f"| {rank} | `{row['candidate']}` | `{row['head']}` | "
            f"{row['accuracy_mean']:.1%} | {row['accuracy_min']:.1%} | "
            f"{row['precision_mean']:.3f} | {row['recall_mean']:.3f} | "
            f"{row['brier_score_mean']:.3f} | "
            f"{row['false_positive_mean']:.1f} | "
            f"{row['false_negative_mean']:.1f} | "
            f"{row['embedding_dimensions']} | "
            f"{row['source_model_size_bytes'] / 1024 / 1024:.1f} MiB | "
            f"{row['head_joblib_size_bytes'] / 1024:.1f} KiB "
            f"({row['artifact_size_scope']}) |"
        )

    if failures:
        lines.extend(["", "## 실행하지 못한 후보", ""])
        for failure in failures:
            lines.append(
                f"- `{failure['candidate']}`: {failure['error_type']} - "
                f"{failure['message']}"
            )

    lines.extend(
        [
            "",
            "## 해석 제한",
            "",
            f"- 현재 데이터는 합성 중심 데이터 {result['dataset_rows']}개이므로 실제 알림 성능을 "
            "증명하지 않는다.",
            "- Embedding을 전체 데이터에 미리 생성하지만 라벨을 사용하지 않는 "
            "고정 사전학습 모델이므로 지도학습 라벨 누수는 없다.",
            "- 기준선은 기존 동일 20회 실험 결과를 불러오며, Embedding 후보의 "
            "저장 크기는 분류 Head만 포함한다.",
            "- 표의 저장 크기는 Python Joblib 크기이며 최종 LiteRT 모델 크기가 아니다.",
            "- Embedding 원본 크기는 로컬 Hugging Face 스냅샷의 미양자화 "
            "가중치와 토크나이저 등을 합한 값이다.",
            "- Embedding 생성 시간은 개발 Mac CPU 측정값이며 Android 성능이 아니다.",
            "- 최종 선택 전 실제 익명화 알림 평가와 INT8 LiteRT 기기 측정이 필요하다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    _, data = load_training_data(args.dataset_version)
    report_path = (
        PROJECT_DIR
        / "reports"
        / f"v{args.dataset_version}_pretrained_embedding_bakeoff.md"
    )
    result_path = (
        PROJECT_DIR
        / "reports"
        / f"v{args.dataset_version}_pretrained_embedding_bakeoff.json"
    )
    lightweight_result_path = (
        PROJECT_DIR
        / "reports"
        / f"v{args.dataset_version}_lightweight_model_bakeoff.json"
    )
    texts = data["text"].tolist()
    labels = data["label"].to_numpy(dtype=int)
    groups = data["template_group"].to_numpy()
    fingerprint = dataset_fingerprint(texts)
    random_states = (42,) if args.quick else tuple(RANDOM_STATES)

    result: dict[str, object] = {
        "dataset_version": args.dataset_version,
        "dataset_rows": len(data),
        "dataset_fingerprint": fingerprint,
        "random_states": list(random_states),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
        },
        "candidates": [asdict(CANDIDATES[name]) for name in args.models],
        "summaries": [],
        "failures": [],
    }

    if not args.no_baseline:
        result["summaries"].append(
            load_tfidf_baseline(random_states, lightweight_result_path)
        )

    for candidate_name in args.models:
        candidate = CANDIDATES[candidate_name]
        print(f"\nEmbedding 생성: {candidate.model_id}")
        try:
            embeddings, timing = create_embeddings(
                candidate,
                texts,
                fingerprint,
                force=args.force_embeddings,
                local_files_only=args.local_files_only,
            )
            if embeddings.shape[0] != len(data):
                raise RuntimeError("Embedding 행 수가 데이터 행 수와 다릅니다.")

            for head_name in make_heads(42):
                print(f"교차 검증: {candidate.name} + {head_name}")
                rows = evaluate_head(
                    embeddings,
                    labels,
                    groups,
                    head_name,
                    random_states,
                )
                result["summaries"].append(
                    summarize(
                        candidate,
                        head_name,
                        rows,
                        embeddings,
                        labels,
                        timing,
                    )
                )
        except Exception as error:  # 후보 하나의 실패로 전체 실험을 중단하지 않는다.
            print(f"후보 실행 실패: {candidate.name}: {error}")
            result["failures"].append(
                {
                    "candidate": candidate.name,
                    "model_id": candidate.model_id,
                    "error_type": type(error).__name__,
                    "message": friendly_failure(candidate, error),
                }
            )

    result["summaries"].sort(
        key=lambda row: (
            row["accuracy_mean"],
            row["recall_mean"],
            -row["head_joblib_size_bytes"],
        ),
        reverse=True,
    )

    report_path.write_text(create_report(result), encoding="utf-8")
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n보고서: {report_path}")
    print(f"상세 결과: {result_path}")


if __name__ == "__main__":
    main()
