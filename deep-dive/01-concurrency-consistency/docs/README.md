# 트랙 01 개념 정리 — 동시성 · 정합성 (docs)

> 이 정리만 이해하고 외우면 "원리 → 엔진 내부 → 앱 설계 → 운영 · 장애" 로 이어지는 꼬리질문에 답할 수 있게 쓴 문서 묶음이다.
> 두 층이다: **레슨 docs**(레슨 폴더마다 `docs/`) 는 주제 하나를 깊게, **트랙 docs**(이 폴더) 는 레슨을 가로지르는 엔진 지도 · 장애 대응 · 선택 기준 · 질문 색인이다.

> **필수 / 심화**: 이 폴더의 트랙 공통 글(01 ~ 06)은 **모두 심화**다 — ② 에서 읽지 않는다. 레슨을 마친 뒤 · 면접 전에 꼬리질문 · 깊은 지식을 대비할 때 읽는다. 필수 글은 레슨 `docs/` 에만 있고, 어느 글이 필수인지는 각 레슨 docs README 의 "구분" 열에 있다.

> **읽는 법**: 01 · 02 · 03 · 05 · 06 은 블로그처럼 위에서 아래로 읽는 글이다 (그림과 함께). 04 는 질문 → 답이 있는 문서로 가는 색인이다.

## 언제 무엇을 읽나

| 때 | 읽을 것 |
|---|---|
| 레슨 ① 질문 · 첫 예측 | 아무것도 읽지 않는다 — 감으로 예측하고 돌린다 (틀려도 된다) |
| 레슨 ② 원리 | 그 레슨 `docs/` 의 **필수** 글만 — 레슨 README 의 ② 표 첫 행이 여기로 연결된다. 레슨 docs README 의 "구분" 열이 "어느 글이 어느 Qnn 을 되짚는 데 쓰이나" 를 알려 준다 |
| 레슨 ④ 내 말로 | 그 레슨의 면접 사다리(마지막 문서)로 소리 내어 연습 — 30초 답 → 2분 답 → 사다리 (사다리는 심화) |
| 레슨을 마친 뒤 · 면접 전 | 그 레슨 docs 의 **심화** 글 — 꼬리질문 · 깊은 지식 대비 |
| 01.01 을 끝낸 뒤 언제든 | [01 PostgreSQL 엔진 지도](01-postgres-engine-map.md) — 레슨에 나온 것들이 엔진 안 어디에 있나 |
| 01.02 를 끝낸 뒤 | [02 장애 대응 쿼리](02-observability-playbook.md) — 락 대기 · 오래 열린 트랜잭션 · 데드락을 운영에서 찾는 법 |
| 01.01 · 01.04 를 끝낸 뒤 | [05 Spring · JPA 로 오면](05-spring-jpa-mapping.md) — 예외 번역 · `@Lock` · `@Version` · 재시도 위치 · rollback-only (Spring Boot 3.5 실측) |
| 01.05 를 끝낸 뒤 | [06 dual write 와 outbox](06-outbox-dual-write.md) — DB 커밋과 메시지 발행 사이가 끊기면 |
| 트랙을 끝낸 뒤 | [03 동시성 문제 → 도구 고르기](03-concurrency-decision-guide.md) — "동시성 문제 어떻게 해결하세요?" 의 답 지도 |
| 면접 전 · 복습 | [04 꼬리질문 색인 · 외우는 순서](04-interview-index.md) — 상위 20문항 · 단계별 질문 → 답이 있는 문서 |

## 전체 목록

| 레슨 | 개념 문서 (읽는 순서 — 필수는 레슨 docs README 의 "구분" 열) | 면접 사다리 |
|---|---|---|
| [01.01 격리수준 · MVCC](../l01-isolation-mvcc/docs/README.md) | 이상 현상과 격리수준 → MVCC 저장 구조 → 스냅샷과 가시성 → 같은 행 쓰기 경쟁 → SERIALIZABLE · SSI · 재시도 → 운영(VACUUM · horizon · wraparound) | [07](../l01-isolation-mvcc/docs/07-interview-ladder.md) |
| [01.02 행 락 · 데드락](../l02-row-locks-deadlock/docs/README.md) | 락의 층 → 줄 서기의 실제 모양 → 줄 서지 않기 → 외래키와 락 모드 → 데드락 → 앱 · 프레임워크 · MySQL | [07](../l02-row-locks-deadlock/docs/07-interview-ladder.md) |
| [01.03 멱등성](../l03-idempotency/docs/README.md) | 멱등성과 재시도 → check-then-act → 유니크 제약과 동시 INSERT → ON CONFLICT → 실패한 트랜잭션 → 멱등 키 설계 → 앱 · 프레임워크 · MySQL | [08](../l03-idempotency/docs/08-interview-ladder.md) |
| [01.04 재고 · 잔고 동시 차감](../l04-stock-concurrency/docs/README.md) | 갱신 손실과 틈 → 원자 조건부 UPDATE → 비관 락 → 낙관 락 → 세 전략 비교 · 핫 로우 → MySQL InnoDB | [07](../l04-stock-concurrency/docs/07-interview-ladder.md) |
| [01.05 이벤트 중복 · 순서](../l05-event-order-dedupe/docs/README.md) | 전달 보장 → 순서가 뒤집히는 길 → inbox 로 중복 거르기 → version 으로 순서 지키기 → 설계 정리 → Spring Kafka · MySQL | [07](../l05-event-order-dedupe/docs/07-interview-ladder.md) |
| [01.06 원장과 대사](../l06-ledger-reconciliation/docs/README.md) | 숫자를 어떻게 저장하나 → 잔고와 원장 → 규칙은 언제 검사하나 → 원장에 기록하기 → 대사 | [06](../l06-ledger-reconciliation/docs/06-interview-ladder.md) |
| 트랙 공통 (이 폴더 · 모두 심화) | [01 엔진 지도](01-postgres-engine-map.md) · [02 장애 대응 쿼리](02-observability-playbook.md) · [03 도구 고르기](03-concurrency-decision-guide.md) · [05 Spring · JPA](05-spring-jpa-mapping.md) · [06 outbox](06-outbox-dual-write.md) · [04 꼬리질문 색인](04-interview-index.md) | 04 가 다섯 사다리와 트랙 문서 질문을 묶는다 |

## 표기 · 믿어도 되는 정도

- `[문서 13.2](링크)` — PostgreSQL 16 공식 문서(또는 MySQL 8.0 · Kafka · Spring · Hibernate 공식 문서 · PostgreSQL 소스 README)의 그 절에 실제로 있는 내용
- `(실측: Qnn)` — 이 레슨 테스트가 정답 상태에서 재는 것 · `(실측: psql 2026-10-13)` — PostgreSQL 16.14 컨테이너에서 직접 · `(실측: Hibernate 6.4.10 · 6.6.58)` · `(실측: Spring Boot 3.5.16)` — 스크래치 프로젝트에서 SQL 로그 · 예외 클래스로
- `(해석)` — 근거 문장에서 이은 판단이나 일반 설계 권고. 면접에서는 "제 판단으로는" 을 붙여 말한다
- 근거를 못 찾은 주장은 빼거나 "확인하지 못했다" 고 적었다. MySQL 은 이 트랙에서 직접 돌리지 않았다 — 공식 문서 문장까지만 믿는다
- 문서마다 작성자와 다른 검증자가 공식 문서 · 실측과 한 문장씩 대조했다 (2026-10-13). 그래도 버전이 바뀌면 숫자 · 기본값부터 다시 확인한다

## 예측 답 접힘 규칙 (레슨 docs 공통)

- 문항(Qnn)의 **결과 값**(숫자 · true/false · 성공/에러 코드)과 그 값을 그대로 보여 주는 실측 · 그림은 `<details>` 안에만 있다
- 메커니즘 · 원리는 펼쳐 둔다 — ② 에서 원리를 배우고 ③ 에서 그 원리로 예측하는 것이 학습 루프다
- 관찰 항목(예: 01.02 데드락에서 "누가 끊기나")의 실측도 접혀 있다 — observe/SCRIPT.md 로 먼저 본다

<sub>그림 다시 그리기(만든 사람용 · 이 트랙 폴더에서): `python3 -I docs/diagrams/draw.py` (엔진 지도) · `python3 -I docs/diagrams/draw_decision.py` (도구 고르기) · `draw_spring.py` (예외 지도) · `draw_outbox.py` (outbox)</sub>
