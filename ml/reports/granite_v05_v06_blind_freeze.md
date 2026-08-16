# Granite v0.5/v0.6 블라인드 예측 봉인

- 상태: `FROZEN_BEFORE_LABELING`
- 모델: `ibm-granite/granite-embedding-97m-multilingual-r2` + MLP 32-unit
- 전처리: `android-importance-text-v2`
- 홀드아웃: 100개
- 홀드아웃 fingerprint: `0e54e78f419aea87164157a357b8fa6a054ec15e994886aa37a123e9aaa5b37a`
- v0.5 학습 행: 600개
- v0.6 학습 행: 760개
- 비공개 예측 파일 SHA-256: `948c89ce563e0b0662880252ae659fed7516be5cdc23caf6e8c185d983c27019`

사람 라벨을 보기 전에 두 모델의 확률과 앱 최종 등급을 저장했다.
라벨 입력 뒤에는 이 파일을 다시 생성하지 않고 해시를 검증해 평가한다.
