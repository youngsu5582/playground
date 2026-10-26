# 04. 꼬리질문 색인 · 외우는 순서

> **한 줄**: 01.01 ~ 01.06 레슨 docs 에 흩어진 꼬리질문을 면접 흐름(기초 → 엔진 내부 → 앱 설계 → 운영 · 장애) 순서로 모은 색인이다. **답은 복사하지 않는다** — 질문 한 줄과 답이 있는 문서만 적는다. 원본이 하나여야 고칠 때 어긋나지 않는다.
> **구분**: 심화 — 꼬리질문 대비 (면접 직전). 처음에는 "상위 20문항" 으로 소리 내어 답하는 연습부터 한다

## 쓰는 법

- 각 문서의 답은 `<details>` 안에 접혀 있다. 질문을 읽고 **먼저 소리 내어 답한 뒤** 연다.
- "사다리" 는 각 레슨의 `면접 사다리` 문서(01.03 만 08, 나머지는 07)다. 30초 답 · 2분 답 · 갈래별 꼬리질문 · 모를 때 · 장애 시나리오가 한 파일에 있다.
- "개념 문서의 꼬리질문" 은 각 개념 문서 끝의 `## 꼬리질문` 절이다. 사다리보다 한 주제에 깊이 들어간다.
- `공통 · 01` · `공통 · 02` 는 이 폴더(docs/)의 [01](01-postgres-engine-map.md) · [02](02-observability-playbook.md) 문서다.
- 문서 이름은 `레슨 · 번호` 로 줄여 쓴다 (예: 01.04 · 02 = [l04-stock-concurrency/docs/02-…](../l04-stock-concurrency/docs/02-atomic-conditional-update.md)).
- 문제 모양에서 도구를 고르는 답 지도는 [03-concurrency-decision-guide.md](03-concurrency-decision-guide.md), 관찰 쿼리는 [02-observability-playbook.md](02-observability-playbook.md).

### 레슨별 사다리 (30초 답이 맨 위에 있다)

| 레슨 | 사다리 | 30초 답의 첫 질문 |
|---|---|---|
| 01.01 격리수준 · MVCC | [07](../l01-isolation-mvcc/docs/07-interview-ladder.md) | PostgreSQL 의 격리수준과 MVCC 를 설명해 보세요 |
| 01.02 행 락 · 데드락 | [07](../l02-row-locks-deadlock/docs/07-interview-ladder.md) | 같은 행을 동시에 고치는 트랜잭션은 어떻게 처리되고, 데드락은 어떻게 다루나요 |
| 01.03 멱등성 | [08](../l03-idempotency/docs/08-interview-ladder.md) | 결제 API 에서 타임아웃 뒤 재시도가 와도 중복 결제가 안 되게 하려면 |
| 01.04 재고 · 잔고 | [07](../l04-stock-concurrency/docs/07-interview-ladder.md) | 재고 10개에 50명이 동시에 사면 어떻게 막나요 |
| 01.05 이벤트 중복 · 순서 | [07](../l05-event-order-dedupe/docs/07-interview-ladder.md) | 이벤트가 중복으로 오고 순서가 뒤집혀도 상태가 맞게 하려면 |
| 01.06 원장과 대사 | [06](../l06-ledger-reconciliation/docs/06-interview-ladder.md) | 돈처럼 맞아야 하는 숫자를 어떻게 저장하고, 틀렸을 때 어떻게 알아채나요 |

## 상위 20문항 — 처음 들으면 이 순서로 대답 연습

기초 → 엔진 → 앱 설계 → 장애 순이다. 각 문항의 30초 답 · 꼬리 답은 표의 사다리 문서(갈래는 괄호)에 접혀 있다.

| # | 질문 | 답이 있는 사다리 |
|---|---|---|
| 1 | PostgreSQL 의 격리수준과 MVCC 를 설명해 보세요 | [01.01 사다리](../l01-isolation-mvcc/docs/07-interview-ladder.md) (30초 답 · 2분 답) |
| 2 | UPDATE 하면 디스크에서 무슨 일이 일어나나요? 다른 세션이 고치는 중인 행을 읽으면요 | [01.01 사다리](../l01-isolation-mvcc/docs/07-interview-ladder.md) (갈래 C) |
| 3 | READ COMMITTED 에서 잔고 차감을 안전하게 하려면? 같은 UPDATE 를 REPEATABLE READ 에서 하면요 | [01.01 사다리](../l01-isolation-mvcc/docs/07-interview-ladder.md) (갈래 B) |
| 4 | REPEATABLE READ 에서 write skew 가 왜 생기고 어떻게 막나요 | [01.01 사다리](../l01-isolation-mvcc/docs/07-interview-ladder.md) (갈래 A) |
| 5 | 같은 행을 동시에 고치는 트랜잭션은 어떻게 처리되고 데드락은 어떻게 다루나요 | [01.02 사다리](../l02-row-locks-deadlock/docs/07-interview-ladder.md) (30초 답 · 갈래 B) |
| 6 | 재고 10개에 50명이 동시에 사면 어떻게 막나요 | [01.04 사다리](../l04-stock-concurrency/docs/07-interview-ladder.md) (30초 답) |
| 7 | 조건부 UPDATE 는 락을 안 쓰는데 왜 안전한가요 | [01.04 사다리](../l04-stock-concurrency/docs/07-interview-ladder.md) (갈래 A) |
| 8 | 낙관 락과 비관 락은 언제 무엇을 쓰나요 | [01.04 사다리](../l04-stock-concurrency/docs/07-interview-ladder.md) (갈래 B) |
| 9 | 선착순 이벤트에 한 상품으로 수만 명이 몰리면요 | [01.04 사다리](../l04-stock-concurrency/docs/07-interview-ladder.md) (갈래 C) |
| 10 | 작업 큐를 DB 로 만들면 어떻게 짜나요 | [01.02 사다리](../l02-row-locks-deadlock/docs/07-interview-ladder.md) (갈래 A) |
| 11 | 결제 API 에서 타임아웃 뒤 재시도가 와도 중복 결제가 안 되게 하려면 | [01.03 사다리](../l03-idempotency/docs/08-interview-ladder.md) (30초 답) |
| 12 | 같은 키로 요청이 동시에 두 번 오면 DB 는 어떻게 하나요 | [01.03 사다리](../l03-idempotency/docs/08-interview-ladder.md) (갈래 A) |
| 13 | 확인하고 넣으면 안 되나요? 유니크 제약이면 충분한가요 | [01.03 사다리](../l03-idempotency/docs/08-interview-ladder.md) (갈래 B) |
| 14 | 결제 승인은 성공했는데 DB 커밋이 실패하면요 | [01.03 사다리](../l03-idempotency/docs/08-interview-ladder.md) (갈래 C) |
| 15 | 이벤트가 중복으로 오고 순서가 뒤집혀도 상태가 맞게 하려면 | [01.05 사다리](../l05-event-order-dedupe/docs/07-interview-ladder.md) (30초 답) |
| 16 | Kafka 가 exactly-once 를 지원한다던데 중복 처리는 필요 없나요 | [01.05 사다리](../l05-event-order-dedupe/docs/07-interview-ladder.md) (갈래 A) |
| 17 | inbox 기록과 상태 갱신을 왜 한 트랜잭션에 묶나요 | [01.05 사다리](../l05-event-order-dedupe/docs/07-interview-ladder.md) (갈래 B) |
| 18 | 순서가 뒤집혀 온 이벤트는 어떻게 처리하나요 | [01.05 사다리](../l05-event-order-dedupe/docs/07-interview-ladder.md) (갈래 C) |
| 19 | 락 때문에 서비스가 느려졌어요 — 어디부터 보나요 | [01.02 사다리](../l02-row-locks-deadlock/docs/07-interview-ladder.md) (갈래 C · 장애 시나리오) |
| 20 | 테이블이 계속 커지고 쿼리가 느려져요 — autovacuum 은 돌고 있는데요 | [01.01 사다리](../l01-isolation-mvcc/docs/07-interview-ladder.md) (갈래 C · 장애 시나리오 1) |

## 1. 기초 — 격리수준 · 이상 현상 · MVCC 개념

| 질문 | 답이 있는 문서 |
|---|---|
| 더티 리드 · 반복 불가 읽기 · 팬텀 · write skew 가 각각 무엇이고 어느 수준에서 막히나 | [01.01 · 01](../l01-isolation-mvcc/docs/01-anomalies-and-isolation-levels.md) |
| READ UNCOMMITTED 를 PostgreSQL 에서 쓰면 무슨 일이 생기나 | [01.01 · 01](../l01-isolation-mvcc/docs/01-anomalies-and-isolation-levels.md) (꼬리질문 1) |
| REPEATABLE READ 에서 팬텀이 안 생기는데 SERIALIZABLE 이 왜 필요한가 | [01.01 · 01](../l01-isolation-mvcc/docs/01-anomalies-and-isolation-levels.md) (꼬리질문 2) |
| 읽기 전용 트랜잭션에서 REPEATABLE READ 와 SERIALIZABLE 의 차이는 | [01.01 · 01](../l01-isolation-mvcc/docs/01-anomalies-and-isolation-levels.md) (꼬리질문 3) |
| 격리수준을 올렸더니 `40001` 이 쏟아진다 — 격리수준 문제인가 앱 문제인가 | [01.01 · 01](../l01-isolation-mvcc/docs/01-anomalies-and-isolation-levels.md) (꼬리질문 4) |
| "읽기는 쓰기를 막지 않는다" 에 예외가 있나 | [01.01 · 03](../l01-isolation-mvcc/docs/03-snapshot-visibility.md) |
| 같은 `@Transactional` 메서드 안에서 `findById` 를 두 번 부르면 값이 바뀔 수 있나 | [01.01 · 03](../l01-isolation-mvcc/docs/03-snapshot-visibility.md) |
| 확인하고 넣기(`if (!exists) save()`)는 왜 깨지나 | [01.03 · 02](../l03-idempotency/docs/02-check-then-act.md) |
| 타임아웃은 왜 실패가 아니라 "모름" 인가 · 왜 `POST` 에만 멱등 키가 필요한가 | [01.03 · 01](../l03-idempotency/docs/01-idempotency-and-retry.md) |
| at-most-once · at-least-once · exactly-once 는 무엇이 다른가 | [01.05 · 01](../l05-event-order-dedupe/docs/01-delivery-semantics.md) |
| 같은 행을 잠그는 락 4모드와 테이블 락은 무엇이 다르고 평범한 SELECT 는 무엇이 막나 | [01.02 · 01](../l02-row-locks-deadlock/docs/01-lock-modes-and-storage.md) |
| 읽고 계산해서 쓰면 왜 갱신 손실이 생기나 · 틈을 없애는 방법과 감지하는 방법의 차이 | [01.04 · 01](../l04-stock-concurrency/docs/01-lost-update-and-the-gap.md) |

## 2. 엔진 내부 — 저장 · 락 · 대기 · 충돌

| 질문 | 답이 있는 문서 |
|---|---|
| 같은 행을 1만 번 UPDATE 하면 테이블은 왜 커지고 어떻게 확인하나 | [01.01 · 02](../l01-isolation-mvcc/docs/02-mvcc-tuple-storage.md) (꼬리질문 1) |
| `xmax` 가 있는 행이 읽히는 이유 · `ctid` 가 같으면 같은 버전인가 · HOT 이 안 되는 조건 | [01.01 · 02](../l01-isolation-mvcc/docs/02-mvcc-tuple-storage.md) |
| `pg_current_snapshot()` 의 `xmin:xmax:xip` 로 튜플 가시성을 어떻게 판정하나 | [01.01 · 03](../l01-isolation-mvcc/docs/03-snapshot-visibility.md) |
| 같은 행 UPDATE 가 부딪히면 READ COMMITTED 와 REPEATABLE READ 는 무엇이 갈리나 | [01.01 · 04](../l01-isolation-mvcc/docs/04-write-conflicts.md) |
| 행 락은 어디에 저장되나 · 락을 100만 행에 걸면 메모리는 | [01.01 · 04](../l01-isolation-mvcc/docs/04-write-conflicts.md) · [01.02 · 01](../l02-row-locks-deadlock/docs/01-lock-modes-and-storage.md) |
| 두 트랜잭션이 같은 행에 `FOR SHARE` 를 걸면 `xmax` 에 무엇이 있나 (MultiXact) | [01.02 · 01](../l02-row-locks-deadlock/docs/01-lock-modes-and-storage.md) |
| `wait_event = transactionid` 는 무엇을 기다리나 · 세 세션이 기다릴 때 `blocked_by` 는 | [01.02 · 02](../l02-row-locks-deadlock/docs/02-waiting-and-observing.md) |
| 뒤늦게 들어온 `ALTER TABLE` 때문에 읽기까지 멈추는 이유 | [01.02 · 02](../l02-row-locks-deadlock/docs/02-waiting-and-observing.md) |
| 외래키가 있으면 자식 INSERT 가 부모에 무슨 락을 거나 · 자식 FK 열에 인덱스가 없으면 | [01.02 · 04](../l02-row-locks-deadlock/docs/04-foreign-keys-and-lock-modes.md) |
| 데드락은 어떻게 감지하나 · 누가 끊기나 · `deadlock_timeout` 을 줄이면 | [01.02 · 05](../l02-row-locks-deadlock/docs/05-deadlock.md) |
| `FOR SHARE` 로 읽고 각자 UPDATE 하면 왜 데드락인가 (락 업그레이드) | [01.02 · 05](../l02-row-locks-deadlock/docs/05-deadlock.md) |
| SERIALIZABLE 은 락을 거나 · rw-의존성 한 방향과 두 방향 · 오탐 | [01.01 · 05](../l01-isolation-mvcc/docs/05-serializable-ssi-retry.md) |
| 유니크 인덱스에서 같은 키의 미커밋 INSERT 앞에서 뒤의 INSERT 는 무엇을 하나 | [01.03 · 03](../l03-idempotency/docs/03-unique-constraint-concurrent-insert.md) |
| 실패한 트랜잭션이 중단 상태(`25P02`)가 되는 이유 · 기존 행을 읽는 세 가지 방법 | [01.03 · 05](../l03-idempotency/docs/05-failed-transaction.md) |
| `ON CONFLICT DO NOTHING` 의 0행이 알려 주는 것과 모르는 것 · `DO UPDATE` 가 보장하는 것 | [01.03 · 04](../l03-idempotency/docs/04-on-conflict.md) |
| 이벤트 순서는 어디까지 보장되고 어디서 뒤집히나 · 파티션을 늘리면 | [01.05 · 02](../l05-event-order-dedupe/docs/02-ordering-paths.md) |
| idempotent producer 가 막는 것과 못 막는 것 | [01.05 · 01](../l05-event-order-dedupe/docs/01-delivery-semantics.md) |
| 앱이 커밋 성공을 받았다 — 이 순간 디스크에는 무엇이 써져 있나 | [공통 · 01](01-postgres-engine-map.md) (꼬리질문 1) |
| 크래시 뒤 복구는 어디서부터 시작하나 · 복구 시간은 무엇이 좌우하나 | [공통 · 01](01-postgres-engine-map.md) (꼬리질문 2) |
| 락은 어디에 저장되나 · 행 락이 수백만 개여도 락 테이블이 안 터지는 이유는 | [공통 · 01](01-postgres-engine-map.md) (꼬리질문 3) |

## 3. 앱 설계 — 도구 고르기 · 재시도 · 멱등 · 이벤트

| 질문 | 답이 있는 문서 |
|---|---|
| 원자 조건부 UPDATE 에서 `qty >= 1` 을 빼면 · 여러 상품을 차례로 차감하면 | [01.04 · 02](../l04-stock-concurrency/docs/02-atomic-conditional-update.md) |
| 비관 락을 모든 곳에 쓰면 되나 · 아직 없는 행에 `FOR UPDATE` 하면 무엇이 잠기나 | [01.04 · 03](../l04-stock-concurrency/docs/03-pessimistic-lock.md) |
| 낙관 락 재시도 상한은 어떻게 정하나 · 재시도 루프를 `@Transactional` 안에 두면 | [01.04 · 04](../l04-stock-concurrency/docs/04-optimistic-lock.md) |
| 편집 화면을 열어 두고 10분 뒤 저장하는 흐름에는 어떤 전략이 맞나 | [01.04 · 04](../l04-stock-concurrency/docs/04-optimistic-lock.md) |
| 낙관 · 비관 · 원자 UPDATE 를 경합에 따라 어떻게 고르나 · 한 행이 병목이면 | [01.04 · 05](../l04-stock-concurrency/docs/05-choosing-and-hot-row.md) |
| `40001` 을 받으면 앱은 무엇을 하나 · 재시도 안에 결제 API 가 있으면 · 상한 값은 누가 정한 것인가 | [01.01 · 05](../l01-isolation-mvcc/docs/05-serializable-ssi-retry.md) |
| 긴 리포트 쿼리를 SERIALIZABLE 로 돌릴 때 쓰기 트랜잭션이 대신 실패하지 않게 하려면 | [01.01 · 05](../l01-isolation-mvcc/docs/05-serializable-ssi-retry.md) |
| 이체에서 A→B 와 B→A 가 동시에 오면 어떻게 예방하나 · 순서를 정할 수 없으면 | [01.02 · 05](../l02-row-locks-deadlock/docs/05-deadlock.md) |
| `FOR UPDATE` 와 `SKIP LOCKED` 의 차이 · 워커가 일하다 죽으면 · `NOWAIT` 와 `lock_timeout = 0` | [01.02 · 03](../l02-row-locks-deadlock/docs/03-not-waiting.md) |
| `SET` 과 `SET LOCAL` 중 락 타임아웃에는 무엇을 쓰나 · 커넥션 풀에서는 | [01.02 · 03](../l02-row-locks-deadlock/docs/03-not-waiting.md) |
| 서버가 한 대여도 `synchronized` 로 충분하지 않은 이유 · 분산 락을 써도 DB 제약이 필요한가 | [01.03 · 02](../l03-idempotency/docs/02-check-then-act.md) |
| 같은 키에 다른 금액이 오면 · 처리 중인 같은 키가 오면 기다릴까 409 일까 | [01.03 · 06](../l03-idempotency/docs/06-idempotency-key-design.md) |
| 서버가 처리 도중 죽으면 키는 · 실패 결과를 키에 저장하나 · 키 만료는 얼마로 | [01.03 · 06](../l03-idempotency/docs/06-idempotency-key-design.md) |
| 클라이언트가 키를 만들게 하는 이유 · 멱등 키와 요청 본문 해시는 같은가 | [01.03 · 01](../l03-idempotency/docs/01-idempotency-and-retry.md) · [01.03 · 06](../l03-idempotency/docs/06-idempotency-key-design.md) |
| inbox · version 조건부 upsert 의 `<` 와 `<=` · delta 이벤트 · version 이 없을 때 | [01.05 · 04](../l05-event-order-dedupe/docs/04-version-ordering.md) · [01.05 · 02](../l05-event-order-dedupe/docs/02-ordering-paths.md) |
| inbox 가 없고 version 만 있으면 무엇이 새나 · 포인트 적립은 무엇이 "한 번" 을 보장하나 | [01.05 · 03](../l05-event-order-dedupe/docs/03-inbox-dedupe.md) · [01.05 · 05](../l05-event-order-dedupe/docs/05-design-patterns.md) |
| inbox 와 outbox 의 차이 · inbox 보관 기간 | [01.05 · 05](../l05-event-order-dedupe/docs/05-design-patterns.md) |
| JPA · Spring 에서는 — 비관 락 SQL · 유니크 위반 예외 · `@Version` · 재시도 위치 | [01.02 · 06](../l02-row-locks-deadlock/docs/06-app-and-mysql.md) · [01.03 · 07](../l03-idempotency/docs/07-app-framework-mysql.md) · [01.04 · 04](../l04-stock-concurrency/docs/04-optimistic-lock.md) |
| `@KafkaListener` 가 같은 메시지로 두 번 호출되는 경우 · 예외 뒤 재시도는 언제까지 | [01.05 · 06](../l05-event-order-dedupe/docs/06-spring-kafka-mysql.md) |
| `max_connections` 를 1000 으로 올리면 해결되나 | [공통 · 01](01-postgres-engine-map.md) (꼬리질문 4) |
| PgBouncer 를 transaction 모드로 쓰면 무엇이 깨질 수 있나 | [공통 · 01](01-postgres-engine-map.md) (꼬리질문 5) |
| 커넥션 풀 크기를 어떻게 정하나 · CPU 코어 8개에 풀을 200으로 잡으면 | [공통 · 01](01-postgres-engine-map.md) (꼬리질문 7) |
| 풀에서 커넥션을 못 받는 대기가 날 때 풀을 키우면 해결되나 | [공통 · 01](01-postgres-engine-map.md) (꼬리질문 8) |
| MySQL InnoDB 라면 — 기본 격리수준 · UPDATE 와 일관된 읽기 · 갭 락 · 데드락 · `INSERT IGNORE` · ODKU | [01.01 · 01](../l01-isolation-mvcc/docs/01-anomalies-and-isolation-levels.md) · [01.02 · 06](../l02-row-locks-deadlock/docs/06-app-and-mysql.md) · [01.03 · 07](../l03-idempotency/docs/07-app-framework-mysql.md) · [01.04 · 06](../l04-stock-concurrency/docs/06-mysql-innodb.md) · [01.05 · 06](../l05-event-order-dedupe/docs/06-spring-kafka-mysql.md) |
| 유니크 위반 · 직렬화 실패 · 데드락 · 락 대기 실패가 JdbcTemplate 과 JPA 에서 각각 어떤 예외로 오나 · 언제 나나 | [공통 · 05](05-spring-jpa-mapping.md) (꼬리질문 1 · 2 · 7) |
| `@Transactional` 메서드 안에서 DB 예외를 catch 하고 계속하면 어떻게 되나 | [공통 · 05](05-spring-jpa-mapping.md) (꼬리질문 3) |
| 재시도는 어디에 두나 · 같은 클래스에 두면 왜 안 되나 (self-invocation) | [공통 · 05](05-spring-jpa-mapping.md) (꼬리질문 4) |
| `@Lock(PESSIMISTIC_WRITE)` 는 어떤 SQL 이 나가나 · NOWAIT 는 · `@Version` 충돌은 어떤 예외이고 어떻게 재시도하나 | [공통 · 05](05-spring-jpa-mapping.md) (꼬리질문 5 · 6) |
| 저장 후 발행을 코드 두 줄로 쓰면 어떤 장애가 나나 · 순서를 바꾸면 해결되나 · Kafka 트랜잭션이 있으면 outbox 가 필요 없나 | [공통 · 06](06-outbox-dual-write.md) (꼬리질문 1 · 5) |
| 릴레이가 발행 후 표시 전에 죽으면 · 폴링 릴레이를 둘 띄우면 · 폴링 vs CDC | [공통 · 06](06-outbox-dual-write.md) (꼬리질문 2 ~ 4) |
| `acks` 의 기본값과 의미 · `acks=all` 이면 메시지를 절대 안 잃나 · `min.insync.replicas` 를 복제 계수와 같게 두면 · 리더 선출과 유실 | [01.05 · 01](../l05-event-order-dedupe/docs/01-delivery-semantics.md) (꼬리질문 5 · 6) · [01.05 · 07](../l05-event-order-dedupe/docs/07-interview-ladder.md) (갈래 E) |
| 금액을 float 로 저장하면 안 되나 · numeric 이면 안전한가 · 정수(센트)로 담는 방식과 비교하면 | [01.06 · 01](../l06-ledger-reconciliation/docs/01-numbers-float-numeric.md) · [01.06 · 06](../l06-ledger-reconciliation/docs/06-interview-ladder.md) (갈래 A) |
| 잔고 컬럼이 있는데 왜 원장이 따로 필요한가 · 잘못 올라간 거래는 어떻게 바로잡나 | [01.06 · 02](../l06-ledger-reconciliation/docs/02-balance-and-ledger.md) · [01.06 · 06](../l06-ledger-reconciliation/docs/06-interview-ladder.md) (갈래 B) |
| 이체 두 다리의 합 0 은 언제 검사하나 · CHECK 로 안 되는 이유 · 지연 제약의 대가 | [01.06 · 03](../l06-ledger-reconciliation/docs/03-when-rules-are-checked.md) · [01.06 · 06](../l06-ledger-reconciliation/docs/06-interview-ladder.md) (갈래 C) |
| 같은 거래가 두 번 · 동시에 오면 · 반대 방향 이체가 섞이면 | [01.06 · 04](../l06-ledger-reconciliation/docs/04-posting-to-the-ledger.md) · [01.06 · 06](../l06-ledger-reconciliation/docs/06-interview-ladder.md) (갈래 D) |

## 4. 운영 · 장애 — 증상에서 거슬러 올라가기

| 질문 (증상) | 답이 있는 문서 |
|---|---|
| 테이블이 계속 커지고 쿼리가 느려진다 (autovacuum 은 돈다) | [01.01 · 06](../l01-isolation-mvcc/docs/06-operations-vacuum-horizon.md) · [01.01 사다리](../l01-isolation-mvcc/docs/07-interview-ladder.md) (장애 시나리오 1) |
| `idle_in_transaction_session_timeout` 을 짧게 걸면 부작용은 · VACUUM 과 VACUUM FULL · XID wraparound | [01.01 · 06](../l01-isolation-mvcc/docs/06-operations-vacuum-horizon.md) |
| SERIALIZABLE 로 올렸더니 간헐적으로 500 | [01.01 사다리](../l01-isolation-mvcc/docs/07-interview-ladder.md) (장애 시나리오 2) |
| API 가 점점 느려지고 커넥션 풀이 마른다 (락 대기) | [01.02 사다리](../l02-row-locks-deadlock/docs/07-interview-ladder.md) (장애 시나리오 1) |
| 배포 중 `ALTER TABLE` 때문에 서비스 전체가 멈췄다 | [01.02 사다리](../l02-row-locks-deadlock/docs/07-interview-ladder.md) (장애 시나리오 2) · [01.02 · 02](../l02-row-locks-deadlock/docs/02-waiting-and-observing.md) |
| 이체 API 가 간헐적으로 500 — `deadlock detected` | [01.02 사다리](../l02-row-locks-deadlock/docs/07-interview-ladder.md) (장애 시나리오 3) · [01.02 · 05](../l02-row-locks-deadlock/docs/05-deadlock.md) |
| 중복 결제가 발생했다 | [01.03 사다리](../l03-idempotency/docs/08-interview-ladder.md) (시나리오 1) |
| 재시도 폭주로 응답이 느려지고 커넥션이 고갈된다 | [01.03 사다리](../l03-idempotency/docs/08-interview-ladder.md) (시나리오 2) · [01.03 · 03](../l03-idempotency/docs/03-unique-constraint-concurrent-insert.md) |
| 선착순 이벤트 직후 DB CPU · 락 대기가 급증한다 | [01.04 사다리](../l04-stock-concurrency/docs/07-interview-ladder.md) (장애 시나리오 1) |
| 재고 숫자는 정상인데 주문 건수가 재고보다 많다 | [01.04 사다리](../l04-stock-concurrency/docs/07-interview-ladder.md) (장애 시나리오 2) · [01.04 · 01](../l04-stock-concurrency/docs/01-lost-update-and-the-gap.md) |
| 재배포 중 리밸런스로 같은 이벤트가 대량으로 다시 처리된다 | [01.05 사다리](../l05-event-order-dedupe/docs/07-interview-ladder.md) (장애 시나리오 1) |
| 순서 역전으로 상태가 과거로 돌아갔다 | [01.05 사다리](../l05-event-order-dedupe/docs/07-interview-ladder.md) (장애 시나리오 2) |
| `ps` 에 `idle in transaction` 이 오래 보인다 — 무슨 뜻이고 무엇을 하나 | [공통 · 01](01-postgres-engine-map.md) (꼬리질문 6) |
| 락 때문에 요청이 멈췄다 — 가장 먼저 무엇을 하나 | [공통 · 02](02-observability-playbook.md) (꼬리질문 1) |
| `pg_cancel_backend` 와 `pg_terminate_backend` 의 차이 · 반환값 `true` 의 의미 | [공통 · 02](02-observability-playbook.md) (꼬리질문 2) |
| 같은 쿼리가 "가끔 느리다" 를 사후에 어떻게 보나 | [공통 · 02](02-observability-playbook.md) (꼬리질문 3) |
| 데드락이 났다는 걸 모니터링으로 어떻게 알고 원인은 어디서 보나 | [공통 · 02](02-observability-playbook.md) (꼬리질문 4) |
| 디스크가 갑자기 찬다 — 테이블 말고 의심할 것은 | [공통 · 02](02-observability-playbook.md) (꼬리질문 5) |
| 처리 시간이 늘어난 뒤 중복 처리가 늘었다 (`max.poll.interval.ms` · 리밸런스) | [01.05 · 01](../l05-event-order-dedupe/docs/01-delivery-semantics.md) (꼬리질문 7) |
| 대사에서 "잔고 ≠ 원장 합" 이 나왔다 · 대사는 어떻게 하나 · 왜 FULL OUTER JOIN 인가 | [01.06 · 05](../l06-ledger-reconciliation/docs/05-reconciliation.md) · [01.06 · 06](../l06-ledger-reconciliation/docs/06-interview-ladder.md) (갈래 E · 시나리오 1) |

## 모를 때 — 정직하게 아는 데까지 말하는 법

각 사다리의 `모를 때` 절에 그 레슨에서 확인하지 못한 것과 말하는 틀이 있다. 면접 전에 한 번씩 소리 내어 읽는다.

- [01.01 사다리](../l01-isolation-mvcc/docs/07-interview-ladder.md) — SIREAD 락 단위 · MySQL 추론 · hint bit 용어 · 숫자를 외우지 않기
- [01.02 사다리](../l02-row-locks-deadlock/docs/07-interview-ladder.md) — tuple 락 구현 · 데드락 희생자 · JPA 락 타임아웃
- [01.03 사다리](../l03-idempotency/docs/08-interview-ladder.md) — ON CONFLICT 의 RR 동작 · JPA 예외 번역 · Idempotency-Key 표준 여부
- [01.04 사다리](../l04-stock-concurrency/docs/07-interview-ladder.md) — `@Version` 의 SQL · `FOR UPDATE ORDER BY` 순서 · 직접 구현하지 않은 핫 로우 대안
- [01.05 사다리](../l05-event-order-dedupe/docs/07-interview-ladder.md) — 리밸런스 시점 · MySQL 영향 행 수 · Spring Kafka 재시도 횟수

공통 틀 (해석 — 사다리들의 문장을 묶은 요약): "정확한 내부 구현은 확인해 봐야 하지만, **관찰한 것은 …**" 으로 시작하고, 추론이면 추론이라고 밝히고, 기본값은 `SHOW` 로 확인한다고 말한다.

## 외우는 계획 (해석 — 학습 방법이라 근거 표시 없음)

1. **1회차 — 이해**: 레슨 docs 를 순서대로 읽는다. 예측 문항을 먼저 적고 접힌 답을 연다. 이 색인은 아직 보지 않는다.
2. **2회차 — 소리 내어 30초 답**: 상위 20문항을 위에서부터, 사다리의 30초 답을 열기 전에 소리 내어 말한다. 막히면 해당 개념 문서만 다시 읽는다. 하루 5문항 정도로 나눈다.
3. **3회차 — 사다리 끝까지**: 문항 하나에서 꼬리질문이 이어지는 길을 갈래 끝까지 말한다. 이후 `모를 때` 절과 장애 시나리오를 읽고 확인 쿼리를 손으로 쳐 본다.
4. **유지**: 절 1 ~ 4 의 표에서 약한 질문만 뽑아 간격을 두고 다시 한다. 답을 그대로 외우기보다 "문제 모양 → 도구 → 실패 신호 → 재시도" ([03 문서](03-concurrency-decision-guide.md)) 뼈대로 말한다.

## 이 문서의 한계

- 질문 문구는 사다리와 개념 문서의 꼬리질문을 줄여 쓴 것이다. 원문과 다르면 원문이 맞다.
- 새로 만든 사실 주장은 없다. 답 · 근거 · 실측은 모두 링크한 문서에 있다.
