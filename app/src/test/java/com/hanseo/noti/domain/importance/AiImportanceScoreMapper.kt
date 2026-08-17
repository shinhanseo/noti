package com.hanseo.noti.domain.importance

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class AiImportanceScoreMapperTest {

    private val mapper = AiImportanceScoreMapper()

    @Test
    fun zeroProbability_returnsMinusFifteen() {
        assertEquals(-15, mapper.map(0.00f))
    }

    @Test
    fun twentyPercentProbability_returnsMinusTen() {
        assertEquals(-10, mapper.map(0.20f))
    }

    @Test
    fun thirtyFivePercentProbability_returnsZero() {
        assertEquals(0, mapper.map(0.35f))
    }

    @Test
    fun sixtyFivePercentProbability_returnsTen() {
        assertEquals(10, mapper.map(0.65f))
    }

    @Test
    fun eightyPercentProbability_returnsFifteen() {
        assertEquals(15, mapper.map(0.80f))
    }

    @Test
    fun oneHundredPercentProbability_returnsFifteen() {
        assertEquals(15, mapper.map(1.00f))
    }

    @Test
    fun negativeProbability_throwsException() {
        assertThrows(IllegalArgumentException::class.java) {
            mapper.map(-0.01f)
        }
    }

    @Test
    fun probabilityGreaterThanOne_throwsException() {
        assertThrows(IllegalArgumentException::class.java) {
            mapper.map(1.01f)
        }
    }
}