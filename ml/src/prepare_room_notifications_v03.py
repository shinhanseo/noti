import argparse
import csv
import re
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_DIR / "data" / "private" / "room_notifications_anonymized_v0.3.csv"

OUTPUT_FIELDS = [
    "id", "app_name", "package_name", "title", "body", "label",
    "notification_type", "template_group", "clarity", "reason_code",
    "android_category", "is_ongoing", "rule_score", "rule_level",
    "forced", "model_eligible", "source", "dataset_version",
    "source_detail", "source_url", "license", "is_real", "is_public",
    "label_status", "original_source_id",
]


def mask_private_text(value: str) -> str:
    value = value.strip()
    value = re.sub(r"https?://\S+", "<URL>", value)
    value = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<EMAIL>", value)
    value = re.sub(r"(?<!\d)01[016789][- ]?\d{3,4}[- ]?\d{4}(?!\d)", "<PHONE>", value)
    value = re.sub(r"(?<!\d)0\d{1,2}[- ]\d{3,4}[- ]\d{4}(?!\d)", "<PHONE>", value)
    value = re.sub(r"(?<!\d)(?:\d[- ]?){12,18}\d(?!\d)", "<ACCOUNT_OR_CARD>", value)
    value = re.sub(
        r"(?<!\d)(?:\d{1,3}(?:,\d{3})+|\d{4,8})(?=\s*(?:원|KRW))",
        "<AMOUNT>",
        value,
    )
    value = re.sub(
        r"(예금|적금|계좌|입금|출금)(\([^)]*\))\s+[가-힣]{2,4}(?=\s+\d{2}[/:])",
        r"\1(<ACCOUNT_SUFFIX>) <NAME>",
        value,
    )
    value = re.sub(r"(?i)(인증번호|인증코드|verification code)(\s*[:은는]?\s*)\d{4,8}", r"\1\2<CODE>", value)
    return re.sub(r"\s+", " ", value)


def first_existing(row: dict[str, str], names: list[str]) -> str:
    for name in names:
        if name and name in row:
            return row.get(name, "") or ""
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Room 알림 CSV를 익명화된 v0.3 후보로 변환합니다.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--title-column", default="title")
    parser.add_argument("--body-column", default="body")
    parser.add_argument("--app-column", default="app_name")
    parser.add_argument("--package-column", default="package_name")
    parser.add_argument("--id-column", default="id")
    args = parser.parse_args()

    with args.input.open(encoding="utf-8-sig", newline="") as csv_file:
        source_rows = list(csv.DictReader(csv_file))

    output_rows = []
    empty_count = 0
    for index, row in enumerate(source_rows, start=1):
        title = mask_private_text(first_existing(row, [args.title_column, "notification_title"]))
        body = mask_private_text(first_existing(row, [args.body_column, "text", "content", "notification_body"]))
        if not title and not body:
            empty_count += 1
            continue
        original_id = first_existing(row, [args.id_column, "notification_id"]) or str(index)
        output_rows.append(
            {
                "id": f"V03_ROOM_{index:06d}",
                "app_name": first_existing(row, [args.app_column, "app", "application_name"]),
                "package_name": first_existing(row, [args.package_column, "package", "sbn_package_name"]),
                "title": title,
                "body": body,
                "label": "",
                "notification_type": "unreviewed_real",
                "template_group": "",
                "clarity": "UNREVIEWED",
                "reason_code": "awaiting_human_review",
                "android_category": "",
                "is_ongoing": "false",
                "rule_score": "",
                "rule_level": "",
                "forced": "false",
                "model_eligible": "false",
                "source": "REAL_PRIVATE_UNLABELED",
                "dataset_version": "0.3",
                "source_detail": "room_export_anonymized",
                "source_url": "",
                "license": "PRIVATE_USER_DATA",
                "is_real": "true",
                "is_public": "false",
                "label_status": "UNLABELED",
                "original_source_id": original_id,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8-sig", newline="") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=OUTPUT_FIELDS,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print("Room 알림 익명화 완료")
    print(f"입력 행: {len(source_rows)}")
    print(f"출력 행: {len(output_rows)}")
    print(f"제외된 빈 알림: {empty_count}")
    print(f"저장 위치: {args.output}")
    print("개인정보 보호를 위해 알림 원문은 출력하지 않았습니다.")


if __name__ == "__main__":
    main()
