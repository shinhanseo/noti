"""Python mirror of Android's importance text preprocessing contract."""

from __future__ import annotations

import re
import unicodedata


PREPROCESSING_VERSION = "android-importance-text-v2"
SAMSUNG_MESSAGES_PACKAGE = "com.samsung.android.messaging"

_MULTIPLE_WHITESPACE = re.compile(r"\s+")
_SAMSUNG_MMS_ENVELOPE = re.compile(
    r"""
    ^\s*
    <\s*제목\s*:\s*(.*?)\s*>
    \s*
    메시지\s*크기\s*:\s*
    \d+(?:[.,]\d+)?\s*(?:kb|mb|gb)
    \s*
    만료\s*:\s*
    .*$
    """,
    flags=re.IGNORECASE | re.DOTALL | re.VERBOSE,
)


def clean_text(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKC", value or "")
    without_format_characters = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Cf"
    )
    return _MULTIPLE_WHITESPACE.sub(" ", without_format_characters).strip()


def extract_semantic_body(package_name: str, body: str) -> str:
    if package_name != SAMSUNG_MESSAGES_PACKAGE:
        return body
    match = _SAMSUNG_MMS_ENVELOPE.fullmatch(body)
    if match is None:
        return body
    return match.group(1).strip()


def normalize_notification_text(
    package_name: str,
    title: str | None,
    body: str | None,
) -> str:
    clean_title = clean_text(title)
    clean_body = clean_text(body)
    semantic_body = extract_semantic_body(package_name, clean_body)
    combined = " ".join(
        value for value in (clean_title, semantic_body) if value
    )
    return _MULTIPLE_WHITESPACE.sub(" ", combined.lower()).strip()


def normalize_keyword(keyword: str) -> str:
    return clean_text(keyword).lower()
