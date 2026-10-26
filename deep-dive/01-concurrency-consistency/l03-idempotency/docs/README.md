# 01.03 개념 정리 — 멱등성 (docs)

> 이 문서들만 읽고 이해하면 "원리 → 엔진 내부 → 운영 · 장애 → 설계 선택" 꼬리질문에 답할 수 있게 쓴 개념 정리다. 근거는 PostgreSQL 16 공식 문서 · MySQL 8.0 · Spring 공식 문서 · RFC 9110 · Stripe API 문서와 이 레슨의 테스트 · psql 실측이다. 근거를 못 찾은 주장은 빼거나 `(해석)` 으로 표시했다.

> **읽는 법**: 개념 글(마지막 면접 사다리 앞까지)은 블로그처럼 위에서 아래로 읽는 연재다 — 장면 하나 → 개념을 하나씩(그림과 함께) → PostgreSQL 에서는 → 한눈에 정리 → 스스로 확인. 면접 대비는 마지막 사다리 글에서 한다.

> **필수 / 심화**: 필수 글(03 · 04 · 06)만 ② 원리에서 읽는다 — ① 에서 감으로 예측한 뒤, 틀린 문항이 왜 틀렸는지 찾으며. 나머지는 심화(꼬리질문 · 깊은 지식 대비)라 레슨을 마친 뒤 · 면접 전에 읽는다. 필수 글 분량은 공백 줄 · 이미지 줄을 뺀 약 33,095자 ≈ 83분(400자/분 추정)이라 ② 시간을 85분으로 잡았다. MySQL 비교 절은 필수 글 안에서도 "(심화)" 다 — 회사 서비스가 PostgreSQL 이라 MySQL 은 비교 참고다.

## 읽는 순서

| # | 문서 | 한 줄 | 구분 |
|---|---|---|---|
| 01 | [멱등성과 재시도](01-idempotency-and-retry.md) | 타임아웃 = "모름" · RFC 9110 멱등 정의 · Idempotency-Key 관례(IETF 초안의 상태) | 심화 — 타임아웃 = "모름" · 멱등의 정의 (배경) |
| 02 | [확인하고 넣기의 경쟁](02-check-then-act.md) | SELECT → INSERT 의 틈 · JVM 락이 부족한 이유 · 유니크 제약이 주는 것 | 심화 — Q01 · Q02 에서 막힐 때 (확인하고 넣기의 틈) |
| 03 | [유니크 제약과 동시 INSERT](03-unique-constraint-concurrent-insert.md) | 미커밋 키 앞의 대기 · 23505 · 롤백 · `transactionid` 락 | **필수** — Q03 ~ Q05 되짚기 |
| 04 | [ON CONFLICT](04-on-conflict.md) | DO NOTHING / DO UPDATE · 영향 행 수 · RETURNING · 격리수준 · 함정 | **필수** — Q06 ~ Q08 · 구현 |
| 05 | [실패한 트랜잭션](05-failed-transaction.md) | 23505 뒤의 중단 상태 · SAVEPOINT · ON CONFLICT 로 피하기 | 심화 — Q09 · Q10 에서 막힐 때 (실패한 트랜잭션) |
| 06 | [멱등 키 설계](06-idempotency-key-design.md) | 선점 · 상태 · 재생 · 지문 · 처리 중 대기 vs 409 · 만료 · 외부 부수효과 · 2-트랜잭션 설계 | **필수** — 구현 (멱등 키 선점 · 재생 · 충돌) |
| 07 | [앱 · 프레임워크 · MySQL](07-app-framework-mysql.md) | Spring 의 23505 번역 · JPA `save` 의 확인된 범위 · `INSERT IGNORE` · `ON DUPLICATE KEY UPDATE` · 락 | 심화 — 앱 · 프레임워크 · MySQL 비교 (꼬리질문 대비) |
| 08 | [면접 사다리](08-interview-ladder.md) | 30초 · 2분 · 갈래별 꼬리질문 · 장애 시나리오 2개 | 심화 — ④ 말하기 연습 · 면접 전 |

권장: ① 에서 감으로 예측해 돌린 뒤, ② 에서는 필수 03 · 04 · 06 만 읽는다 — 03 으로 Q03 ~ Q05 를, 04 로 Q06 ~ Q08 을, 06 으로 구현을 준비한다. Q01 · Q02 · Q09 · Q10 에서 막히면 02 · 05 를 펼친다. 나머지는 심화 — 레슨을 마친 뒤 · 면접 전.

## 예측 답 접힘 규칙

- 문항(Qnn) 시나리오의 **결과 값**(숫자 · true/false · 성공/에러 코드)은 `<details>` 안에만 있다. 예측 전에 읽어도 답이 새지 않게 썼다.
- 일반 원리(예: "ON CONFLICT 는 원자적 삽입-또는-갱신을 보장한다")는 본문에 있다 — 원리 자체가 ② 의 공부 대상이다. 그래도 문항 값은 먼저 직접 적는다.
- 직접 돌려 본 psql 출력도 문항 장면과 같으면 `<details>` 안이다. 열기 전에 [observe/SCRIPT.md](../observe/SCRIPT.md) 로 관찰부터 해 본다.
- 예외: 08 면접 사다리는 ④ 복습용이라 답이 접혀 있되 문항 값을 말한다.
- 표기: `(실측: Qnn)` = 이 레슨 테스트(정답 상태), `(실측: psql 2026-10-13)` = PostgreSQL 16.14 컨테이너에서 직접, `(해석)` = 근거 문장에서 이은 판단.

## 그림

| 그림 | 어디서 | 위치 |
|---|---|---|
| 멱등성 — 확인과 선점 · pay() 흐름 (기존) | 01 | [../diagrams/idempotency.svg](../diagrams/idempotency.svg) |
| 같은 키로 두 요청이 부딪힐 때 (한 트랜잭션 · 예측 답이 보인다 — 03 에서는 접혀 있다) | 03 · 06 | [diagrams/key-race.svg](diagrams/key-race.svg) |
| 멱등 키의 상태 전이 (2-트랜잭션) | 06 | [diagrams/key-states.svg](diagrams/key-states.svg) |

다시 그리기(만든 사람용 · 레슨 폴더에서): `python3 -I docs/diagrams/draw.py`

## 이 레슨과 연결

- 손 작업: [예측](../src/test/java/deepdive/c01/l03/IdempotencyPredictTest.java) · [구현](../src/main/java/deepdive/c01/l03/PaymentService.java) · [관찰](../observe/SCRIPT.md) · [내 말로](../NOTES.md)
- 이어지는 레슨: 01.04 재고 · 잔고 동시 차감 · 02.03 outbox (외부 호출과 DB 커밋 사이의 틈)
