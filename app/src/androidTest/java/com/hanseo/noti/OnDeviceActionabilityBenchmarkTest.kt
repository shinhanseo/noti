package com.hanseo.noti

import android.os.Debug
import android.os.SystemClock
import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.hanseo.noti.ai.OnDeviceActionabilityClassifier
import kotlin.math.ceil
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class OnDeviceActionabilityBenchmarkTest {

    @Test
    fun benchmarkKoEnE5TinyOnCurrentDevice() {
        val context = InstrumentationRegistry.getInstrumentation().targetContext
        forceGc()
        val before = memorySnapshot()

        val initializationStarted = SystemClock.elapsedRealtimeNanos()
        val classifier = OnDeviceActionabilityClassifier.fromAssets(context)
        val initializationMs = elapsedMs(initializationStarted)
        forceGc()
        val afterInitialization = memorySnapshot()

        classifier.use { value ->
            val firstStarted = SystemClock.elapsedRealtimeNanos()
            val firstResult = value.classify(TEXTS.first())
            val firstInferenceMs = elapsedMs(firstStarted)

            repeat(WARMUP_RUNS) { index ->
                value.classify(TEXTS[index % TEXTS.size])
            }

            val durations = FloatArray(MEASURED_RUNS)
            repeat(MEASURED_RUNS) { index ->
                val started = SystemClock.elapsedRealtimeNanos()
                value.classify(TEXTS[index % TEXTS.size])
                durations[index] = elapsedMs(started)
            }
            val afterInference = memorySnapshot()
            val summary = summarize(durations)

            assertEquals(3, firstResult.probabilities.size)
            Log.i(
                TAG,
                "result={" +
                    "\"device\":\"${android.os.Build.MODEL}\"," +
                    "\"sdk\":${android.os.Build.VERSION.SDK_INT}," +
                    "\"runs\":$MEASURED_RUNS," +
                    "\"threads\":4," +
                    "\"initialization_ms\":${format(initializationMs)}," +
                    "\"first_inference_ms\":${format(firstInferenceMs)}," +
                    "\"warm_mean_ms\":${format(summary.mean)}," +
                    "\"warm_median_ms\":${format(summary.median)}," +
                    "\"warm_p95_ms\":${format(summary.p95)}," +
                    "\"warm_min_ms\":${format(summary.min)}," +
                    "\"warm_max_ms\":${format(summary.max)}," +
                    "\"pss_before_kb\":${before.totalPssKb}," +
                    "\"pss_after_init_kb\":${afterInitialization.totalPssKb}," +
                    "\"pss_after_inference_kb\":${afterInference.totalPssKb}," +
                    "\"pss_init_delta_kb\":${afterInitialization.totalPssKb - before.totalPssKb}," +
                    "\"native_pss_after_inference_kb\":${afterInference.nativePssKb}," +
                    "\"dalvik_pss_after_inference_kb\":${afterInference.dalvikPssKb}" +
                    "}"
            )
        }
    }

    private fun memorySnapshot(): MemorySnapshot {
        val memory = Debug.MemoryInfo()
        Debug.getMemoryInfo(memory)
        return MemorySnapshot(
            totalPssKb = memory.totalPss,
            nativePssKb = memory.nativePss,
            dalvikPssKb = memory.dalvikPss,
        )
    }

    private fun forceGc() {
        repeat(2) {
            Runtime.getRuntime().gc()
            System.runFinalization()
        }
    }

    private fun summarize(values: FloatArray): TimingSummary {
        val sorted = values.sorted()
        return TimingSummary(
            mean = values.average().toFloat(),
            median = sorted[sorted.size / 2],
            p95 = sorted[ceil(sorted.size * 0.95).toInt() - 1],
            min = sorted.first(),
            max = sorted.last(),
        )
    }

    private fun elapsedMs(startedNanos: Long): Float {
        return (SystemClock.elapsedRealtimeNanos() - startedNanos) / 1_000_000f
    }

    private fun format(value: Float): String = "%.3f".format(java.util.Locale.US, value)

    private data class MemorySnapshot(
        val totalPssKb: Int,
        val nativePssKb: Int,
        val dalvikPssKb: Int,
    )

    private data class TimingSummary(
        val mean: Float,
        val median: Float,
        val p95: Float,
        val min: Float,
        val max: Float,
    )

    private companion object {
        const val TAG = "NotiAiBenchmark"
        const val WARMUP_RUNS = 5
        const val MEASURED_RUNS = 50

        val TEXTS = listOf(
            "배송 출발 주문하신 상품이 오늘 오후 도착할 예정입니다.",
            "결제가 실패했습니다. 계좌 잔액을 확인해주세요.",
            "오늘만 사용할 수 있는 할인 쿠폰이 도착했습니다.",
            "회의 자료를 오늘 오후 3시까지 회신해주세요.",
            "남긴 댓글에 새로운 답글이 등록되었습니다.",
        )
    }
}
