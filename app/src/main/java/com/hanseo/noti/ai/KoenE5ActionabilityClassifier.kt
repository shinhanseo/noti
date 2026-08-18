package com.hanseo.noti.ai

import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession
import java.io.Closeable

class KoenE5ActionabilityClassifier(
    modelPath: String,  // ONNX 실제 경로
    numberOfThreads: Int = DEFAULT_THREAD_COUNT // onnx 모델이 CPU 연산 시 사용할 스레드 수
) : Closeable {

    // ONNX 전체 실행 환경
    private val environment: OrtEnvironment = OrtEnvironment.getEnvironment()

    // ONNX 모델 실행 방법 설정
    private val sessionOptions: OrtSession.SessionOptions = //
        OrtSession.SessionOptions().apply {
            setIntraOpNumThreads(numberOfThreads)
        }

    //ONNX 파일을 읽어 메모리에 올림
    private val session: OrtSession =
        environment.createSession(
            modelPath,
            sessionOptions
        )

    override fun close() {
        session.close()
        sessionOptions.close()
    }

    private companion object {
        const val DEFAULT_THREAD_COUNT = 4
    }
}