# 01.04 개념 정리 — 재고 · 잔고 동시 차감 (docs)

> 이 문서들만 읽고 이해하면 "원리 → 엔진 내부 → 운영 · 장애 → 설계 선택" 꼬리질문에 답할 수 있게 쓴 개념 정리다. 근거는 PostgreSQL 16 공식 문서 · MySQL 8.0 · Jakarta Persistence 스펙과 이 레슨의 테스트 · psql 실측이다. 근거를 못 찾은 주장은 빼거나 `(해석)` 으로 표시했다.

> **읽는 법**: 개념 글(마지막 면접 사다리 앞까지)은 블로그처럼 위에서 아래로 읽는 연재다 — 장면 하나 → 개념을 하나씩(그림과 함께) → PostgreSQL 에서는 → 한눈에 정리 → 스스로 확인. 면접 대비는 마지막 사다리 글에서 한다.

> **필수 / 심화**: 필수 글(02 · 03 · 04)만 ② 원리에서 읽는다 — ① 에서 감으로 예측한 뒤, 틀린 문항이 왜 틀렸는지 찾으며. 나머지는 심화(꼬리질문 · 깊은 지식 대비)라 레슨을 마친 뒤 · 면접 전에 읽는다. 필수 글 분량은 공백 줄 · 이미지 줄을 뺀 약 29,036자 ≈ 73분(400자/분 추정)이라 ② 시간을 75분으로 잡았다. MySQL 비교 절은 필수 글 안에서도 "(심화)" 다 — 회사 서비스가 PostgreSQL 이라 MySQL 은 비교 참고다.

## 읽는 순서

| # | 문서 | 한 줄 | 구분 |
|---|---|---|---|
| 01 | [읽고 계산해서 쓰기 — 갱신 손실 · 초과 판매](01-lost-update-and-the-gap.md) | 검사와 차감 사이의 틈 · 음수가 안 되는 버그 · 세 갈래 해법 | 심화 — Q01 에서 막힐 때 · 문제의 큰 그림 |
| 02 | [원자 조건부 UPDATE](02-atomic-conditional-update.md) | 한 문장 · 영향 행 수 · 행 락 대기 후 재평가 · RETURNING · RR 의 40001 | **필수** — Q02 · Q03 · Q08 · 구현 ① |
| 03 | [비관 락 `FOR UPDATE`](03-pessimistic-lock.md) | 읽는 순간 잠금 · 락 보유 시간 · NOWAIT · lock_timeout · 데드락과 정렬 | **필수** — Q06 · Q07 · 구현 ② |
| 04 | [낙관 락 version](04-optimistic-lock.md) | 0 행 = 충돌 · 재시도 상한(재고 N → 최대 N 번) · RR 의 40001 · JPA `@Version` | **필수** — Q04 · Q05 · 구현 ③ |
| 05 | [세 전략 비교와 선택 · 핫 로우](05-choosing-and-hot-row.md) | 관찰 표 읽는 법 · 경합에 따른 선택 · 버킷 분할 · 큐 · 예약 | 심화 — 관찰 테스트 표 해석 · 선택 기준 (③ 관찰 뒤 · 면접 전) |
| 06 | [MySQL InnoDB 라면](06-mysql-innodb.md) | UPDATE 는 최신 값을 읽는다 · 일관된 읽기와의 차이 · 인덱스와 락 범위 | 심화 — MySQL InnoDB 비교 (꼬리질문 대비) |
| 07 | [면접 사다리](07-interview-ladder.md) | 30초 · 2분 · 갈래별 꼬리질문 · 장애 시나리오 | 심화 — ④ 말하기 연습 · 면접 전 |

권장: ① 에서 감으로 예측해 돌린 뒤, ② 에서는 필수 02 · 03 · 04 만 읽는다 — 02 로 Q02 · Q03 · Q08 과 구현 ① 을, 03 으로 Q06 · Q07 과 구현 ② 를, 04 로 Q04 · Q05 와 구현 ③ 을 되짚는다. Q01 에서 막히면 01 을 펼친다. 관찰 테스트 표를 NOTES 에 옮긴 뒤 05 로 해석해도 좋지만 심화다.

## 예측 답 접힘 규칙

- 문항(Qnn) 시나리오의 **결과 값**(숫자 · true/false · 성공/에러 코드)은 `<details>` 안에만 있다. 예측 전에 읽어도 답이 새지 않게 썼다.
- 일반 원리(예: "READ COMMITTED 에서 기다린 쪽은 최신 값에 WHERE 를 다시 평가한다", "REPEATABLE READ 에서 스냅샷 이후 바뀐 행을 고치면 40001")는 본문에 있다 — 원리 자체가 ② 의 공부 대상이다. 그래도 문항 값을 먼저 직접 적는다.
- 관찰 테스트 해석 과제(README ③ a~d)의 답 후보는 05 의 접힌 칸에 있다. 내 해석을 NOTES 에 쓴 뒤 연다.
- 표기: `(실측: Qnn)` = 이 레슨 테스트(정답 상태), `(실측: 관찰 테스트 2026-10-13)` = 정답 구현으로 `StockObservationTest` 를 돌린 값(실행마다 다름), `(실측: psql 2026-10-13)` = PostgreSQL 16 컨테이너에서 직접, `(해석)` = 근거 문장에서 이은 판단 · 일반 설계.

## 그림

| 그림 | 어디서 | 위치 |
|---|---|---|
| 재고 동시 차감 — 틈과 세 전략 (기존) | 01 | [../diagrams/stock-concurrency.svg](../diagrams/stock-concurrency.svg) |
| 구매자 B 의 길 — 세 전략 타임라인 | 03 · 05 | [diagrams/three-timelines.svg](diagrams/three-timelines.svg) |

다시 그리기(만든 사람용 · 레슨 폴더에서): `python3 -I docs/diagrams/draw.py`

## 이 레슨과 연결

- 손 작업: [예측](../src/test/java/deepdive/c01/l04/StockPredictTest.java) · [구현](../src/main/java/deepdive/c01/l04/) · [관찰 테스트](../src/test/java/deepdive/c01/l04/StockObservationTest.java) · [관찰](../observe/SCRIPT.md) · [내 말로](../NOTES.md)
- 앞선 레슨: [01.01 docs](../../l01-isolation-mvcc/docs/README.md) (격리수준 · MVCC · 재평가 · 40001) · 이어지는 레슨: [01.02 docs](../../l02-row-locks-deadlock/docs/README.md) (행 락 모드 · 데드락)
