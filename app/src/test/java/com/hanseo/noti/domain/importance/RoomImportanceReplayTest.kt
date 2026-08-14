package com.hanseo.noti.domain.importance

import java.nio.charset.StandardCharsets
import java.nio.file.Files
import java.nio.file.Path
import java.util.Base64
import org.junit.Assert.assertTrue
import org.junit.Assume.assumeTrue
import org.junit.Test

class RoomImportanceReplayTest {

    @Test
    fun replayPrivateRoomNotificationsWithoutUpdatingDatabase() {
        val inputPath = System.getenv(INPUT_ENV)
        val outputPath = System.getenv(OUTPUT_ENV)

        assumeTrue(
            "${INPUT_ENV}와 ${OUTPUT_ENV}가 있을 때만 Room 재평가를 실행합니다.",
            !inputPath.isNullOrBlank() && !outputPath.isNullOrBlank()
        )

        val classifier = ImportanceClassifier()
        val outputLines = mutableListOf(
            "private_id\told_score\told_level\tnew_score\tnew_level\treason_ids"
        )

        Files.readAllLines(Path.of(inputPath)).forEachIndexed { index, line ->
            if (index == 0 || line.isBlank()) return@forEachIndexed

            val columns = line.split('\t')
            require(columns.size == 8) {
                "Room replay 입력 열이 8개가 아닙니다: ${columns.size}"
            }

            val input = ImportanceInput(
                packageName = decode(columns[1]),
                title = decodeNullable(columns[2]),
                body = decodeNullable(columns[3]),
                category = decodeNullable(columns[4]),
                isOngoing = columns[5] == "1"
            )
            val result = classifier.classify(
                input = input,
                settings = ImportanceSettings(),
                evaluatedAtMillis = 0L
            )
            val reasonIds = result.reasons
                .mapNotNull { it.ruleId }
                .joinToString(",")

            outputLines += listOf(
                columns[0],
                columns[6],
                columns[7],
                result.score.toString(),
                result.level.name,
                reasonIds
            ).joinToString("\t")
        }

        assertTrue("재평가된 알림이 없습니다.", outputLines.size > 1)
        Files.write(
            Path.of(outputPath),
            outputLines,
            StandardCharsets.UTF_8
        )
    }

    private fun decode(value: String): String =
        String(Base64.getDecoder().decode(value), StandardCharsets.UTF_8)

    private fun decodeNullable(value: String): String? =
        if (value == NULL_MARKER) null else decode(value)

    private companion object {
        const val INPUT_ENV = "NOTI_ROOM_REPLAY_INPUT"
        const val OUTPUT_ENV = "NOTI_ROOM_REPLAY_OUTPUT"
        const val NULL_MARKER = "-"
    }
}
