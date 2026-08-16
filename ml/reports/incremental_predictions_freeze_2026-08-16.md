# 증분 Room 모델 예측 봉인

- 라벨 입력 전 행 수: 45개
- 검수 파일 SHA-256: `ad043e0c41e26a607bfc06e587e26b556ae82f34a9541c4e7a797cd4131a1155`
- 예측 파일 SHA-256: `c3dcf0b5630cbcef0144de97c345ef116368f6f86e81ca9e7ec9430b3d865a4f`

```json
{
  "granite_97m_r2": {
    "model_id": "ibm-granite/granite-embedding-97m-multilingual-r2",
    "head_sha256": "7f72c1f6add2b4f2bf22b394ffca0082b53d1f487a54e26d35db82fdb6d42520",
    "embedding_dimension": 384
  },
  "embeddinggemma_300m": {
    "model_id": "google/embeddinggemma-300m",
    "head_sha256": "c787fb5151f516d36880a82dc7e952085db15f4fcd82577fb1a25b4655ac8930",
    "embedding_dimension": 768
  },
  "koelectra_small_v3": {
    "model_id": "monologg/koelectra-small-v3-discriminator",
    "head_sha256": "b0e8c177efcd7da8726d3fe9ba01da1dde3c5db25875c49a88c35cfab1d837eb",
    "embedding_dimension": 256
  }
}
```

세 모델의 예측 확률과 라벨을 사람의 정답 입력 전에 저장했다.
평가 시 이 파일은 다시 생성하지 않고 봉인된 값을 그대로 사용한다.
