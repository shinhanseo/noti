cmake_minimum_required(VERSION 3.22.1)
project(noti_sentencepiece LANGUAGES CXX)

include(FetchContent)

set(SPM_ENABLE_SHARED OFF CACHE BOOL "" FORCE)
set(SPM_ENABLE_TCMALLOC OFF CACHE BOOL "" FORCE)
set(SPM_BUILD_TEST OFF CACHE BOOL "" FORCE)
set(SPM_BUILD_TCMALLOC OFF CACHE BOOL "" FORCE)

FetchContent_Declare(
    sentencepiece
    URL https://github.com/google/sentencepiece/archive/refs/tags/v0.2.1.tar.gz
    URL_HASH SHA256=c1a59e9259c9653ad0ade653dadff074cd31f0a6ff2a11316f67bee4189a8f1b
)
FetchContent_GetProperties(sentencepiece)
if (NOT sentencepiece_POPULATED)
    FetchContent_Populate(sentencepiece)
    add_subdirectory(
        "${sentencepiece_SOURCE_DIR}"
        "${sentencepiece_BINARY_DIR}"
        EXCLUDE_FROM_ALL
    )
endif()

# Android Gradle Plugin discovers SentencePiece's CLI targets as native outputs.
# They are not packaged, but must still link successfully during the native build.
foreach(spm_cli spm_encode spm_decode spm_normalize spm_train spm_export_vocab)
    if (TARGET ${spm_cli})
        target_link_libraries(${spm_cli} log)
    endif()
endforeach()

add_library(noti_sentencepiece SHARED sentencepiece_jni.cpp)

target_include_directories(
    noti_sentencepiece
    PRIVATE
    "${sentencepiece_SOURCE_DIR}/src"
)

target_link_libraries(
    noti_sentencepiece
    PRIVATE
    sentencepiece-static
    log
)

target_link_options(
    noti_sentencepiece
    PRIVATE
    "-Wl,-z,max-page-size=16384"
    "-Wl,-z,common-page-size=16384"
)
