# 01.05 개념 정리 — 이벤트 중복 · 순서 (docs)

> 이 문서들만 읽고 이해하면 "전달 보장 → 중복 · 역전 경로 → inbox · version → 설계 · 운영 → MySQL · Spring" 꼬리질문에 답할 수 있게 쓴 개념 정리다. 근거는 PostgreSQL 16 공식 문서 · Kafka 4.0 문서 · Spring Kafka · MySQL 8.0 문서와 이 레슨의 테스트 · psql 실측이다. 근거를 못 찾은 주장은 빼거나 `(해석)` 으로 표시했다.

> **읽는 법**: 개념 글(마지막 면접 사다리 앞까지)은 블로그처럼 위에서 아래로 읽는 연재다 — 장면 하나 → 개념을 하나씩(그림과 함께) → PostgreSQL 에서는 → 한눈에 정리 → 스스로 확인. 면접 대비는 마지막 사다리 글에서 한다.

> **필수 / 심화**: 필수 글(02 · 03 · 04)만 ② 원리에서 읽는다 — ① 에서 감으로 예측한 뒤, 틀린 문항이 왜 틀렸는지 찾으며. 나머지는 심화(꼬리질문 · 깊은 지식 대비)라 레슨을 마친 뒤 · 면접 전에 읽는다. 필수 글 분량은 공백 줄 · 이미지 줄을 뺀 약 27,032자 ≈ 68분(400자/분 추정)이라 ② 시간을 70분으로 잡았다. MySQL 비교 절은 필수 글 안에서도 "(심화)" 다 — 회사 서비스가 PostgreSQL 이라 MySQL 은 비교 참고다.

## 읽는 순서

| # | 문서 | 한 줄 | 구분 |
|---|---|---|---|
| 01 | [전달 보장](01-delivery-semantics.md) | at-most/at-least/exactly-once · 중복이 생기는 경로 · idempotent producer 의 범위 | 심화 — Q01 에서 막힐 때 (전달 보장) |
| 02 | [순서가 뒤집히는 길](02-ordering-paths.md) | 파티션 안 순서 · 재시도 · 병렬 소비 · 여러 생산자 | **필수** — Q02 되짚기 |
| 03 | [중복 거르기 — inbox](03-inbox-dedupe.md) | PK + ON CONFLICT DO NOTHING · 영향 행 수 · 한 트랜잭션 · 동시 같은 id | **필수** — Q04 · Q05 · Q06 · Q09 되짚기 |
| 04 | [순서 지키기 — version](04-version-ordering.md) | 조건부 upsert · stale · `<` vs `<=` · 동시 · version 이 없다면 | **필수** — Q03 · Q07 · Q08 · 구현 |
| 05 | [설계 정리](05-design-patterns.md) | idempotent consumer · 부수 효과 · inbox 보존 · outbox(02.03 예고) | 심화 — 설계 정리 (구현 뒤 · 면접 전) |
| 06 | [앱 · 프레임워크 · MySQL](06-spring-kafka-mysql.md) | Spring Kafka 커밋 · 재시도 · `INSERT IGNORE` · `ON DUPLICATE KEY UPDATE` | 심화 — Spring Kafka · MySQL (꼬리질문 대비) |
| 07 | [면접 사다리](07-interview-ladder.md) | 30초 · 2분 · 갈래별 꼬리질문 · 장애 시나리오 | 심화 — ④ 말하기 연습 · 면접 전 |

권장: ① 에서 감으로 예측해 돌린 뒤, ② 에서는 필수 02 · 03 · 04 만 읽는다 — 02 로 Q02 를, 03 으로 Q04 · Q05 · Q06 · Q09 를, 04 로 Q03 · Q07 · Q08 과 구현을 되짚는다. Q01 에서 막히면 01 을 펼친다. 나머지는 심화 — 레슨을 마친 뒤 · 면접 전.

## 예측 답 접힘 규칙

- 문항(Qnn) 시나리오의 **결과 값**(숫자 · true/false · 상태 값)은 `<details>` 안에만 있다. 예측 전에 읽어도 답이 새지 않게 썼다.
- 일반 원리(예: "DO NOTHING 은 충돌 행을 건너뛴다", "조건은 마지막에 평가된다", "inbox 와 반영은 한 트랜잭션")는 본문에 있다 — 원리 자체가 ② 의 공부 대상이다. 그래도 문항 값을 먼저 직접 적는다.
- 직접 돌려 본 psql 출력도 문항 장면과 같으면 `<details>` 안이다. 열기 전에 [observe/SCRIPT.md](../observe/SCRIPT.md) 로 관찰부터 해 본다.
- 표기: `(실측: Qnn)` = 이 레슨 테스트(정답 상태), `(실측: psql 2026-10-13)` = PostgreSQL 16.14 컨테이너에서 직접, `(해석)` = 근거 문장에서 이은 판단이거나 확인하지 못한 것.

## 그림

| 그림 | 어디서 | 위치 |
|---|---|---|
| 이벤트 중복 · 순서 — 도착한 순간 (기존) | 05 | [../diagrams/event-dedupe.svg](../diagrams/event-dedupe.svg) |
| 중복과 역전이 생기는 길 | 01 · 02 | [diagrams/dup-order-paths.svg](diagrams/dup-order-paths.svg) |

다시 그리기(만든 사람용 · 레슨 폴더에서): `python3 -I docs/diagrams/draw.py`

## 이 레슨과 연결

- 손 작업: [예측](../src/test/java/deepdive/c01/l05/DedupePredictTest.java) · [구현](../src/main/java/deepdive/c01/l05/EventApplier.java) · [관찰](../observe/SCRIPT.md) · [내 말로](../NOTES.md)
- 이웃: 유니크 제약 · ON CONFLICT · `23505`/`25P02` 는 [01.03 docs](../../l03-idempotency/docs/README.md), MVCC · READ COMMITTED 재평가 · `40001` 재시도는 [01.01 docs](../../l01-isolation-mvcc/docs/README.md). 이어지는 레슨: 02.03 outbox · 멱등 소비 (아직 없음)
