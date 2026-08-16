"""Contract tests for the Python mirror of Android text preprocessing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from notification_text_preprocessor import (  # noqa: E402
    normalize_keyword,
    normalize_notification_text,
)


class NotificationTextPreprocessorTest(unittest.TestCase):
    def test_samsung_mms_keeps_subject_and_removes_metadata(self) -> None:
        result = normalize_notification_text(
            "com.samsung.android.messaging",
            "컬리",
            "<제목: 컬리 쿠폰 당첨 안내> 메시지 크기: 3KB "
            "만료: 8월 19일, 오전 11:44",
        )
        self.assertEqual(result, "컬리 컬리 쿠폰 당첨 안내")
        self.assertNotIn("메시지 크기", result)
        self.assertNotIn("만료", result)

    def test_samsung_delivery_mms_keeps_delivery_company(self) -> None:
        result = normalize_notification_text(
            "com.samsung.android.messaging",
            "010-1234-5678",
            "<제목: [로젠택배]> 메시지 크기: 183KB "
            "만료: 8월 15일, 오전 9:09",
        )
        self.assertIn("로젠택배", result)
        self.assertNotIn("183kb", result)
        self.assertNotIn("8월 15일", result)

    def test_non_samsung_expiration_is_preserved(self) -> None:
        result = normalize_notification_text(
            "com.example.card",
            "카드 안내",
            "카드 유효기간이 내일 만료됩니다",
        )
        self.assertIn("만료됩니다", result)

    def test_unicode_format_characters_are_removed(self) -> None:
        result = normalize_notification_text(
            "com.samsung.android.messaging",
            "컬리",
            "<제목: 컬리\u200e 쿠폰\u200e 당첨 안내>",
        )
        self.assertIn("쿠폰 당첨", result)
        self.assertNotIn("\u200e", result)

    def test_keyword_uses_same_unicode_contract(self) -> None:
        self.assertEqual(normalize_keyword("  쿠폰\u200e  당첨  "), "쿠폰 당첨")


if __name__ == "__main__":
    unittest.main()
