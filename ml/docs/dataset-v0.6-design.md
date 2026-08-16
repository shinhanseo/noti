# noti. 알림 데이터셋 v0.6 설계

## 목적

v0.5는 합성 교차검증 성능은 높았지만 실제 Room Active Learning 표본에서 일반
알림을 중요하다고 과도하게 판정했다. v0.6은 모델을 바꾸지 않고 실제 오류 유형에
맞춰 공통 Actionability 정책과 학습 문장 분포를 교정한다.

개인 Room 원문 40개는 공개 학습 CSV에 복사하지 않았다. 패키지·사람 이름·상품명
등을 제거하고 관찰한 오류 유형만 프로젝트 소유 합성 문장으로 다시 작성했다.

## 정책 교정

v0.4~v0.5의 배송 진행 52개는 모두 `ATTENTION_WORTHY`였다. 실제 검수 결과에
따라 출고·이동·도착 예정처럼 행동이 필요 없는 진행 정보는 `INFORMATIONAL`로
교정했다.

- 배송 출발·이동·도착 예정: `INFORMATIONAL`
- 배송 완료·상품 도착: `ATTENTION_WORTHY`
- 반품 회수·수거 준비: `ATTENTION_WORTHY`

## 신규 실제형 합성 문장 160개

| 문장군 | 수 | Actionability |
| --- | ---: | --- |
| 시스템 처리·백업·검사 상태 | 32 | `INFORMATIONAL` |
| 출석·리뷰·혜택 참여 유도 | 32 | `PROMOTIONAL` |
| 일반 안전·예방 정보 | 16 | `INFORMATIONAL` |
| 배송 완료·상품 도착 | 16 | `ATTENTION_WORTHY` |
| 반품 회수·수거 준비 | 16 | `ATTENTION_WORTHY` |
| 응답·승인·제출·본인확인 요청 | 32 | `ACTION_REQUIRED` |
| 결제·출금·이용 내역 | 16 | `ATTENTION_WORTHY` |

## 생성 결과

- 전체 학습·대조 데이터: 840개
- 모델 학습 대상: 760개
- 기존 배송 진행 라벨 교정: 52개
- 신규 실제형 합성 데이터: 160개
- 개인화 context: 80개, 학습 제외 유지

| Actionability | 학습 대상 |
| --- | ---: |
| `ACTION_REQUIRED` | 210 |
| `ATTENTION_WORTHY` | 138 |
| `INFORMATIONAL` | 182 |
| `PROMOTIONAL` | 230 |

## Granite 개발 세트 진단

같은 Granite Embedding 97M R2와 같은 MLP head에서 학습 데이터만 비교했다.

| 데이터 | 합성 CV 정확도 | 실제 40개 일치율 | 일반→중요 오판 | 중요 Recall |
| --- | ---: | ---: | ---: | ---: |
| v0.5 | 94.3% | 72.5% | 9 | 60% |
| v0.6 | 89.3% | 82.5% | 7 | 100% |

합성 CV 하락은 문장군이 어려워지고 분포가 실제형으로 바뀐 결과다. 실제 40개는
v0.6 설계에 사용했기 때문에 독립 테스트가 아니라 개발 세트다. 다음 시점에 수집한
미사용 실제 라벨로 성능을 다시 확인하기 전에는 v0.6 성능을 확정하지 않는다.

## 블라인드 재검증 결과

기존 개발 40개 및 동일 문장군을 제외한 실제 Room 100개를 모델 예측 봉인 후
검수했다. v0.5는 Accuracy 90.0%, 중요 Recall 75.0%, 중요 F1 0.545였고,
v0.6은 Accuracy 87.0%, 중요 Recall 50.0%, 중요 F1 0.381이었다.

정확도 차이의 paired bootstrap 95% CI는 -8.0%p~+2.0%p이고 McNemar exact
p-value는 0.4531이다. v0.5의 통계적 우월성을 확정할 수는 없지만 v0.6의 개선도
재현되지 않았으므로 v0.6을 배포 후보로 채택하지 않는다.

```bash
python src/generate_dataset_v06.py
python src/validate_dataset_v06.py
python src/compare_granite_v05_v06_active_learning.py
```
