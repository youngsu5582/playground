# 01.02 개념 정리 — 행 락 · 데드락 (docs)

> 이 문서들만 읽고 이해하면 "원리 → 엔진 내부 → 운영 · 장애 → 설계 선택" 꼬리질문에 답할 수 있게 쓴 개념 정리다. 근거는 PostgreSQL 16 공식 문서 · 소스 README · MySQL 8.0 · Hibernate 문서/소스와 이 레슨의 테스트 · psql 실측이다. 근거를 못 찾은 주장은 빼거나 `(해석)` 으로 표시했다.

> **읽는 법**: 개념 글(마지막 면접 사다리 앞까지)은 블로그처럼 위에서 아래로 읽는 연재다 — 장면 하나 → 개념을 하나씩(그림과 함께) → PostgreSQL 에서는 → 한눈에 정리 → 스스로 확인. 면접 대비는 마지막 사다리 글에서 한다.

> **필수 / 심화**: 필수 글(02 · 03 · 05)만 ② 원리에서 읽는다 — ① 에서 감으로 예측한 뒤, 틀린 문항이 왜 틀렸는지 찾으며. 나머지는 심화(꼬리질문 · 깊은 지식 대비)라 레슨을 마친 뒤 · 면접 전에 읽는다. 필수 글 분량은 공백 줄 · 이미지 줄을 뺀 약 32,580자 ≈ 81분(400자/분 추정)이라 ② 시간을 85분으로 잡았다. MySQL 비교 절은 필수 글 안에서도 "(심화)" 다 — 회사 서비스가 PostgreSQL 이라 MySQL 은 비교 참고다.

## 읽는 순서

| # | 문서 | 한 줄 | 구분 |
|---|---|---|---|
| 01 | [락의 층 — 테이블 락 · 행 락 4모드 · 튜플에 적힌 락](01-lock-modes-and-storage.md) | 테이블 8모드 · 행 4모드와 충돌표 · xmax · MultiXact | 심화 — Q07 에서 막힐 때 (락 모드 · 충돌표) |
| 02 | [줄 서기의 실제 모양](02-waiting-and-observing.md) | `wait_event` · `pg_locks` · `pg_blocking_pids` · 대기 사슬 · ALTER 뒤에 서는 읽기 | **필수** — Q01 · Q02 · Q09 되짚기 |
| 03 | [줄 서지 않기](03-not-waiting.md) | NOWAIT · `lock_timeout` · `statement_timeout` · SKIP LOCKED 큐 · 실패 뒤 트랜잭션 · SAVEPOINT | **필수** — Q03 ~ Q06 · 구현 1 (JobQueue) |
| 04 | [외래키와 락 모드](04-foreign-keys-and-lock-modes.md) | 자식 INSERT 가 부모에 거는 `FOR KEY SHARE` · 부모 UPDATE / DELETE | 심화 — Q08 에서 막힐 때 (외래키 락) |
| 05 | [데드락](05-deadlock.md) | 감지(대기 그래프) · 40P01 · 누가 끊기나 · 락 업그레이드 · 순서 예방 vs 재시도 | **필수** — Q10 · 구현 2 (데드락) |
| 06 | [앱 · 프레임워크 · MySQL](06-app-and-mysql.md) | JPA 비관적 락 → SQL · InnoDB 레코드 / 갭 / 넥스트키 락 · 타임아웃 · 데드락 | 심화 — 앱 · JPA · MySQL 비교 (꼬리질문 대비) |
| 07 | [면접 사다리](07-interview-ladder.md) | 30초 · 2분 · 갈래별 꼬리질문 · 장애 시나리오 3개 | 심화 — ④ 말하기 연습 · 면접 전 |

권장: ① 에서 감으로 예측해 돌린 뒤, ② 에서는 필수 02 · 03 · 05 만 읽는다 — 02 로 Q01 · Q02 · Q09 를, 03 으로 Q03 ~ Q06 과 구현 1 을, 05 로 Q10 과 구현 2 를 되짚는다. Q07 · Q08 에서 막히면 01 · 04 를 펼친다. 나머지는 심화 — 레슨을 마친 뒤 · 면접 전.

## 예측 답 접힘 규칙

- 문항(Qnn) 시나리오의 **결과 값**(true/false · 숫자 · 성공/에러 코드)은 `<details>` 안에만 있다. 예측 전에 읽어도 답이 새지 않게 썼다.
- 일반 원리(예: "행 락은 읽기를 막지 않는다", "NOWAIT 는 에러로 끝낸다", 충돌표)는 본문에 있다 — 원리 자체가 ② 의 공부 대상이다. 그래도 문항 값을 먼저 직접 적는다.
- 직접 돌려 본 psql 출력 중 문항 장면과 같은 것은 `<details>` 안이다. 열기 전에 [observe/SCRIPT.md](../observe/SCRIPT.md) 로 관찰부터 해 본다. (문서 05 의 "누가 끊겼나" 실측은 관찰 항목이라 접힌 칸에 있다 — 장면 4 를 끝낸 뒤 펼친다. 문서 02 의 "실측 2 — ALTER 뒤에 서는 읽기" 같은 일반 관찰은 본문에 있다.)
- 표기: `(실측: Qnn)` = 이 레슨 테스트(정답 상태), `(실측: psql 2026-10-13)` = PostgreSQL 16.14 컨테이너(`deadlock_timeout=5s`)에서 직접, `(해석)` = 근거 문장에서 이은 판단.

## 그림

| 그림 | 어디서 | 위치 |
|---|---|---|
| 행 락 · 데드락 (기존) | 01 · 05 | [../diagrams/row-locks-deadlock.svg](../diagrams/row-locks-deadlock.svg) |
| 행 락은 튜플 헤더에 적힌다 (MultiXact) | 01 | [diagrams/multixact.svg](diagrams/multixact.svg) |
| 줄 서기의 실제 모양 (행 락 · 테이블 락) | 02 | [diagrams/wait-queue.svg](diagrams/wait-queue.svg) |

다시 그리기(만든 사람용 · 레슨 폴더에서): `python3 -I docs/diagrams/draw.py`

## 이 레슨과 연결

- 손 작업: [예측](../src/test/java/deepdive/c01/l02/RowLockPredictTest.java) · [구현 1](../src/main/java/deepdive/c01/l02/JobQueue.java) · [구현 2](../src/main/java/deepdive/c01/l02/TransferService.java) · [관찰](../observe/SCRIPT.md) · [내 말로](../NOTES.md)
- 앞 레슨: [01.01 격리수준 · MVCC](../../l01-isolation-mvcc/docs/README.md) (행 락 · 재확인 · 재시도는 [04](../../l01-isolation-mvcc/docs/04-write-conflicts.md) · [05](../../l01-isolation-mvcc/docs/05-serializable-ssi-retry.md))
- 이어지는 레슨: 01.04 재고 · 잔고 동시 차감 · 02.03 outbox
