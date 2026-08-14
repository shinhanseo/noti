package com.hanseo.noti.domain.importance

import java.text.Normalizer
import java.util.Locale

object ImportanceTextPreprocessor {

    private const val SAMSUNG_MESSAGES_PACKAGE =
        "com.samsung.android.messaging"

    private val unicodeFormatCharacters =
        Regex("\\p{Cf}+")

    private val multipleWhitespace =
        Regex("\\s+")

    private val samsungMmsEnvelope = Regex(
        pattern = """
            ^\s*
            <\s*제목\s*:\s*(.*?)\s*>
            \s*
            메시지\s*크기\s*:\s*
            \d+(?:[.,]\d+)?\s*(?:kb|mb|gb)
            \s*
            만료\s*:\s*
            .*$
        """.trimIndent().replace("\n", ""),
        options = setOf(
            RegexOption.IGNORE_CASE,
            RegexOption.DOT_MATCHES_ALL
        )
    )

    fun normalize(input: ImportanceInput): String {
        val cleanTitle = clean(input.title.orEmpty())
        val cleanBody = clean(input.body.orEmpty())

        val semanticBody = extractSemanticBody(
            packageName = input.packageName,
            body = cleanBody
        )

        return listOf(
            cleanTitle,
            semanticBody
        )
            .filter { it.isNotBlank() }
            .joinToString(" ")
            .lowercase(Locale.ROOT)
            .replace(multipleWhitespace, " ")
            .trim()
    }

    fun normalizeKeyword(keyword: String): String {
        return clean(keyword)
            .lowercase(Locale.ROOT)
    }

    private fun extractSemanticBody(
        packageName: String,
        body: String
    ): String {
        if (packageName != SAMSUNG_MESSAGES_PACKAGE) {
            return body
        }

        val match = samsungMmsEnvelope.matchEntire(body)
            ?: return body

        return match.groupValues[1].trim()
    }

    private fun clean(value: String): String {
        return Normalizer
            .normalize(value, Normalizer.Form.NFKC)
            .replace(unicodeFormatCharacters, "")
            .replace(multipleWhitespace, " ")
            .trim()
    }
}