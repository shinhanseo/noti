# noti. ML Lab

`noti.`의 알림 중요도 분류 모델을 학습하고 평가하는 Python 실험 공간이다.

Android 앱 코드는 루트의 `app/`에서 관리하고, 머신러닝 코드는 이 `ml/` 폴더에서 관리한다.

## 진행 순서

1. 합성 알림 CSV 검사
2. 제목과 본문을 모델 입력으로 결합
3. 학습 데이터와 테스트 데이터 분리
4. 문자 n-gram TF-IDF 생성
5. Logistic Regression 학습
6. 평가 결과와 오분류 분석
7. Android 적용용 모델 변환 검토

## 예정 구조

```text
ml/
├── data/
│   ├── public/
│   └── private/
├── src/
├── models/
├── reports/
├── requirements.txt
└── README.md
```

실제 알림 원문과 개인 데이터는 `data/private/`에만 보관하며 Git에 커밋하지 않는다.
