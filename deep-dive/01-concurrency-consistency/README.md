# 트랙 01 — 동시성 · 정합성 (PostgreSQL 16)

> 질문 하나로 묶인다: **"읽고 → 판단하고 → 쓴다" 사이에 남이 끼어들면?**

| 레슨 | 끼어드는 것 | 막는 도구 |
|---|---|---|
| [01.01 격리수준 · MVCC](l01-isolation-mvcc/README.md) | 다른 트랜잭션의 커밋 | 스냅샷 · SERIALIZABLE + 재시도 |
| [01.02 행 락 · 데드락](l02-row-locks-deadlock/README.md) | 같은 행을 노리는 쓰기 | FOR UPDATE · NOWAIT · SKIP LOCKED · 락 순서 |
| [01.03 멱등성](l03-idempotency/README.md) | 같은 요청의 재전송 | 유니크 제약 · ON CONFLICT · 멱등 키 |
| [01.04 재고·잔고 동시 차감](l04-stock-concurrency/README.md) | 50명이 동시에 | 원자 UPDATE · 낙관 락 · 비관 락 — 처리량 비교 |
| [01.05 이벤트 중복·순서](l05-event-order-dedupe/README.md) | 늦게 도착한 과거 이벤트 | inbox · version |
| [01.06 원장과 대사](l06-ledger-reconciliation/README.md) | 맞아야 하는 숫자가 어긋남 (기록 누락 · 중복 · 반올림) | numeric · append-only 원장 · 지연 제약 · 대사 쿼리 |

권장 순서는 위에서 아래. 01.01 의 결론("서로 다른 행을 고치는 경쟁은 행 락으로 못 막는다")이 01.02~01.04 의 출발점이다.
DB 는 당분간 PostgreSQL. MySQL InnoDB(갭 락 · next-key 락)와의 차이는 각 레슨 docs 의 MySQL 절에 공식 문서 기준으로 정리했다 (직접 돌려 보지는 않았다).

**개념 정리 — [docs/](docs/README.md)**: 레슨마다 `docs/`(개념 순서 + 면접 사다리)가 있고, 그중 **필수** 2~3편만 ② 원리에서 읽는다(① 에서 감으로 예측한 뒤). 나머지와 아래 트랙 공통 글은 모두 **심화**(꼬리질문 · 깊은 지식 대비 — 레슨을 마친 뒤 · 면접 전)다. 트랙 공통 6개 — [엔진 지도](docs/01-postgres-engine-map.md) · [장애 대응 쿼리](docs/02-observability-playbook.md) · [동시성 문제 → 도구 고르기](docs/03-concurrency-decision-guide.md) · [Spring · JPA 로 오면](docs/05-spring-jpa-mapping.md) · [dual write 와 outbox](docs/06-outbox-dual-write.md) · [꼬리질문 색인](docs/04-interview-index.md). 외워서 면접에 쓰는 정리다.
