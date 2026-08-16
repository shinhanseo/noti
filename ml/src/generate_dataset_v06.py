"""Build v0.6 from v0.5 using policy lessons from real Room review."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from generate_dataset_v05 import (
    assign_cv_folds,
    make_seed_row,
    read_csv,
    write_csv,
)


PROJECT_DIR = Path(__file__).resolve().parents[1]
PUBLIC_DIR = PROJECT_DIR / "data" / "public"
V05_TRAIN = PUBLIC_DIR / "train_notifications_v0.5.csv"
V05_CONTEXT = PUBLIC_DIR / "context_notifications_v0.5.csv"
V05_EVALUATION = PUBLIC_DIR / "public_evaluation_v0.5.csv"
V05_MANIFEST = PUBLIC_DIR / "source_manifest_v0.5.csv"
TRAIN_OUTPUT = PUBLIC_DIR / "train_notifications_v0.6.csv"
CONTEXT_OUTPUT = PUBLIC_DIR / "context_notifications_v0.6.csv"
EVALUATION_OUTPUT = PUBLIC_DIR / "public_evaluation_v0.6.csv"
MANIFEST_OUTPUT = PUBLIC_DIR / "source_manifest_v0.6.csv"


SYSTEM_PROFILES = (
    ("Galaxy", "system", "시스템 작업"),
    ("Galaxy Store", "store", "앱 업데이트"),
    ("Samsung Cloud", "cloud", "데이터 백업"),
    ("디바이스 케어", "devicecare", "휴대전화 검사"),
)

SYSTEM_TEMPLATES = (
    ("{subject} 중…", "{subject}이 백그라운드에서 진행 중입니다."),
    ("{subject}", "완료될 때까지 잠시 기다려 주세요."),
    ("진행 상태", "{subject} 진행률은 76%입니다."),
    ("자동 실행", "설정에 따라 {subject}을 자동으로 실행하고 있습니다."),
    ("처리 중", "{subject}을 처리하고 있습니다."),
    ("상태 표시", "{subject}이 정상적으로 실행 중입니다."),
    ("다운로드 중", "{subject} 파일을 내려받는 중입니다."),
    ("준비 중", "{subject}을 사용할 수 있도록 준비하고 있습니다."),
)

ENGAGEMENT_PROFILES = (
    ("카카오페이", "kakaopay", "출석체크"),
    ("쇼핑", "shopping", "관심 상품"),
    ("배달", "delivery_review", "주문 리뷰"),
    ("리워드", "reward", "걷기 포인트"),
)

ENGAGEMENT_TEMPLATES = (
    ("잊고 계신가요?", "최근 {subject}에 참여하지 않았어요. 지금 확인해 보세요."),
    ("혜택이 기다리고 있어요", "{subject}에 참여하면 포인트를 받을 수 있어요."),
    ("의견을 남겨주세요", "더 나은 서비스를 위해 {subject}에 참여해주세요."),
    ("오늘의 추천", "최근 이용 기록을 바탕으로 {subject} 소식을 준비했어요."),
    ("새로운 소식", "{subject}과 관련된 업데이트가 등록됐어요."),
    ("놓치지 마세요", "{subject} 혜택이 곧 종료됩니다."),
    ("확인해 보세요", "{subject} 화면에서 새로운 내용을 볼 수 있어요."),
    ("포인트 받기", "{subject}을 완료하고 추가 포인트를 받아보세요."),
)

SAFETY_PROFILES = (
    ("안전디딤돌", "safety", "폭염"),
    ("소방청", "fire", "전기화재"),
    ("기상청", "weather", "강풍"),
    ("지자체", "local_safety", "호우"),
)

SAFETY_TEMPLATES = (
    ("안전 안내", "{subject} 예방을 위한 생활 안전 수칙을 안내합니다."),
    ("예방 수칙", "{subject}에 대비해 시설물 상태를 확인하시기 바랍니다."),
    ("생활 정보", "{subject} 발생 가능성이 있어 일반 행동 요령을 알려드립니다."),
    ("주의 안내", "{subject} 관련 최신 안전 정보를 확인할 수 있습니다."),
)

DELIVERY_PROFILES = (
    ("쿠팡", "coupang", "주문 상품"),
    ("오늘의집", "ohouse", "가구 주문"),
    ("CJ대한통운", "cjlogistics", "택배 물품"),
    ("컬리", "kurly", "식품 주문"),
)

DELIVERY_COMPLETE_TEMPLATES = (
    ("배송 완료", "{subject}이 문 앞에 배송 완료되었습니다."),
    ("배달 완료", "요청한 장소에 {subject}을 전달했습니다."),
    ("상품 도착", "{subject}이 배송지에 도착했습니다."),
    ("수령 확인", "{subject} 배송을 완료했습니다. 수령 상태를 확인해주세요."),
)

PICKUP_TEMPLATES = (
    ("회수 예정", "오늘 {subject}을 회수합니다. 지정한 장소에 놓아주세요."),
    ("반품 방문 안내", "기사님이 곧 방문합니다. {subject}을 포장해 준비해주세요."),
    ("수거 준비 요청", "{subject} 수거를 위해 문 앞에 내놓아 주세요."),
    ("교환 상품 회수", "교환할 {subject}을 방문 전에 준비해주세요."),
)

ACTION_PROFILES = (
    ("Slack", "slack", "팀 회의"),
    ("학교 포털", "school", "수강 신청"),
    ("정부24", "gov24", "민원 신청"),
    ("예약 서비스", "reservation", "방문 예약"),
)

ACTION_TEMPLATES = (
    ("참석 여부 확인", "오늘 오후 7시까지 {subject} 참석 여부를 응답해주세요."),
    ("오늘까지 응답 필요", "{subject} 요청에 오늘 안으로 답변해주세요."),
    ("승인 요청", "{subject} 처리를 진행하려면 승인이 필요합니다."),
    ("제출 마감", "{subject} 관련 서류 제출이 오늘 마감됩니다."),
    ("정보 보완 필요", "{subject} 정보가 부족합니다. 내용을 추가해주세요."),
    ("본인 확인 요청", "{subject}을 계속하려면 본인 확인을 완료해주세요."),
    ("예약 유지 확인", "{subject}을 유지하려면 정해진 시간까지 확인해주세요."),
    ("선택 필요", "{subject} 처리 방법을 선택해주세요."),
)

TRANSACTION_PROFILES = (
    ("현대카드", "hyundaicard", "후불교통카드 이용"),
    ("토스", "toss", "계좌 출금"),
    ("카카오뱅크", "kakaobank", "계좌 이체"),
    ("KB Pay", "kbpay", "카드 결제"),
)

TRANSACTION_TEMPLATES = (
    ("이용내역 안내", "{subject} 내역이 새로 등록되었습니다."),
    ("거래 완료", "요청한 {subject} 처리가 완료되었습니다."),
    ("금융 내역", "{subject} 금액과 잔액을 확인할 수 있습니다."),
    ("승인 내역", "{subject}이 정상 승인되었습니다."),
)


def migrate(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    migrated: list[dict[str, object]] = []
    for source in rows:
        row: dict[str, object] = dict(source)
        row["dataset_version"] = "0.6"
        row["cv_fold"] = ""
        migrated.append(row)
    return migrated


def make_v06_rows(fields: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    number = 1
    scenarios = (
        (SYSTEM_PROFILES, SYSTEM_TEMPLATES, "system_progress", "SYSTEM_STATUS", "INFORMATIONAL", False, 0),
        (ENGAGEMENT_PROFILES, ENGAGEMENT_TEMPLATES, "engagement_prompt", "PROMOTION", "PROMOTIONAL", True, 0),
        (SAFETY_PROFILES, SAFETY_TEMPLATES, "general_safety", "SAFETY_INFORMATION", "INFORMATIONAL", False, 0),
        (DELIVERY_PROFILES, DELIVERY_COMPLETE_TEMPLATES, "delivery_complete", "DELIVERY_COMPLETE", "ATTENTION_WORTHY", True, 20),
        (DELIVERY_PROFILES, PICKUP_TEMPLATES, "pickup_preparation", "PICKUP_PREPARATION", "ATTENTION_WORTHY", True, 25),
        (ACTION_PROFILES, ACTION_TEMPLATES, "explicit_action", "USER_ACTION", "ACTION_REQUIRED", False, 30),
        (TRANSACTION_PROFILES, TRANSACTION_TEMPLATES, "transaction_record", "TRANSACTION_STATUS", "ATTENTION_WORTHY", True, 20),
    )
    for profiles, templates, notification_type, event_type, actionability, sensitive, score in scenarios:
        for template_index, (title, body) in enumerate(templates, 1):
            for app_name, slug, subject in profiles:
                row = make_seed_row(
                    row_id=f"V06_REAL_PATTERN_{number:03d}",
                    app_name=app_name,
                    slug=f"real_pattern.{slug}",
                    title=title.format(subject=subject),
                    body=body.format(subject=subject),
                    notification_type=notification_type,
                    event_type=event_type,
                    actionability=actionability,
                    template_group=f"v06_{notification_type}_{template_index:02d}",
                    preference_sensitive=sensitive,
                    rule_score=score,
                    base_fields=fields,
                )
                row.update(
                    {
                        "source": "SYNTHETIC_REAL_PATTERN_REVIEWED",
                        "dataset_version": "0.6",
                        "source_detail": "v0.6_patterns_from_private_room_error_taxonomy",
                        "base_label_status": "POLICY_APPROVED_V06",
                        "reason_code": f"v06_{notification_type}_real_pattern",
                        "cv_fold": "",
                    }
                )
                rows.append(row)
                number += 1
    return rows


def revise_passive_delivery(rows: list[dict[str, object]]) -> int:
    revised = 0
    for row in rows:
        if row.get("notification_type") != "delivery_status":
            continue
        row.update(
            {
                "label": 0,
                "actionability": "INFORMATIONAL",
                "base_label": 0,
                "reason_code": "v06_passive_delivery_progress",
                "base_label_status": "POLICY_REVISED_V06",
            }
        )
        revised += 1
    return revised


def main() -> None:
    fields, train_source = read_csv(V05_TRAIN)
    _, context_source = read_csv(V05_CONTEXT)
    _, evaluation_source = read_csv(V05_EVALUATION)
    manifest_fields, manifest_source = read_csv(V05_MANIFEST)

    train = migrate(train_source)
    revised = revise_passive_delivery(train)
    additions = make_v06_rows(fields)
    train.extend(additions)
    assign_cv_folds(train)
    context = migrate(context_source)
    evaluation = migrate(evaluation_source)

    manifest = [dict(row) for row in manifest_source]
    for row in manifest:
        row["notes"] = str(row.get("notes", ""))
    manifest.append(
        {
            "source_id": "noti_v06_real_pattern_seeds",
            "name": "v0.6 private Room error-taxonomy synthetic seeds",
            "url": "",
            "license": "PROJECT_OWNED",
            "intended_use": "TRAIN",
            "status": "INCLUDED",
            "notes": "160 synthetic rows; contains no copied private notification text",
        }
    )

    write_csv(TRAIN_OUTPUT, fields, train)
    write_csv(CONTEXT_OUTPUT, fields, context)
    write_csv(EVALUATION_OUTPUT, fields, evaluation)
    write_csv(MANIFEST_OUTPUT, manifest_fields, manifest)

    eligible = [row for row in train if row["cv_fold"] != ""]
    print("v0.6 데이터 생성 완료")
    print(f"기존 배송 진행 라벨 교정: {revised}개")
    print(f"신규 실제형 합성 데이터: {len(additions)}개")
    print(f"전체: {len(train)}개, 학습 대상: {len(eligible)}개")
    print(f"학습 분포: {dict(Counter(row['actionability'] for row in eligible))}")


if __name__ == "__main__":
    main()
