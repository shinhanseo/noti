import argparse
from pathlib import Path

import joblib


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = (
    PROJECT_DIR
    / "models"
    / "noti_char_tfidf_mlp_v0.2.joblib"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="저장된 noti. 알림 중요도 모델로 한 건을 예측합니다."
    )
    parser.add_argument("--title", required=True, help="알림 제목")
    parser.add_argument("--body", required=True, help="알림 본문")
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help="joblib 모델 경로",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pipeline = joblib.load(args.model)
    text = f"{args.title.strip()} {args.body.strip()}"
    probability = float(pipeline.predict_proba([text])[0, 1])
    prediction = "PROMOTE" if probability >= 0.5 else "KEEP"

    print(f"입력: {text}")
    print(f"중요 확률: {probability:.6f}")
    print(f"예측: {prediction}")


if __name__ == "__main__":
    main()
