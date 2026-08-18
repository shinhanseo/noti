#include <jni.h>

#include <memory>
#include <string>
#include <vector>

#include "sentencepiece_processor.h"

namespace {

using sentencepiece::SentencePieceProcessor;

void throw_illegal_state(JNIEnv* env, const std::string& message) {
  jclass exception_class = env->FindClass("java/lang/IllegalStateException");
  if (exception_class != nullptr) {
    env->ThrowNew(exception_class, message.c_str());
  }
}

std::string to_utf8(JNIEnv* env, jbyteArray bytes) {
  const jsize length = env->GetArrayLength(bytes);
  std::string value(static_cast<size_t>(length), '\0');
  if (length > 0) {
    env->GetByteArrayRegion(
        bytes, 0, length, reinterpret_cast<jbyte*>(value.data()));
  }
  return value;
}

}  // namespace

extern "C" JNIEXPORT jlong JNICALL
Java_com_hanseo_noti_ai_tokenizer_NativeSentencePieceTokenizer_nativeCreate(
    JNIEnv* env, jobject, jstring model_path) {
  const char* path = env->GetStringUTFChars(model_path, nullptr);
  if (path == nullptr) {
    return 0;
  }
  auto processor = std::make_unique<SentencePieceProcessor>();
  const auto status = processor->Load(path);
  env->ReleaseStringUTFChars(model_path, path);
  if (!status.ok()) {
    throw_illegal_state(env, status.ToString());
    return 0;
  }
  return reinterpret_cast<jlong>(processor.release());
}

extern "C" JNIEXPORT jintArray JNICALL
Java_com_hanseo_noti_ai_tokenizer_NativeSentencePieceTokenizer_nativeEncode(
    JNIEnv* env, jobject, jlong handle, jbyteArray text_utf8) {
  auto* processor = reinterpret_cast<SentencePieceProcessor*>(handle);
  if (processor == nullptr) {
    throw_illegal_state(env, "SentencePiece tokenizer is closed");
    return nullptr;
  }
  std::vector<int> ids;
  const auto status = processor->Encode(to_utf8(env, text_utf8), &ids);
  if (!status.ok()) {
    throw_illegal_state(env, status.ToString());
    return nullptr;
  }
  jintArray result = env->NewIntArray(static_cast<jsize>(ids.size()));
  if (result != nullptr && !ids.empty()) {
    env->SetIntArrayRegion(
        result,
        0,
        static_cast<jsize>(ids.size()),
        reinterpret_cast<const jint*>(ids.data()));
  }
  return result;
}

extern "C" JNIEXPORT void JNICALL
Java_com_hanseo_noti_ai_tokenizer_NativeSentencePieceTokenizer_nativeDestroy(
    JNIEnv*, jobject, jlong handle) {
  delete reinterpret_cast<SentencePieceProcessor*>(handle);
}
