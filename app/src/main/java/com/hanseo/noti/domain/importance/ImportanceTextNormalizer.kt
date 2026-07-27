package com.hanseo.noti.domain.importance

import java.util.Locale

object ImportanceTextNormalizer {
    private val multipleWhitespace = Regex("\\s+")

    fun normalize(title: String?, body: String?): String {
        val combinedText = "${title.orEmpty()} ${body.orEmpty()}"

        return combinedText
            .lowercase(Locale.ROOT)
            .trim()
            .replace(multipleWhitespace, " ")
    }

    fun normalizeKeyword(keyword: String): String {
        return keyword
            .lowercase(Locale.ROOT)
            .trim()
            .replace(multipleWhitespace, " ")
    }
}