from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_DIR
    / "data"
    / "public"
    / "train_notifications.csv"
)


def main() -> None:
    data = pd.read_csv(DATA_PATH)

    print("데이터 크기")
    print(data.shape)

    print("\nColumn 목록")
    print(data.columns.tolist())

    print("\n처음 5개 알림")
    print(
        data[
            [
                "title",
                "body",
                "label",
                "group",
            ]
        ].head()
    )

    print("\nLabel 개수")
    print(
        data["label"]
        .value_counts()
        .sort_index()
    )

    print("\n비어 있는 값 개수")
    print(
        data[
            [
                "title",
                "body",
                "label",
            ]
        ].isna().sum()
    )


if __name__ == "__main__":
    main()