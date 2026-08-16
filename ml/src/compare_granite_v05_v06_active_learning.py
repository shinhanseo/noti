"""Compare v0.5/v0.6 Granite thin heads on CV and reviewed Room cases."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score

import experiment_embeddinggemma_actionability_v05 as experiment
from actionability_contract import (
    ACTIONABILITY_LABELS,
    ACTIONABILITY_TO_ID,
    encode_actionability,
    predicted_actionability,
)
from notification_text_preprocessor import normalize_notification_text


PROJECT_DIR = Path(__file__).resolve().parents[1]
V05_PATH = PROJECT_DIR / "data" / "public" / "train_notifications_v0.5.csv"
V06_PATH = PROJECT_DIR / "data" / "public" / "train_notifications_v0.6.csv"
ACTIVE_PATH = (
    PROJECT_DIR
    / "data"
    / "private"
    / "room_export_2026-08-12_raw"
    / "active_learning_review_40.csv"
)
JSON_OUTPUT = PROJECT_DIR / "reports" / "granite_v05_v06_active_learning.json"
MARKDOWN_OUTPUT = PROJECT_DIR / "reports" / "granite_v05_v06_active_learning.md"
MODEL_ID = "ibm-granite/granite-embedding-97m-multilingual-r2"


def load_active() -> pd.DataFrame:
    data = pd.read_csv(ACTIVE_PATH).fillna("")
    if not data["user_common_actionability"].isin(ACTIONABILITY_LABELS).all():
        raise ValueError("Active Learning 공통 라벨이 비었거나 잘못되었습니다.")
    data["text"] = [
        normalize_notification_text(package, title, body)
        for package, title, body in zip(
            data["package_name"], data["title"], data["body"]
        )
    ]
    data["actionability_id"] = data["user_common_actionability"].map(
        ACTIONABILITY_TO_ID
    ).astype(np.int32)
    return data


def embed_all(
    v05: pd.DataFrame, v06: pd.DataFrame, active: pd.DataFrame
) -> dict[str, np.ndarray]:
    texts = list(dict.fromkeys([*v06["text"], *active["text"]]))
    experiment.MODEL_ID = MODEL_ID
    experiment.CLASSIFICATION_PREFIX = ""
    vectors, _, model = experiment.create_embeddings(
        texts, force=False, local_files_only=True
    )
    del model
    positions = {text: index for index, text in enumerate(texts)}
    return {
        "v05": vectors[[positions[text] for text in v05["text"]]],
        "v06": vectors[[positions[text] for text in v06["text"]]],
        "active": vectors[[positions[text] for text in active["text"]]],
    }


def metrics(actual: np.ndarray, probabilities: np.ndarray) -> dict[str, object]:
    predicted = np.argmax(probabilities, axis=1)
    actual_important = actual != 0
    predicted_important = predicted != 0
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_f1": float(f1_score(actual, predicted, average="macro")),
        "confusion_matrix": confusion_matrix(actual, predicted, labels=[0, 1, 2]).tolist(),
        "important_false_positive": int((~actual_important & predicted_important).sum()),
        "important_false_negative": int((actual_important & ~predicted_important).sum()),
        "important_recall": float(
            (actual_important & predicted_important).sum() / actual_important.sum()
        ),
        "predicted_counts": {
            label: int((predicted == index).sum())
            for index, label in enumerate(ACTIONABILITY_LABELS)
        },
    }


def evaluate_dataset(
    data: pd.DataFrame,
    vectors: np.ndarray,
    active: pd.DataFrame,
    active_vectors: np.ndarray,
) -> dict[str, object]:
    labels = data["actionability_id"].to_numpy(dtype=np.int32)
    folds = data["cv_fold"].to_numpy(dtype=np.int32)
    oof = np.zeros((len(data), 3), dtype=np.float64)
    for fold in sorted(np.unique(folds)):
        train = folds != fold
        validation = folds == fold
        head = experiment.make_head("mlp_32")
        experiment.fit_head(head, "mlp_32", vectors[train], labels[train])
        oof[validation] = head.predict_proba(vectors[validation])

    final_head = experiment.make_head("mlp_32")
    experiment.fit_head(final_head, "mlp_32", vectors, labels)
    active_probability = final_head.predict_proba(active_vectors)
    active_labels = active["actionability_id"].to_numpy(dtype=np.int32)
    return {
        "training_rows": int(len(data)),
        "cross_validation": metrics(labels, oof),
        "active_learning_development": metrics(active_labels, active_probability),
        "active_predictions": predicted_actionability(active_probability),
    }


def markdown(results: dict[str, object]) -> str:
    v05 = results["v0.5"]
    v06 = results["v0.6"]
    lines = [
        "# Granite v0.5 → v0.6 데이터 교정 실험",
        "",
        "같은 Granite Embedding 97M R2와 같은 MLP head를 사용하고 학습 데이터만 바꿨다.",
        "",
        "## 결과",
        "",
        "| 데이터 | 학습 행 | 합성 CV 정확도 | 합성 CV Macro F1 | 실제 40개 일치율 | 실제 일반→중요 오판 | 실제 중요 Recall |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, value in (("v0.5", v05), ("v0.6", v06)):
        cv = value["cross_validation"]
        active = value["active_learning_development"]
        lines.append(
            f"| {name} | {value['training_rows']} | {cv['accuracy']:.3f} | "
            f"{cv['macro_f1']:.3f} | {active['accuracy']:.3f} | "
            f"{active['important_false_positive']} | {active['important_recall']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## 주의",
            "",
            "실제 40개는 v0.6 오류 유형 설계에 사용한 개발 세트다. 독립 테스트 점수로 주장할 수 없다.",
            "v0.6 채택 여부는 새로운 시점의 미사용 실제 라벨로 다시 확인해야 한다.",
            "개인 선호 라벨은 공통 모델 학습이나 이 표의 정답으로 사용하지 않았다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    v05 = experiment.load_training_data(V05_PATH)
    v06 = experiment.load_training_data(V06_PATH)
    active = load_active()
    vectors = embed_all(v05, v06, active)
    results = {
        "model_id": MODEL_ID,
        "head": "mlp_32",
        "active_learning_rows": len(active),
        "v0.5": evaluate_dataset(v05, vectors["v05"], active, vectors["active"]),
        "v0.6": evaluate_dataset(v06, vectors["v06"], active, vectors["active"]),
    }
    JSON_OUTPUT.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    MARKDOWN_OUTPUT.write_text(markdown(results), encoding="utf-8")
    print(markdown(results))


if __name__ == "__main__":
    main()
